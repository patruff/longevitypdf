# Longevity PDF Processor

Automated system for processing scientific papers about longevity and extracting key statistics.

## Overview

This repository automatically processes PDF papers about longevity research and extracts:
- **longevity_increase_percent**: Percentage increase in lifespan
- **model_organism**: The organism studied (e.g., C. elegans, mice, rats)
- **intervention_used**: The treatment or intervention applied

## How It Works

1. **Add Papers**: Upload PDF files to Google Drive folder `longevitypapers` (or use local `papers/` folder)
2. **Trigger Processing**: Edit `papers/kickoff.txt` and commit the change (or run manually)
3. **Automated Processing**: GitHub Action fetches PDFs from Google Drive and runs the processing script
4. **View Results**: Check the `processed_papers/` folder for JSON output

## PDF Source Options

This system supports two methods for providing PDFs:

1. **Google Drive (Recommended)**: PDFs are automatically fetched from a Google Drive folder named `longevitypapers`
2. **Local Folder (Fallback)**: If Google Drive is not configured, PDFs can be placed in the local `papers/` folder

## Setup

### Prerequisites

- Python 3.11+
- xAI API key (Grok)
- Google Cloud Service Account (for Google Drive integration)

### Google Drive Setup

To enable Google Drive integration:

1. **Create a Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable Google Drive API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"

3. **Create a Service Account**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Fill in the service account details and create

4. **Generate JSON Key**:
   - Click on the created service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key"
   - Choose JSON format and download the file

5. **Share Google Drive Folder**:
   - Create a folder named `longevitypapers` in your Google Drive
   - Right-click the folder and click "Share"
   - Share it with the service account email (found in the JSON file as `client_email`)
   - Give it "Viewer" or "Editor" permissions

6. **Add to GitHub Secrets**:
   - Go to Settings > Secrets and variables > Actions
   - Add a new secret named `GOOGLE_CREDENTIALS`
   - Paste the entire contents of the JSON file as the value

### Local Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your environment variables:
```bash
export XAI_API_KEY="your-xai-api-key-here"
export GOOGLE_CREDENTIALS='{"type": "service_account", "project_id": "...", ...}'
```

3. Run the processor:
```bash
python process_papers.py
```

### GitHub Actions Setup

1. Add your secrets to GitHub:
   - Go to Settings > Secrets and variables > Actions
   - Add `XAI_API_KEY` (get from https://console.x.ai/)
   - Add `GOOGLE_CREDENTIALS` (entire JSON from service account)

2. The workflow will automatically trigger when you:
   - Edit and commit `papers/kickoff.txt`
   - Manually trigger via Actions tab

3. PDFs will be automatically fetched from your Google Drive `longevitypapers` folder

## Project Structure

```
longevitypdf/
├── papers/                      # Fallback: Place PDF papers here if not using Google Drive
│   └── kickoff.txt             # Edit this to trigger processing
├── processed_papers/            # Processed results (JSON)
│   └── .processed_tracker.json # Tracks which papers were processed
├── .github/
│   └── workflows/
│       └── process_papers.yml  # GitHub Action workflow
├── process_papers.py           # Main processing script
├── google_drive_client.py      # Google Drive integration module
├── requirements.txt            # Python dependencies
└── processing.log              # Processing logs
```

## Output Format

Each processed paper generates a JSON file with the following structure:

```json
{
  "filename": "paper.pdf",
  "processed_at": "2025-11-02T10:30:00",
  "stats": {
    "longevity_increase_percent": "25%",
    "model_organism": "C. elegans",
    "intervention_used": "rapamycin"
  },
  "raw_text_preview": "First 1000 characters of extracted text..."
}
```

## Usage

### Adding New Papers (Google Drive)

1. Upload your PDF files to the `longevitypapers` folder in Google Drive
2. Edit `papers/kickoff.txt` (add a timestamp or increment a counter)
3. Commit and push the changes
4. The GitHub Action will automatically fetch PDFs from Google Drive and process any new ones

### Adding New Papers (Local Folder)

If not using Google Drive:

1. Place your PDF files in the `papers/` folder
2. Edit `papers/kickoff.txt` (add a timestamp or increment a counter)
3. Commit and push the changes
4. The GitHub Action will automatically process any new PDFs

### Manual Processing

To process papers locally:

```bash
python process_papers.py
```

### Checking Results

Processed papers are saved in `processed_papers/` as JSON files with the naming convention:
`{original_filename}_processed.json`

## Features

- **Google Drive Integration**: Automatically fetches PDFs from your Google Drive folder
- **Automatic Tracking**: Only processes new papers (tracked in `.processed_tracker.json`)
- **AI-Powered Extraction**: Uses Grok AI to intelligently extract longevity statistics
- **Error Handling**: Comprehensive logging and error handling
- **GitHub Integration**: Automatically commits processed results back to the repository
- **Fallback Support**: Works with local folder if Google Drive is not configured

## Logs

Processing logs are saved to `processing.log` and include:
- Papers being processed
- Extraction results
- Any errors encountered

## Troubleshooting

**API Key Issues**: Ensure `XAI_API_KEY` is set in your environment or GitHub Secrets

**Google Drive Not Working**:
- Check that `GOOGLE_CREDENTIALS` secret is properly set in GitHub
- Verify the service account has access to the `longevitypapers` folder
- Ensure the Google Drive API is enabled in your Google Cloud project

**PDF Extraction Fails**: Some PDFs may be scanned images requiring OCR (not currently supported)

**GitHub Action Not Triggering**: Ensure you're committing changes to `papers/kickoff.txt` specifically

**"Folder not found" Error**: Make sure the folder is named exactly `longevitypapers` and is shared with your service account

## Contributing

Feel free to open issues or submit pull requests for improvements.

## License

MIT
