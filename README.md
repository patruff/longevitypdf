# Longevity Papers RAG System

🧬 **AI-Powered Question Answering for Longevity Research Papers**

## 🚀 New MCP Server (Recommended!)

This project now includes an **MCP (Model Context Protocol) server** that provides RAG (Retrieval Augmented Generation) capabilities using Google's File Search Tool.

### Features
- 📄 Upload longevity research papers (PDFs)
- 🔍 Query papers with natural language questions
- 📚 Get AI-generated answers with citations
- 💰 Free storage & embeddings (only pay for indexing: $0.15/1M tokens)

### Quick Start

👉 **[See QUICKSTART.md](QUICKSTART.md)** for 5-minute setup guide!

📖 **[See MCP_README.md](MCP_README.md)** for full documentation

### Why Use the MCP Server?
- ✅ Natural language queries instead of manual JSON parsing
- ✅ Automatic citations from source papers
- ✅ Free storage and query embeddings
- ✅ Interactive conversation with Claude
- ✅ Better search quality (semantic vs keyword)

---

## 📚 Legacy System

The original automated PDF processor is still available below.

## Overview

This repository automatically processes PDF papers about longevity research stored in Google Drive and extracts:
- **longevity_increase_percent**: Percentage increase in lifespan
- **model_organism**: The organism studied (e.g., C. elegans, mice, rats, humans)
- **intervention_used**: The treatment or intervention applied (e.g., rapamycin, caloric restriction)

All PDFs are sourced from Google Drive, and processed results are saved back to Google Drive in a `processed_papers` subfolder.

## How It Works

1. **Upload Papers**: Add PDF files to your `longevitypapers` folder in Google Drive
2. **Automated Processing**: GitHub Action runs every 6 hours (or manually triggered) to check for new PDFs
3. **AI Extraction**: Grok AI extracts longevity statistics from each paper
4. **Results Stored**: Processed results saved to `longevitypapers/processed_papers/` folder in Google Drive
5. **Tracking**: System tracks which papers have been processed to avoid duplicates

## Setup

### Prerequisites

- Python 3.11+
- xAI API key (for Grok AI)
- Google Cloud Service Account with Google Drive API access

### Google Drive Setup

#### 1. Create a Google Cloud Project

- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a new project or select an existing one

#### 2. Enable Google Drive API

- Navigate to "APIs & Services" > "Library"
- Search for "Google Drive API"
- Click "Enable"

#### 3. Create a Service Account

- Go to "APIs & Services" > "Credentials"
- Click "Create Credentials" > "Service Account"
- Fill in the service account details and create

#### 4. Generate JSON Key

- Click on the created service account
- Go to "Keys" tab
- Click "Add Key" > "Create new key"
- Choose JSON format and download the file

#### 5. Create and Share Google Drive Folder

- Create a folder named `longevitypapers` in your Google Drive (must be this exact name)
- Right-click the folder and click "Share"
- Share it with the service account email (found in the JSON file as `client_email`)
- Give it **"Editor"** permissions (required for creating the `processed_papers` subfolder)

#### 6. Add GitHub Secrets

- Go to your repo Settings > Secrets and variables > Actions
- Add a new secret named `GOOGLE_DRIVE_CREDENTIALS`
- Paste the entire contents of the JSON key file as the value
- Add another secret named `XAI_API_KEY` with your xAI API key (get from https://console.x.ai/)

### Local Setup (Optional)

To run the processor locally:

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your environment variables:
```bash
export XAI_API_KEY="your-xai-api-key-here"
export GOOGLE_DRIVE_CREDENTIALS='{"type": "service_account", "project_id": "...", ...}'
```

3. Run the processor:
```bash
python process_papers.py
```

## Project Structure

```
longevitypdf/
├── .github/
│   └── workflows/
│       └── process_papers.yml  # GitHub Action workflow (runs every 6 hours)
├── process_papers.py           # Main processing script
├── google_drive_client.py      # Google Drive integration module
├── requirements.txt            # Python dependencies
└── processing.log              # Processing logs (local only)
```

### Google Drive Structure

```
longevitypapers/                    # Your main folder in Google Drive
├── paper1.pdf                      # PDF papers to process
├── paper2.pdf
├── mice_adf.pdf
└── processed_papers/               # Auto-created subfolder for results
    ├── paper1_processed.json       # Processed results
    ├── paper2_processed.json
    └── .processed_tracker.json     # Tracks which papers were processed
```

## Usage

### Adding New Papers

1. Upload PDF files to your `longevitypapers` folder in Google Drive
2. Wait for the next scheduled run (every 6 hours), or
3. Manually trigger via GitHub Actions tab > "Process Longevity Papers" > "Run workflow"

The system will automatically:
- Detect new PDFs
- Download and process them
- Save results to `processed_papers` subfolder in Google Drive
- Track processed papers to avoid re-processing

### Viewing Results

Processed papers are saved in the `longevitypapers/processed_papers/` folder in your Google Drive as JSON files:

```json
{
  "filename": "mice_adf.pdf",
  "processed_at": "2025-11-02T10:30:00",
  "stats": {
    "longevity_increase_percent": "25%",
    "model_organism": "mice",
    "intervention_used": "alternate-day fasting"
  },
  "raw_text_preview": "First 1000 characters of extracted text..."
}
```

### Checking Processing Status

- Check the Actions tab in GitHub to see workflow runs
- View `processing.log` in workflow artifacts for detailed logs
- Check the `.processed_tracker.json` file in Google Drive to see which papers have been processed

## Features

- **Cloud-Based**: All PDFs and results stored in Google Drive (no local storage needed)
- **Automated**: Runs every 6 hours automatically via GitHub Actions
- **Smart Tracking**: Only processes new papers, skips already-processed ones
- **AI-Powered**: Uses Grok AI for intelligent extraction of longevity statistics
- **Error Handling**: Comprehensive logging and error handling
- **Manual Control**: Can be triggered manually anytime from GitHub Actions

## Troubleshooting

### "Google Drive authentication failed"

- Verify `GOOGLE_DRIVE_CREDENTIALS` secret is set in GitHub
- Check that the JSON is valid (copy the entire file contents)
- Ensure the service account JSON key is not expired

### "Could not find 'longevitypapers' folder"

- Make sure the folder is named exactly `longevitypapers` (case-sensitive)
- Verify the folder is shared with the service account email
- Check that the service account has "Editor" permissions

### "Could not create 'processed_papers' subfolder"

- Ensure the service account has **"Editor"** permissions (not just "Viewer")
- Check that Google Drive API is enabled in your Google Cloud project

### "No PDFs found in Google Drive"

- Verify PDFs are directly in the `longevitypapers` folder (not in subfolders)
- Check that files have `.pdf` extension
- Ensure files are not in trash

### "XAI_API_KEY not set"

- Add `XAI_API_KEY` to GitHub Secrets
- Get your API key from https://console.x.ai/

### PDF Extraction Fails

- Some PDFs may be scanned images requiring OCR (not currently supported)
- Try using a text-based PDF instead

## Workflow Schedule

The GitHub Action runs:
- **Every 6 hours** automatically (at :00 minutes)
- **Manually** via the Actions tab in GitHub
- You can adjust the schedule in `.github/workflows/process_papers.yml` by modifying the cron expression

## Contributing

Feel free to open issues or submit pull requests for improvements.

## License

MIT
