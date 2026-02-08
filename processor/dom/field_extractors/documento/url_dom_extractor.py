from ..base_extractor import BaseExtractor

class UrlDomExtractor(BaseExtractor):

    field = "url_dom"

    def extract_from_heuristic(self, record):
        return record.get("link")

    def extract_from_model(self, record):
        pass