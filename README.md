# Longevity PDF Processor

Automated system for processing scientific papers about longevity and extracting key statistics.

## Overview

This repository automatically processes PDF papers about longevity research and extracts:
- **longevity_increase_percent**: Percentage increase in lifespan
- **model_organism**: The organism studied (e.g., C. elegans, mice, rats)
- **intervention_used**: The treatment or intervention applied

## How It Works

1. **Add Papers**: Place PDF files in the `papers/` folder
2. **Trigger Processing**: Edit `papers/kickoff.txt` and commit the change
3. **Automated Processing**: GitHub Action runs the processing script
4. **View Results**: Check the `processed_papers/` folder for JSON output

## Setup

### Prerequisites

- Python 3.11+
- xAI API key (Grok)

### Local Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your xAI API key:
```bash
export XAI_API_KEY="your-api-key-here"
```

3. Run the processor:
```bash
python process_papers.py
```

### GitHub Actions Setup

1. Add your xAI API key to GitHub Secrets:
   - Go to Settings > Secrets and variables > Actions
   - Add a new secret named `XAI_API_KEY`
   - Get your API key from https://console.x.ai/

2. The workflow will automatically trigger when you:
   - Edit and commit `papers/kickoff.txt`
   - Manually trigger via Actions tab

## Project Structure

```
longevitypdf/
├── papers/                      # Place PDF papers here
│   └── kickoff.txt             # Edit this to trigger processing
├── processed_papers/            # Processed results (JSON)
│   └── .processed_tracker.json # Tracks which papers were processed
├── .github/
│   └── workflows/
│       └── process_papers.yml  # GitHub Action workflow
├── process_papers.py           # Main processing script
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

### Adding New Papers

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

- **Automatic Tracking**: Only processes new papers (tracked in `.processed_tracker.json`)
- **AI-Powered Extraction**: Uses Grok AI to intelligently extract longevity statistics
- **Error Handling**: Comprehensive logging and error handling
- **GitHub Integration**: Automatically commits processed results back to the repository

## Logs

Processing logs are saved to `processing.log` and include:
- Papers being processed
- Extraction results
- Any errors encountered

## Troubleshooting

**API Key Issues**: Ensure `XAI_API_KEY` is set in your environment or GitHub Secrets

**PDF Extraction Fails**: Some PDFs may be scanned images requiring OCR (not currently supported)

**GitHub Action Not Triggering**: Ensure you're committing changes to `papers/kickoff.txt` specifically

## Contributing

Feel free to open issues or submit pull requests for improvements.

## License

MIT
