from ..base_extractor import BaseExtractor

class EnteExtractor(BaseExtractor):

    field = "ente"

    def extract_from_heuristic(self, record):
        return record.get("municipio")

    def extract_from_model(self, record):
        pass