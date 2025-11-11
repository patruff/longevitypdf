#!/usr/bin/env python3
"""
Standalone script to test Google File Search with longevity papers.
Can be run in CI/CD or locally to upload PDFs and run queries.
"""

import os
import sys
import time
import json
from pathlib import Path
from google import genai
from google.genai import types


def get_client():
    """Initialize Google GenAI client."""
    api_key = os.getenv("GOOGLE_GENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_GENAI_API_KEY environment variable not set. "
            "Get your API key from https://aistudio.google.com/apikey"
        )
    return genai.Client(api_key=api_key)


def get_or_create_store(client):
    """Get or create the file search store."""
    # For GitHub Actions, we'll create a new store each time
    # In production, you'd want to persist the store name
    config_path = Path.home() / ".longevity_papers_mcp" / "store_config.json"

    store_name = None
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
                store_name = config.get("store_name")
                print(f"📦 Using existing store: {store_name}")
        except Exception as e:
            print(f"⚠️  Could not load store config: {e}")

    if not store_name:
        print("📦 Creating new file search store...")
        store = client.file_search_stores.create()
        store_name = store.name
        print(f"✅ Created new store: {store_name}")

        # Save store name
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump({"store_name": store_name}, f)
        print(f"💾 Saved store config to {config_path}")

    return store_name


def upload_pdf(client, store_name, file_path):
    """Upload a PDF to the file search store."""
    file_path = Path(file_path).resolve()

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.suffix.lower() == '.pdf':
        raise ValueError(f"File must be a PDF, got: {file_path.suffix}")

    print(f"\n📤 Uploading {file_path.name}...")

    # Upload file to the file search store
    operation = client.file_search_stores.upload_to_file_search_store(
        file_search_store_name=store_name,
        file=str(file_path)
    )

    # Wait for upload to complete
    print("⏳ Waiting for upload and indexing...")
    max_wait = 300  # 5 minutes max
    start_time = time.time()

    while not operation.done:
        if time.time() - start_time > max_wait:
            raise TimeoutError("Upload timed out after 5 minutes")
        time.sleep(5)
        operation = client.operations.get(operation)
        elapsed = int(time.time() - start_time)
        print(f"  ⏱️  {elapsed}s elapsed...", end='\r')

    print(f"\n✅ Successfully uploaded and indexed: {file_path.name}")

    # Wait a bit more to ensure documents are fully indexed and available
    print("⏳ Ensuring documents are available for querying...")
    time.sleep(10)

    return operation


def query_papers(client, store_name, query, model="gemini-2.0-flash-exp"):
    """Query the papers using RAG with citations."""
    print(f"\n🔍 Query: {query}")
    print(f"   Model: {model}")

    # Use the file search store as a tool in generation call
    response = client.models.generate_content(
        model=model,
        contents=query,
        config=types.GenerateContentConfig(
            tools=[types.Tool(
                file_search=types.FileSearch(
                    file_search_store_names=[store_name]
                )
            )]
        )
    )

    # Extract answer
    answer = response.text

    # Extract citations from grounding metadata
    citations = []
    if response.candidates and len(response.candidates) > 0:
        grounding = response.candidates[0].grounding_metadata
        if grounding and grounding.grounding_chunks:
            for chunk in grounding.grounding_chunks:
                if chunk.retrieved_context:
                    citations.append({
                        "title": chunk.retrieved_context.title,
                        "uri": getattr(chunk.retrieved_context, 'uri', 'N/A')
                    })

    # Print formatted response
    print("\n" + "="*80)
    print("📝 ANSWER")
    print("="*80)
    print(answer)
    print()

    if citations:
        print("="*80)
        print("📚 CITATIONS")
        print("="*80)
        unique_sources = {c['title'] for c in citations}
        for i, source in enumerate(unique_sources, 1):
            print(f"{i}. {source}")
    else:
        print("ℹ️  No citations found in this response")

    print("="*80 + "\n")

    return answer, citations


def list_papers(client, store_name):
    """List all indexed papers in the store."""
    print("\n📚 Listing indexed papers...")

    try:
        # List documents in the store using the documents API
        response = client.file_search_stores.documents.list(parent=store_name)

        if not response or not hasattr(response, 'documents') or not response.documents:
            print("ℹ️  No papers indexed yet")
            return []

        doc_list = list(response.documents)

        # Calculate stats
        total_bytes = sum(int(getattr(doc, 'size_bytes', 0)) for doc in doc_list)
        total_mb = total_bytes / (1024 * 1024)

        # Estimate tokens (roughly 1 token per 4 characters, 1 char = 1 byte for ASCII)
        estimated_tokens = total_bytes // 4
        estimated_cost = (estimated_tokens / 1_000_000) * 0.15

        print(f"\n📊 Found {len(doc_list)} indexed paper(s):\n")
        for i, doc in enumerate(doc_list, 1):
            display_name = getattr(doc, 'display_name', 'Unknown')
            size_bytes = int(getattr(doc, 'size_bytes', 0))
            size_mb = size_bytes / (1024 * 1024)

            print(f"{i}. {display_name}")
            print(f"   ID: {doc.name}")
            print(f"   Size: {size_mb:.2f} MB ({size_bytes:,} bytes)")
            if hasattr(doc, 'state'):
                print(f"   State: {doc.state}")
            if hasattr(doc, 'create_time'):
                print(f"   Uploaded: {doc.create_time}")
            print()

        # Print summary stats
        print("="*80)
        print("📈 INDEXING STATISTICS")
        print("="*80)
        print(f"📄 Total Papers: {len(doc_list)}")
        print(f"📦 Total Size: {total_mb:.2f} MB ({total_bytes:,} bytes)")
        print(f"🔤 Estimated Tokens: ~{estimated_tokens:,}")
        print(f"💰 Estimated Indexing Cost: ~${estimated_cost:.4f}")
        print("="*80)

        return doc_list

    except Exception as e:
        print(f"⚠️  Could not list documents: {e}")
        print(f"   Store: {store_name}")

        # Debug: show available methods
        print(f"\n🔍 Debug - Available file_search_stores methods:")
        for attr in dir(client.file_search_stores):
            if not attr.startswith('_'):
                print(f"   - {attr}")

        if hasattr(client.file_search_stores, 'documents'):
            print(f"\n🔍 Debug - Available documents methods:")
            for attr in dir(client.file_search_stores.documents):
                if not attr.startswith('_'):
                    print(f"   - {attr}")

        return []


def main():
    """Main workflow."""
    print("🧬 Longevity Papers - Google File Search Test")
    print("="*80 + "\n")

    # Initialize client
    print("🔑 Initializing Google GenAI client...")
    client = get_client()
    print("✅ Client initialized\n")

    # Get or create store
    store_name = get_or_create_store(client)

    # Upload PDF if specified
    pdf_path = os.getenv("PDF_PATH", "vitd_telomere.pdf")
    if pdf_path and Path(pdf_path).exists():
        upload_pdf(client, store_name, pdf_path)
    else:
        print(f"⚠️  PDF not found: {pdf_path}")

    # List papers
    list_papers(client, store_name)

    # Run example queries
    example_queries = [
        "What is this paper about? Summarize the main findings.",
        "What is the relationship between vitamin D and telomeres according to this research?",
        "What methods were used in this study?"
    ]

    print(f"\n🎯 Running {len(example_queries)} example queries...\n")

    for i, query in enumerate(example_queries, 1):
        print(f"\n{'='*80}")
        print(f"QUERY {i}/{len(example_queries)}")
        print(f"{'='*80}")
        try:
            query_papers(client, store_name, query)
        except Exception as e:
            print(f"❌ Error running query: {e}")
            continue

    print("\n✅ Test completed successfully!")
    print(f"📦 Store: {store_name}")
    print("\nYou can now use this store in the MCP server by ensuring the")
    print("store config is present at ~/.longevity_papers_mcp/store_config.json")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
