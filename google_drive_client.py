"""
Google Drive client for accessing and downloading PDF files from a specified folder.
"""
import os
import json
import logging
import tempfile
from pathlib import Path
from typing import List, Optional, Dict
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

logger = logging.getLogger(__name__)


class GoogleDriveClient:
    """Client for interacting with Google Drive API."""

    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

    def __init__(self, credentials_json: Optional[str] = None):
        """
        Initialize Google Drive client.

        Args:
            credentials_json: JSON string containing service account credentials.
                            If None, will try to load from GOOGLE_CREDENTIALS env var.
        """
        self.service = None
        self.temp_dir = None

        # Get credentials from parameter or environment variable
        if credentials_json is None:
            credentials_json = os.getenv('GOOGLE_CREDENTIALS')

        if not credentials_json:
            logger.warning("No Google Drive credentials provided. Set GOOGLE_CREDENTIALS environment variable.")
            return

        try:
            # Parse credentials JSON
            credentials_dict = json.loads(credentials_json)

            # Create credentials from service account info
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=self.SCOPES
            )

            # Build the Drive API service
            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("Successfully authenticated with Google Drive")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in Google credentials: {e}")
        except Exception as e:
            logger.error(f"Error initializing Google Drive client: {e}")

    def is_authenticated(self) -> bool:
        """Check if the client is authenticated."""
        return self.service is not None

    def find_folder(self, folder_name: str) -> Optional[str]:
        """
        Find a folder by name in Google Drive.

        Args:
            folder_name: Name of the folder to find

        Returns:
            Folder ID if found, None otherwise
        """
        if not self.is_authenticated():
            logger.error("Not authenticated with Google Drive")
            return None

        try:
            # Search for folder by name
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=10
            ).execute()

            items = results.get('files', [])

            if not items:
                logger.error(f"Folder '{folder_name}' not found in Google Drive")
                return None

            if len(items) > 1:
                logger.warning(f"Multiple folders named '{folder_name}' found. Using the first one.")

            folder_id = items[0]['id']
            logger.info(f"Found folder '{folder_name}' with ID: {folder_id}")
            return folder_id

        except Exception as e:
            logger.error(f"Error finding folder '{folder_name}': {e}")
            return None

    def list_pdfs_in_folder(self, folder_id: str) -> List[Dict[str, str]]:
        """
        List all PDF files in a specific folder.

        Args:
            folder_id: Google Drive folder ID

        Returns:
            List of dictionaries with 'id' and 'name' keys for each PDF
        """
        if not self.is_authenticated():
            logger.error("Not authenticated with Google Drive")
            return []

        try:
            # Search for PDF files in the folder
            query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, modifiedTime)',
                pageSize=100,
                orderBy='modifiedTime desc'
            ).execute()

            items = results.get('files', [])
            logger.info(f"Found {len(items)} PDF files in folder")

            return items

        except Exception as e:
            logger.error(f"Error listing PDFs in folder: {e}")
            return []

    def download_pdf(self, file_id: str, file_name: str, destination_dir: Path) -> Optional[Path]:
        """
        Download a PDF file from Google Drive.

        Args:
            file_id: Google Drive file ID
            file_name: Name of the file
            destination_dir: Directory to save the file

        Returns:
            Path to downloaded file, or None if download failed
        """
        if not self.is_authenticated():
            logger.error("Not authenticated with Google Drive")
            return None

        try:
            # Request file content
            request = self.service.files().get_media(fileId=file_id)

            # Create destination path
            destination_path = destination_dir / file_name

            # Download file
            with io.FileIO(destination_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        logger.debug(f"Download {int(status.progress() * 100)}% complete for {file_name}")

            logger.info(f"Downloaded '{file_name}' to {destination_path}")
            return destination_path

        except Exception as e:
            logger.error(f"Error downloading file '{file_name}': {e}")
            return None

    def download_all_pdfs_from_folder(self, folder_name: str) -> List[Path]:
        """
        Download all PDFs from a named folder.

        Args:
            folder_name: Name of the Google Drive folder

        Returns:
            List of paths to downloaded PDF files
        """
        downloaded_files = []

        # Find the folder
        folder_id = self.find_folder(folder_name)
        if not folder_id:
            return downloaded_files

        # List PDFs in the folder
        pdf_files = self.list_pdfs_in_folder(folder_id)
        if not pdf_files:
            logger.warning(f"No PDF files found in folder '{folder_name}'")
            return downloaded_files

        # Create temporary directory for downloads
        self.temp_dir = Path(tempfile.mkdtemp(prefix='longevity_pdfs_'))
        logger.info(f"Created temporary directory: {self.temp_dir}")

        # Download each PDF
        for pdf_file in pdf_files:
            file_id = pdf_file['id']
            file_name = pdf_file['name']

            downloaded_path = self.download_pdf(file_id, file_name, self.temp_dir)
            if downloaded_path:
                downloaded_files.append(downloaded_path)

        logger.info(f"Successfully downloaded {len(downloaded_files)} of {len(pdf_files)} PDFs")
        return downloaded_files

    def cleanup_temp_files(self):
        """Clean up temporary downloaded files."""
        if self.temp_dir and self.temp_dir.exists():
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                logger.error(f"Error cleaning up temporary directory: {e}")
