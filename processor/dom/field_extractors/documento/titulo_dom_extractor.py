from ..base_extractor import BaseExtractor

class TituloDomExtractor(BaseExtractor):

    field = "titulo_dom"

    def extract_from_heuristic(self, record):
        return record.get("titulo")

    def extract_from_model(self, record):
        pass