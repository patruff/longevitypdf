#!/usr/bin/env python3
"""
Longevity Papers MCP Server

An MCP (Model Context Protocol) server that provides RAG (Retrieval Augmented Generation)
capabilities for longevity research papers using Google's File Search Tool.

Features:
- Upload PDFs to Google's File Search store (free storage & embeddings)
- Query papers with natural language and get AI-generated answers with citations
- Manage file search stores and indexed documents
- Zero cost for storage and query-time embeddings (only pay for initial indexing)
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Any, Optional
from google import genai
from google.genai import types
import mcp.server.stdio
import mcp.types as mcp_types
from mcp.server import Server
from mcp.server.models import InitializationOptions

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Server instance
server = Server("longevity-papers-rag")

# Global client and store
_client: Optional[genai.Client] = None
_file_search_store: Optional[Any] = None
_store_name: Optional[str] = None


def get_client() -> genai.Client:
    """Get or create the Google GenAI client."""
    global _client
    if _client is None:
        api_key = os.getenv("GOOGLE_GENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_GENAI_API_KEY environment variable not set. "
                "Get your API key from https://aistudio.google.com/apikey"
            )
        _client = genai.Client(api_key=api_key)
        logger.info("Initialized Google GenAI client")
    return _client


def get_or_create_store() -> tuple[Any, str]:
    """Get or create the file search store."""
    global _file_search_store, _store_name

    if _file_search_store is None:
        client = get_client()

        # Try to load store name from config
        config_path = Path.home() / ".longevity_papers_mcp" / "store_config.json"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                    _store_name = config.get("store_name")
                    logger.info(f"Loaded existing store name: {_store_name}")
            except Exception as e:
                logger.warning(f"Could not load store config: {e}")

        # Create new store if needed
        if not _store_name:
            logger.info("Creating new file search store...")
            _file_search_store = client.file_search_stores.create()
            _store_name = _file_search_store.name
            logger.info(f"Created new file search store: {_store_name}")

            # Save store name
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump({"store_name": _store_name}, f)
            logger.info(f"Saved store config to {config_path}")
        else:
            # Store exists, we can use it by name
            _file_search_store = True  # Placeholder, we just need the name

    return _file_search_store, _store_name


@server.list_tools()
async def handle_list_tools() -> list[mcp_types.Tool]:
    """List available MCP tools."""
    return [
        mcp_types.Tool(
            name="upload_longevity_paper",
            description=(
                "Upload a longevity research paper (PDF) to the RAG system. "
                "The paper will be automatically indexed using Google's File Search tool. "
                "Indexing cost: $0.15 per 1M tokens (one-time). Storage is FREE."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the PDF file to upload"
                    }
                },
                "required": ["file_path"]
            }
        ),
        mcp_types.Tool(
            name="query_longevity_papers",
            description=(
                "Query the longevity papers knowledge base using natural language. "
                "Returns AI-generated answers grounded in the uploaded papers with citations. "
                "Perfect for questions like: 'What interventions increase lifespan in mice?', "
                "'Which studies show the highest longevity gains?', or "
                "'What are the effects of rapamycin on aging?'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language question about longevity research"
                    },
                    "model": {
                        "type": "string",
                        "description": "Gemini model to use (default: gemini-2.0-flash-exp)",
                        "enum": ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"]
                    }
                },
                "required": ["query"]
            }
        ),
        mcp_types.Tool(
            name="list_indexed_papers",
            description=(
                "List all papers currently indexed in the RAG system. "
                "Shows file names and metadata for all uploaded documents."
            ),
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        mcp_types.Tool(
            name="get_store_info",
            description=(
                "Get information about the current file search store, "
                "including store name and configuration details."
            ),
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        mcp_types.Tool(
            name="delete_paper",
            description=(
                "Delete a specific paper from the RAG system by its file ID."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_id": {
                        "type": "string",
                        "description": "The file ID to delete (from list_indexed_papers)"
                    }
                },
                "required": ["file_id"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[mcp_types.TextContent | mcp_types.ImageContent | mcp_types.EmbeddedResource]:
    """Handle tool execution requests."""

    try:
        if name == "upload_longevity_paper":
            return await upload_longevity_paper(arguments or {})
        elif name == "query_longevity_papers":
            return await query_longevity_papers(arguments or {})
        elif name == "list_indexed_papers":
            return await list_indexed_papers(arguments or {})
        elif name == "get_store_info":
            return await get_store_info(arguments or {})
        elif name == "delete_paper":
            return await delete_paper(arguments or {})
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        return [mcp_types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def upload_longevity_paper(arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    """Upload a PDF to the file search store."""
    file_path = arguments.get("file_path")

    if not file_path:
        return [mcp_types.TextContent(
            type="text",
            text="Error: file_path is required"
        )]

    file_path = Path(file_path).expanduser().resolve()

    if not file_path.exists():
        return [mcp_types.TextContent(
            type="text",
            text=f"Error: File not found: {file_path}"
        )]

    if not file_path.suffix.lower() == '.pdf':
        return [mcp_types.TextContent(
            type="text",
            text=f"Error: File must be a PDF, got: {file_path.suffix}"
        )]

    try:
        client = get_client()
        _, store_name = get_or_create_store()

        logger.info(f"Uploading {file_path.name} to file search store...")

        # Upload file to the file search store
        operation = client.file_search_stores.upload_to_file_search_store(
            file_search_store_name=store_name,
            file=str(file_path)
        )

        # Wait for upload to complete
        logger.info("Waiting for upload and indexing to complete...")
        max_wait = 300  # 5 minutes max
        start_time = time.time()

        while not operation.done:
            if time.time() - start_time > max_wait:
                return [mcp_types.TextContent(
                    type="text",
                    text="Error: Upload timed out after 5 minutes"
                )]
            time.sleep(5)
            operation = client.operations.get(operation)

        logger.info(f"Successfully uploaded and indexed {file_path.name}")

        # Wait to ensure document is available
        logger.info("Ensuring document is available for querying...")
        time.sleep(10)

        return [mcp_types.TextContent(
            type="text",
            text=(
                f"✅ Successfully uploaded and indexed: {file_path.name}\n\n"
                f"The paper is now searchable in the RAG system.\n"
                f"Store: {store_name}\n\n"
                f"You can now query it using the 'query_longevity_papers' tool!"
            )
        )]

    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        return [mcp_types.TextContent(
            type="text",
            text=f"Error uploading file: {str(e)}"
        )]


async def query_longevity_papers(arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    """Query the papers using RAG with citations."""
    query = arguments.get("query")
    model = arguments.get("model", "gemini-2.0-flash-exp")

    if not query:
        return [mcp_types.TextContent(
            type="text",
            text="Error: query is required"
        )]

    try:
        client = get_client()
        _, store_name = get_or_create_store()

        logger.info(f"Querying papers with: {query}")

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

        # Format response
        result_text = f"## Answer\n\n{answer}\n\n"

        if citations:
            result_text += "## Citations\n\n"
            unique_sources = {c['title'] for c in citations}
            for i, source in enumerate(unique_sources, 1):
                result_text += f"{i}. {source}\n"
        else:
            result_text += "*No citations found in this response.*\n"

        logger.info(f"Query completed with {len(unique_sources) if citations else 0} sources")

        return [mcp_types.TextContent(
            type="text",
            text=result_text
        )]

    except Exception as e:
        logger.error(f"Error querying papers: {e}", exc_info=True)
        return [mcp_types.TextContent(
            type="text",
            text=f"Error querying papers: {str(e)}"
        )]


async def list_indexed_papers(arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    """List all indexed papers in the store."""
    try:
        client = get_client()
        _, store_name = get_or_create_store()

        logger.info("Listing indexed papers...")

        # List documents in the store using the documents API
        response = client.file_search_stores.documents.list(parent=store_name)

        # Pager is an iterator - convert to list directly
        doc_list = list(response)

        if not doc_list:
            return [mcp_types.TextContent(
                type="text",
                text="No papers indexed yet. Use 'upload_longevity_paper' to add papers."
            )]

        # Calculate stats
        total_bytes = sum(int(getattr(doc, 'size_bytes', 0)) for doc in doc_list)
        total_mb = total_bytes / (1024 * 1024)

        # Estimate tokens (roughly 1 token per 4 characters)
        estimated_tokens = total_bytes // 4
        estimated_cost = (estimated_tokens / 1_000_000) * 0.15

        # Format document list
        result = "## Indexed Longevity Papers\n\n"
        for i, doc in enumerate(doc_list, 1):
            display_name = getattr(doc, 'display_name', 'Unknown')
            size_bytes = int(getattr(doc, 'size_bytes', 0))
            size_mb = size_bytes / (1024 * 1024)

            result += f"{i}. **{display_name}**\n"
            result += f"   - Document ID: `{doc.name}`\n"
            result += f"   - Size: {size_mb:.2f} MB ({size_bytes:,} bytes)\n"
            if hasattr(doc, 'state'):
                result += f"   - State: {doc.state}\n"
            if hasattr(doc, 'create_time'):
                result += f"   - Uploaded: {doc.create_time}\n"
            result += "\n"

        result += "---\n\n"
        result += "## 📈 Indexing Statistics\n\n"
        result += f"- **Total Papers**: {len(doc_list)}\n"
        result += f"- **Total Size**: {total_mb:.2f} MB ({total_bytes:,} bytes)\n"
        result += f"- **Estimated Tokens**: ~{estimated_tokens:,}\n"
        result += f"- **Estimated Indexing Cost**: ~${estimated_cost:.4f}\n\n"
        result += f"**Store**: `{store_name}`"

        return [mcp_types.TextContent(
            type="text",
            text=result
        )]

    except Exception as e:
        logger.error(f"Error listing papers: {e}", exc_info=True)
        return [mcp_types.TextContent(
            type="text",
            text=f"Error listing papers: {str(e)}"
        )]


async def get_store_info(arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    """Get file search store information."""
    try:
        _, store_name = get_or_create_store()

        config_path = Path.home() / ".longevity_papers_mcp" / "store_config.json"

        info = f"## File Search Store Information\n\n"
        info += f"**Store Name:** `{store_name}`\n"
        info += f"**Config Path:** `{config_path}`\n\n"
        info += "### Pricing\n"
        info += "- **Storage:** FREE\n"
        info += "- **Query embeddings:** FREE\n"
        info += "- **Initial indexing:** $0.15 per 1M tokens\n\n"
        info += "This store persists across sessions and can be reused.\n"

        return [mcp_types.TextContent(
            type="text",
            text=info
        )]

    except Exception as e:
        logger.error(f"Error getting store info: {e}", exc_info=True)
        return [mcp_types.TextContent(
            type="text",
            text=f"Error getting store info: {str(e)}"
        )]


async def delete_paper(arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    """Delete a paper from the store."""
    file_id = arguments.get("file_id")

    if not file_id:
        return [mcp_types.TextContent(
            type="text",
            text="Error: file_id is required. Use 'list_indexed_papers' to get file IDs."
        )]

    try:
        client = get_client()

        logger.info(f"Deleting file: {file_id}")
        client.files.delete(name=file_id)
        logger.info(f"Successfully deleted {file_id}")

        return [mcp_types.TextContent(
            type="text",
            text=f"✅ Successfully deleted file: {file_id}"
        )]

    except Exception as e:
        logger.error(f"Error deleting file: {e}", exc_info=True)
        return [mcp_types.TextContent(
            type="text",
            text=f"Error deleting file: {str(e)}"
        )]


async def main():
    """Run the MCP server."""
    logger.info("Starting Longevity Papers MCP Server...")

    # Run the server using stdin/stdout
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="longevity-papers-rag",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities={}
                )
            )
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
