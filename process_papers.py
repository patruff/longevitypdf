#!/usr/bin/env python3
"""
Longevity Paper Processing Script

This script processes PDF papers from Google Drive or the papers/ folder to extract
longevity-related statistics including longevity_increase_percent, model_organism,
and intervention_used.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from openai import OpenAI
import PyPDF2
from google_drive_client import GoogleDriveClient

# Configuration
PAPERS_FOLDER = "papers"  # Fallback for local processing
PROCESSED_FOLDER = "processed_papers"
PROCESSED_TRACKER = "processed_papers/.processed_tracker.json"
LOG_FILE = "processing.log"
GOOGLE_DRIVE_FOLDER_NAME = "longevitypapers"  # Name of folder in Google Drive

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PaperProcessor:
    """Processes scientific papers to extract longevity data."""

    def __init__(self):
        self.papers_folder = Path(PAPERS_FOLDER)
        self.processed_folder = Path(PROCESSED_FOLDER)
        self.tracker_file = Path(PROCESSED_TRACKER)
        self.processed_papers = self._load_tracker()

        # Initialize Google Drive client
        self.drive_client = GoogleDriveClient()
        self.use_google_drive = self.drive_client.is_authenticated()

        if self.use_google_drive:
            logger.info("Using Google Drive as PDF source")
        else:
            logger.info("Google Drive not configured. Using local papers folder as fallback")

        # Initialize Grok client (xAI)
        api_key = os.getenv("XAI_API_KEY")
        if not api_key:
            logger.warning("XAI_API_KEY not set. AI extraction will not work.")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.x.ai/v1"
            )

    def _load_tracker(self) -> Dict:
        """Load the tracker file that keeps record of processed papers."""
        if self.tracker_file.exists():
            with open(self.tracker_file, 'r') as f:
                return json.load(f)
        return {"processed": []}

    def _save_tracker(self):
        """Save the tracker file."""
        self.processed_folder.mkdir(exist_ok=True)
        with open(self.tracker_file, 'w') as f:
            json.dump(self.processed_papers, f, indent=2)

    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text content from a PDF file."""
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ""

    def _extract_longevity_stats(self, text: str, filename: str) -> Optional[Dict]:
        """
        Extract longevity statistics from paper text using Grok AI.

        Returns a dictionary with:
        - longevity_increase_percent: float or str
        - model_organism: str
        - intervention_used: str
        """
        if not self.client:
            logger.error("Grok client not initialized. Cannot extract stats.")
            return None

        if not text.strip():
            logger.error(f"No text extracted from {filename}")
            return None

        try:
            # Truncate text if too long (Grok has token limits)
            max_chars = 100000
            if len(text) > max_chars:
                text = text[:max_chars] + "\n\n[TEXT TRUNCATED]"

            prompt = f"""Analyze this scientific paper about longevity and extract the following information:

1. longevity_increase_percent: The percentage increase in lifespan/longevity (e.g., "25%", "15.5%"). If multiple values are mentioned, prioritize the main/maximum finding.
2. model_organism: The organism studied (e.g., "C. elegans", "mice", "rats", "yeast", "fruit flies", "humans")
3. intervention_used: The intervention or treatment used (e.g., "caloric restriction", "rapamycin", "metformin", "exercise")

Paper text:
{text}

Return ONLY a JSON object with these three fields. If any information is not found, use null. Example:
{{"longevity_increase_percent": "25%", "model_organism": "C. elegans", "intervention_used": "rapamycin"}}"""

            response = self.client.chat.completions.create(
                model="grok-4-fast-non-reasoning",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract JSON from response
            response_text = response.choices[0].message.content.strip()

            # Try to parse JSON, handling potential markdown code blocks
            if response_text.startswith("```"):
                # Remove markdown code block formatting
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text

            stats = json.loads(response_text)
            logger.info(f"Successfully extracted stats from {filename}")
            return stats

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for {filename}: {e}")
            logger.error(f"Response was: {response_text}")
            return None
        except Exception as e:
            logger.error(f"Error extracting stats from {filename}: {e}")
            return None

    def _get_unprocessed_papers(self) -> List[Path]:
        """Get list of PDF files that haven't been processed yet."""
        all_pdfs = []

        if self.use_google_drive:
            # Fetch PDFs from Google Drive
            logger.info(f"Fetching PDFs from Google Drive folder: {GOOGLE_DRIVE_FOLDER_NAME}")
            all_pdfs = self.drive_client.download_all_pdfs_from_folder(GOOGLE_DRIVE_FOLDER_NAME)

            if not all_pdfs:
                logger.warning("No PDFs downloaded from Google Drive")
                return []
        else:
            # Fallback to local papers folder
            if not self.papers_folder.exists():
                logger.warning(f"Papers folder {self.papers_folder} does not exist")
                return []

            all_pdfs = list(self.papers_folder.glob("*.pdf"))

        # Filter out already processed papers
        unprocessed = [
            pdf for pdf in all_pdfs
            if pdf.name not in self.processed_papers["processed"]
        ]

        return unprocessed

    def process_paper(self, pdf_path: Path) -> bool:
        """
        Process a single paper and save results.

        Returns True if successful, False otherwise.
        """
        logger.info(f"Processing {pdf_path.name}...")

        # Extract text from PDF
        text = self._extract_text_from_pdf(pdf_path)
        if not text:
            logger.error(f"Could not extract text from {pdf_path.name}")
            return False

        # Extract longevity stats
        stats = self._extract_longevity_stats(text, pdf_path.name)
        if not stats:
            logger.error(f"Could not extract stats from {pdf_path.name}")
            return False

        # Prepare output
        output = {
            "filename": pdf_path.name,
            "processed_at": datetime.now().isoformat(),
            "stats": stats,
            "raw_text_preview": text[:1000] + "..." if len(text) > 1000 else text
        }

        # Save to processed folder
        output_filename = pdf_path.stem + "_processed.json"
        output_path = self.processed_folder / output_filename

        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)

        logger.info(f"Saved processed data to {output_path}")

        # Update tracker
        self.processed_papers["processed"].append(pdf_path.name)
        self._save_tracker()

        return True

    def process_all(self):
        """Process all unprocessed papers from Google Drive or local folder."""
        unprocessed = self._get_unprocessed_papers()

        if not unprocessed:
            logger.info("No new papers to process")
            return

        logger.info(f"Found {len(unprocessed)} paper(s) to process")

        success_count = 0
        for pdf_path in unprocessed:
            if self.process_paper(pdf_path):
                success_count += 1

        logger.info(f"Successfully processed {success_count}/{len(unprocessed)} papers")

        # Cleanup temporary files if using Google Drive
        if self.use_google_drive:
            self.drive_client.cleanup_temp_files()

    def cleanup(self):
        """Clean up resources (temporary files, etc.)."""
        if self.use_google_drive:
            self.drive_client.cleanup_temp_files()


def main():
    """Main entry point for the script."""
    logger.info("=" * 60)
    logger.info("Starting Longevity Paper Processing")
    logger.info("=" * 60)

    processor = PaperProcessor()

    try:
        processor.process_all()
    finally:
        # Ensure cleanup happens even if there's an error
        processor.cleanup()

    logger.info("=" * 60)
    logger.info("Processing Complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
