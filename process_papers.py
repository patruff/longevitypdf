#!/usr/bin/env python3
"""
Longevity Paper Processing Script

This script processes PDF papers from Google Drive folder 'longevitypapers' to extract
longevity-related statistics including longevity_increase_percent, model_organism,
and intervention_used. Processed results are saved back to Google Drive in a
'processed_papers' subfolder within 'longevitypapers'.
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
LOG_FILE = "processing.log"
GOOGLE_DRIVE_FOLDER_NAME = "longevitypapers"  # Name of folder in Google Drive
PROCESSED_SUBFOLDER_NAME = "processed_papers"  # Subfolder within longevitypapers
TRACKER_FILE_NAME = ".processed_tracker.json"  # Tracker file name

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
        # Initialize Google Drive client
        self.drive_client = GoogleDriveClient()

        if not self.drive_client.is_authenticated():
            raise ValueError("Google Drive authentication failed. Please set GOOGLE_DRIVE_CREDENTIALS environment variable.")

        logger.info("Successfully authenticated with Google Drive")

        # Find the main longevitypapers folder
        self.main_folder_id = self.drive_client.find_folder(GOOGLE_DRIVE_FOLDER_NAME)
        if not self.main_folder_id:
            raise ValueError(f"Could not find '{GOOGLE_DRIVE_FOLDER_NAME}' folder in Google Drive")

        # Find or create the processed_papers subfolder
        self.processed_folder_id = self.drive_client.find_or_create_subfolder(
            self.main_folder_id,
            PROCESSED_SUBFOLDER_NAME
        )

        if not self.processed_folder_id:
            raise ValueError(f"Could not create '{PROCESSED_SUBFOLDER_NAME}' subfolder")

        logger.info(f"Using Google Drive folder '{GOOGLE_DRIVE_FOLDER_NAME}' for processing")

        # Load tracker from Google Drive
        self.processed_papers = self._load_tracker()

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
        """Load the tracker file from Google Drive."""
        try:
            content = self.drive_client.download_file_content(
                self.processed_folder_id,
                TRACKER_FILE_NAME
            )

            if content:
                tracker_data = json.loads(content)
                logger.info(f"Loaded tracker with {len(tracker_data.get('processed', []))} processed papers")
                return tracker_data
            else:
                logger.info("No existing tracker file found, creating new one")
                return {"processed": []}

        except Exception as e:
            logger.error(f"Error loading tracker: {e}")
            return {"processed": []}

    def _save_tracker(self):
        """Save the tracker file to Google Drive."""
        try:
            tracker_json = json.dumps(self.processed_papers, indent=2)

            # Check if tracker file already exists
            existing_file_id = self.drive_client.file_exists_in_folder(
                self.processed_folder_id,
                TRACKER_FILE_NAME
            )

            if existing_file_id:
                # Update existing file
                self.drive_client.update_file_content(existing_file_id, tracker_json)
                logger.info("Updated tracker file in Google Drive")
            else:
                # Create new file
                self.drive_client.upload_json_content(
                    tracker_json,
                    self.processed_folder_id,
                    TRACKER_FILE_NAME
                )
                logger.info("Created new tracker file in Google Drive")

        except Exception as e:
            logger.error(f"Error saving tracker: {e}")

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
        """Get list of PDF files from Google Drive that haven't been processed yet."""
        logger.info(f"Fetching PDFs from Google Drive folder: {GOOGLE_DRIVE_FOLDER_NAME}")

        # Download all PDFs from Google Drive
        all_pdfs = self.drive_client.download_all_pdfs_from_folder(GOOGLE_DRIVE_FOLDER_NAME)

        if not all_pdfs:
            logger.warning("No PDFs found in Google Drive")
            return []

        # Filter out already processed papers
        unprocessed = [
            pdf for pdf in all_pdfs
            if pdf.name not in self.processed_papers["processed"]
        ]

        logger.info(f"Found {len(unprocessed)} unprocessed papers out of {len(all_pdfs)} total")
        return unprocessed

    def process_paper(self, pdf_path: Path) -> bool:
        """
        Process a single paper and save results to Google Drive.

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

        # Save to Google Drive processed folder
        output_filename = pdf_path.stem + "_processed.json"
        output_json = json.dumps(output, indent=2)

        file_id = self.drive_client.upload_json_content(
            output_json,
            self.processed_folder_id,
            output_filename
        )

        if not file_id:
            logger.error(f"Failed to upload processed data for {pdf_path.name} to Google Drive")
            return False

        logger.info(f"Saved processed data to Google Drive: {output_filename}")

        # Update tracker
        self.processed_papers["processed"].append(pdf_path.name)
        self._save_tracker()

        return True

    def process_all(self):
        """Process all unprocessed papers from Google Drive."""
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

        # Cleanup temporary downloaded files
        self.drive_client.cleanup_temp_files()

    def cleanup(self):
        """Clean up resources (temporary files, etc.)."""
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
