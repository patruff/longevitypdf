# Quick Start Guide - Longevity Papers MCP Server

Get up and running in 5 minutes! 🚀

## Step 1: Get Your API Key (2 minutes)

1. Go to [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click "Create API Key"
3. Copy the key (starts with `AIza...`)

## Step 2: Install Dependencies (1 minute)

```bash
cd longevitypdf
pip install -r requirements.txt
```

## Step 3: Configure Claude Desktop (2 minutes)

Find your Claude Desktop config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

Add this configuration (replace the paths and API key):

```json
{
  "mcpServers": {
    "longevity-papers": {
      "command": "python",
      "args": ["/Users/yourname/longevitypdf/mcp_server.py"],
      "env": {
        "GOOGLE_GENAI_API_KEY": "AIza_your_api_key_here"
      }
    }
  }
}
```

**⚠️ Important**:
- Use the **absolute path** to `mcp_server.py`
- Don't forget to replace `your_api_key_here` with your actual API key!

## Step 4: Restart Claude Desktop

Close Claude Desktop completely and reopen it.

## Step 5: Test It! ✨

In Claude Desktop, try these commands:

### Upload a paper
```
Can you upload the PDF at ~/Documents/my_longevity_paper.pdf?
```

### Query papers
```
What interventions have been shown to increase lifespan in mice?
```

### List papers
```
Show me all the papers in the RAG system
```

## 🎉 You're Done!

Now you can:
- Upload longevity research papers
- Ask questions in natural language
- Get AI-generated answers with citations
- Build your own longevity research knowledge base!

## 💡 Example Workflow

1. **Collect papers**: Download some longevity research PDFs
2. **Upload them**: Ask Claude to upload each PDF
3. **Start querying**: Ask questions about the research
4. **Get insights**: Claude will answer using content from your papers with proper citations!

## 📚 Next Steps

- Read the [full documentation](MCP_README.md)
- Try uploading multiple papers
- Experiment with different query types
- Build your longevity research knowledge base!

## ❓ Need Help?

Common issues:
- **Server not showing up?** Check your config path is absolute
- **API key error?** Verify your API key in the config file
- **Upload fails?** Use absolute paths to PDFs

See [Troubleshooting](MCP_README.md#-troubleshooting) in the full docs.

---

**Happy researching! 🧬🔬**
