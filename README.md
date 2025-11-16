# Longevity Papers RAG - MCP Server

🧬 **Query longevity research papers with AI-powered RAG (Retrieval Augmented Generation)**

An MCP (Model Context Protocol) server that provides intelligent search and question-answering capabilities over longevity research papers using Google's File Search Tool. Upload PDFs, ask questions in natural language, and get AI-generated answers with proper citations!

## 🚀 Features

- **📄 PDF Upload**: Upload longevity research papers to Google's File Search store
- **🔍 Intelligent Search**: Query papers using natural language questions
- **📚 Citation Support**: Get AI-generated answers with proper source citations
- **📈 Usage Tracking**: Track indexed papers, total tokens, and estimated costs
- **💰 Cost Effective**:
  - Storage: **FREE**
  - Query embeddings: **FREE**
  - Initial indexing: $0.15 per 1M tokens (one-time cost)
- **🔄 Persistent Storage**: Files persist across sessions
- **🛠️ Full Management**: List, query, and delete indexed papers

## 📋 Prerequisites

- Python 3.10+
- Google GenAI API key ([Get one free here](https://aistudio.google.com/apikey))
- Claude Desktop (or any MCP-compatible client)

## 🛠️ Installation

### 1. Clone and Setup

```bash
git clone https://github.com/patruff/longevitypdf.git
cd longevitypdf
pip install -r requirements.txt
```

### 2. Get Google GenAI API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Click "Create API Key"
3. Copy your API key

### 3. Configure Claude Desktop

Add the MCP server to your Claude Desktop configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "longevity-papers": {
      "command": "python",
      "args": ["/absolute/path/to/longevitypdf/mcp_server.py"],
      "env": {
        "GOOGLE_GENAI_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

**Important**: Replace `/absolute/path/to/longevitypdf/` with the actual absolute path to this directory!

### 4. Restart Claude Desktop

Close and reopen Claude Desktop. The server will now be available!

## 🎯 Available Tools

### 1. `upload_longevity_paper`

Upload a PDF research paper to the RAG system.

**Parameters:**
- `file_path` (required): Path to the PDF file

**Example:**
```
Upload ~/Documents/rapamycin_longevity_study.pdf to the system
```

### 2. `query_longevity_papers`

Ask questions about the indexed papers in natural language.

**Parameters:**
- `query` (required): Your question about longevity research
- `model` (optional): Gemini model to use (default: gemini-2.0-flash-exp)

**Example Questions:**
- "What interventions have been shown to increase lifespan in mice?"
- "Which studies show the highest longevity gains from caloric restriction?"
- "What are the effects of rapamycin on aging in C. elegans?"
- "Compare the longevity benefits of metformin vs rapamycin"
- "What model organisms are most commonly used in longevity research?"

### 3. `list_indexed_papers`

List all papers currently in the RAG system with detailed statistics:
- Total papers indexed
- Total size in MB
- Estimated tokens processed
- Estimated indexing cost

**Example:**
```
Show me all the papers in the RAG system
```

### 4. `get_store_info`

Get information about the current file search store, including configuration and pricing details.

### 5. `delete_paper`

Delete a specific paper from the RAG system.

**Parameters:**
- `file_id` (required): File ID from `list_indexed_papers`

## 💡 Usage Examples

### Getting Started

1. **Upload your first paper:**
   ```
   Upload ~/Documents/longevity_papers/rapamycin_mice.pdf to the system
   ```

2. **Check indexing statistics:**
   ```
   List all indexed papers
   ```

3. **Query the papers:**
   ```
   What did the rapamycin study find about lifespan extension in mice?
   ```

### Advanced Queries

Ask complex questions that span multiple papers:

- "Compare the effectiveness of dietary restriction vs pharmacological interventions"
- "What are the common mechanisms of action across successful longevity interventions?"
- "Which interventions have been tested in both mice and humans?"
- "What are the most promising interventions for human longevity based on animal studies?"

## 🔧 Automated Sync & Workflows

### Google Drive Integration

The system automatically syncs PDFs from your Google Drive to the RAG system!

#### Setup Google Drive Sync

1. **Create a Service Account:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the Google Drive API
   - Create a Service Account and download the JSON key file

2. **Share Drive Folder:**
   - Create a folder named `longevitypapers` in your Google Drive
   - Share this folder with your service account email (found in the JSON key)
   - Give it "Viewer" or "Editor" access

3. **Add GitHub Secret:**
   - Go to your repository Settings → Secrets and variables → Actions
   - Create a new secret named `GOOGLE_DRIVE_CREDENTIALS`
   - Paste the entire contents of your service account JSON key file
   - Also ensure `GOOGLE_GENAI_API_KEY` secret is set

4. **Start Syncing:**
   - Upload PDFs to your `longevitypapers` folder in Google Drive
   - The system automatically checks every 6 hours for new PDFs
   - New PDFs are automatically uploaded to the RAG system
   - Or manually trigger the sync from the Actions tab

### GitHub Actions Workflows

The repository includes three workflows:

#### 1. **Sync PDFs from Google Drive** (`sync_drive_pdfs.yml`) ⭐ NEW!
Automatically syncs PDFs from your Google Drive folder to the File Search RAG system.

**Runs automatically:**
- Every 6 hours via scheduled cron job
- Checks your `longevitypapers` Google Drive folder
- Downloads any new PDFs
- Uploads them to File Search
- Tracks synced files to avoid duplicates

**Or run manually:**
1. Go to the Actions tab in GitHub
2. Select "Sync PDFs from Google Drive"
3. Click "Run workflow"

**What it does:**
- Connects to Google Drive using service account
- Lists PDFs in the `longevitypapers` folder
- Compares with previously synced files
- Downloads and uploads only new PDFs
- Saves sync state for future runs

#### 2. **Query Longevity Papers** (`query_papers.yml`)
Ask questions about your indexed papers directly from GitHub Actions.

**How to use:**
1. Go to the Actions tab in GitHub
2. Select "Query Longevity Papers"
3. Click "Run workflow"
4. Enter your question (e.g., "What are the main findings about vitamin D and telomeres?")
5. Choose a Gemini model (default: gemini-2.0-flash-exp)
6. Click "Run workflow"

The workflow will query your papers and display the AI-generated answer with citations.

#### 3. **Test File Search** (`test_file_search.yml`)
Automated testing workflow that runs automatically when PDFs are added or when triggered manually.

**Triggers automatically on:**
- Push to main or claude/* branches
- Changes to PDF files
- Changes to test_file_search.py

**Or run manually:**
1. Go to the Actions tab
2. Select "Test Google File Search"
3. Click "Run workflow"

This workflow uploads the test PDF, lists all indexed papers, and runs example queries.

### Local Testing

```bash
# Test file search locally
export GOOGLE_GENAI_API_KEY="your_key_here"
python test_file_search.py

# Test Google Drive sync locally
export GOOGLE_GENAI_API_KEY="your_key_here"
export GOOGLE_DRIVE_CREDENTIALS='{"type":"service_account",...}'
python sync_drive_pdfs.py
```

**Note:** All workflows require secrets to be set in your repository settings.

## 🏗️ Architecture

### Google File Search Tool

The MCP server uses Google's [File Search Tool](https://ai.google.dev/gemini-api/docs/file-search) which provides:

- **Automatic chunking**: Optimal text splitting for embeddings
- **Vector search**: Semantic search powered by `gemini-embedding-001`
- **Managed infrastructure**: No need to manage vector databases
- **Built-in citations**: Automatic source tracking

### Storage

- **File Search Store**: Single shared store with display name "longevitypdf"
  - All PDFs are uploaded to the same store for unified RAG queries
  - Created automatically on first use if not exists
  - System searches for existing store by display name before creating new one
- **Config file**: `~/.longevity_papers_mcp/store_config.json`
- **Sync state**: `~/.longevity_papers_mcp/synced_files.json` (tracks Google Drive PDFs)
- **Persistence**: Store name and sync state are saved and reused across sessions

### Google Drive Sync Process

1. **Every 6 hours** (or manually triggered):
   - Script connects to Google Drive using service account
   - Lists all PDFs in the `longevitypapers` folder
   - Compares with `synced_files.json` to identify new files
   - Downloads new PDFs to temporary directory
   - Uploads each new PDF to Google File Search
   - Updates sync state file with file ID, name, timestamp, and size
   - Deletes temporary files

2. **Duplicate Prevention**:
   - Each Google Drive file has a unique ID
   - Sync state tracks uploaded file IDs
   - Files are never re-uploaded unless manually removed from sync state

3. **Workflow Benefits**:
   - Just drop PDFs in your Drive folder - automatic indexing!
   - No need to commit PDFs to git repository
   - Works from any device (phone, tablet, computer)
   - Can share Drive folder with collaborators

### Pricing

| Operation | Cost |
|-----------|------|
| Storage | **FREE** |
| Query embeddings | **FREE** |
| Initial indexing | $0.15 per 1M tokens |

**Example**: A typical research paper (20 pages) ≈ 10K tokens = **$0.0015 to index**

## 📈 Tracking & Statistics

The `list_indexed_papers` tool provides detailed metrics:

- **Papers Indexed**: Total number of documents
- **Total Size**: Combined size in MB and bytes
- **Estimated Tokens**: Approximate token count (~1 token per 4 characters)
- **Estimated Cost**: Total indexing cost at $0.15 per 1M tokens

Example output:
```
📈 INDEXING STATISTICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 Total Papers: 5
📦 Total Size: 12.45 MB (13,058,048 bytes)
🔤 Estimated Tokens: ~3,264,512
💰 Estimated Indexing Cost: ~$0.4897
```

## 🔧 Development

### Project Structure

```
longevitypdf/
├── mcp_server.py              # Main MCP server implementation
├── test_file_search.py        # Standalone testing script
├── sync_drive_pdfs.py         # Google Drive sync script
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variable template
├── README.md                 # This file
├── vitd_telomere.pdf         # Example research paper
└── .github/
    └── workflows/
        ├── sync_drive_pdfs.yml   # Automated Google Drive sync (every 6 hours)
        ├── query_papers.yml      # Manual query workflow
        └── test_file_search.yml  # Automated testing workflow
```

### Running Standalone (Testing)

```bash
# Set your API key
export GOOGLE_GENAI_API_KEY="your_key_here"

# Run the server (for testing/debugging)
python mcp_server.py
```

The server communicates via stdio (standard input/output) using the MCP protocol.

### Logging

Logs are written to stderr and include:
- Server startup/initialization
- File uploads and indexing
- Query operations
- Error messages

View logs in Claude Desktop's developer console.

## 🐛 Troubleshooting

### "GOOGLE_GENAI_API_KEY environment variable not set"

- Check that your `claude_desktop_config.json` has the correct API key
- Restart Claude Desktop after making changes

### "File not found" when uploading

- Use absolute paths: `/Users/yourname/Documents/paper.pdf`
- Or expand home directory: `~/Documents/paper.pdf`
- Check file exists and has `.pdf` extension

### "Upload timed out"

- Large PDFs (>50 pages) may take a few minutes to index
- Check your internet connection
- Try uploading smaller PDFs first

### No citations in query response

- This is normal for some queries that don't require specific sources
- Try more specific questions that reference paper content
- Ensure papers are successfully uploaded (check with `list_indexed_papers`)

### Server not appearing in Claude Desktop

1. Check JSON syntax in `claude_desktop_config.json`
2. Verify absolute path to `mcp_server.py` is correct
3. Ensure Python is in your PATH
4. Restart Claude Desktop completely

## 🔒 Privacy & Security

- **API Key**: Your Google GenAI API key is stored locally in Claude Desktop config
- **Papers**: PDFs are uploaded to Google's File Search service
- **Data**: Google's standard [terms of service](https://ai.google.dev/gemini-api/terms) apply
- **Local Storage**: Only store name is saved locally (`~/.longevity_papers_mcp/`)

## 📚 Resources

- [Google File Search Tool Announcement](https://developers.googleblog.com/en/introducing-the-file-search-tool-in-gemini-api/)
- [File Search Documentation](https://ai.google.dev/gemini-api/docs/file-search)
- [File Search Documents API](https://ai.google.dev/gemini-api/docs/file-search-documents)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Google AI Studio](https://aistudio.google.com/)

## 🎓 Use Cases

### Research
- Literature reviews on longevity interventions
- Cross-study comparisons
- Finding specific experimental details

### Learning
- Understanding longevity research landscape
- Exploring different model organisms
- Learning about intervention mechanisms

### Analysis
- Identifying research gaps
- Comparing methodologies
- Extracting statistics across studies

## 🚀 Future Enhancements

Potential improvements:
- [ ] Bulk PDF upload from directory
- [ ] Export query results to markdown/JSON
- [ ] Custom embedding models (BioBERT support)
- [ ] Advanced filtering (by year, organism, intervention)
- [ ] Paper metadata extraction
- [ ] Integration with PubMed API
- [ ] Automatic paper recommendations
- [ ] Cost tracking over time
- [ ] Custom chunking strategies

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.

---

**Built with ❤️ for longevity research**

*Using Google's File Search Tool + MCP Protocol*
