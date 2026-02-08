import hashlib
import os
import shutil
import tempfile
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from service_essentials.object_storage_manager.object_storage_manager import (
    ObjectStorageManager,
)

from ..base_extractor import BaseExtractor, DEFAULT_VALUE


class LocalAcessoArquivoExtractor(BaseExtractor):
    field_name = "local_acesso_arquivo"

    def __init__(self, logger_instance, object_storage_manager):
        super().__init__(logger_instance, object_storage_manager)
        self.session = self._create_retry_session()
        self.bucket = os.getenv("PUBLIC_BUCKET", "workflow-hmg")
        self.logger.info(f"Extractor '{self.field_name}' initialized with bucket: {self.bucket}")

    def _create_retry_session(self) -> requests.Session:
        """
        Creates a requests Session with a retry mechanism.
        """
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def extract(self, data: dict[str, Any]) -> str:
        """
        Extracts a document URL, downloads it, stores in object storage,
        and returns the object storage path.
        """
        self.logger.debug(f"Extractor '{self.field_name}' received data: {data}")
        download_url = data.get("url") or data.get("uri")
        
        if not download_url:
            self.logger.warning(f"Extractor '{self.field_name}': No download URL found in data: {data}. Returning DEFAULT_VALUE.")
            return DEFAULT_VALUE

        self.logger.info(f"Extractor '{self.field_name}': Attempting to download and store document from URL: {download_url}")
        object_name = self._download_and_store_in_object_storage(download_url)
        
        if object_name:
            s3_path = f"{object_name}"
            self.logger.info(f"Extractor '{self.field_name}': Successfully processed. S3 path: {s3_path}")
            return s3_path
        
        self.logger.error(f"Extractor '{self.field_name}': Failed to download or store document from URL: {download_url}. Returning DEFAULT_VALUE.")
        return DEFAULT_VALUE

    def _download_and_store_in_object_storage(self, url: str) -> Optional[str]:
        if not url:
            self.logger.error("Attempted to download with an empty URL. Aborting.")
            return None

        temp_file_path = None
        try:
            self.logger.debug(f"Downloading document from: {url}")
            response = self.session.get(url, stream=True)
            response.raise_for_status()

            url_hash = hashlib.sha256(url.encode()).hexdigest()
            try:
                filename_from_url = url.split("/")[-1].split("?")[0]
                _, extension = os.path.splitext(filename_from_url)
                if not extension:
                    content_type = response.headers.get("Content-Type", "")
                    if "pdf" in content_type:
                        extension = ".pdf"
                    elif "xml" in content_type:
                        extension = ".xml"
                    elif "json" in content_type:
                        extension = ".json"
                    elif "zip" in content_type:
                        extension = ".zip"
                    else:
                        extension = ""  # Default to no extension if content type also doesn't help
            except Exception as e:
                self.logger.warning(f"Could not determine extension from URL {url}: {e}. No extension will be used.")
                extension = ""  # Default to no extension on exception

            object_name = f"documents/{url_hash}{extension}"

            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                shutil.copyfileobj(response.raw, tmp_file)
                temp_file_path = tmp_file.name

            self.logger.debug(
                f"Uploading temp file {temp_file_path} to object storage at path: {object_name}"
            )
            self.object_storage_manager.upload_file(
                self.bucket, object_name, temp_file_path
            )
            self.logger.info(
                f"Successfully uploaded document from {url} to {object_name}"
            )

            return object_name

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to download document from {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(
                f"Failed to upload document from {url} to object storage: {e}"
            )
            return None
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                self.logger.debug(f"Cleaned up temporary file: {temp_file_path}")