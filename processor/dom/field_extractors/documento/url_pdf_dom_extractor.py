from ..base_extractor import BaseExtractor

from service_essentials.object_storage_manager.object_storage_manager_factory import ObjectStoreManagerFactory
from utils.dom_utils import DomUtils
import os
import hashlib
import datetime

class UrlPdfDomExtractor(BaseExtractor):
    field = "url_pdf_dom"

    def extract_from_heuristic(self, record):        
        bucket_name = os.getenv("PUBLIC_BUCKET", "workflow-hmg")
        url_hash = hashlib.sha256(record.get('url').encode()).hexdigest()
        data = datetime.datetime.strptime(record.get('data'), "%Y-%m-%d %H:%M:%S") 
        object_name = f"documents/{data.year}/{data.month}/{data.day}/{url_hash}{'.pdf'}"

        return DomUtils.download_and_store(record.get('url'), bucket_name, object_name, self.object_storage_manager, self.logger)

    def extract_from_model(self, record):
        pass
