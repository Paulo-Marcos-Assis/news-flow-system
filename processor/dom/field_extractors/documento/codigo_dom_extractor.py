from ..base_extractor import BaseExtractor

class CodigoDomExtractor(BaseExtractor):

    field = "codigo_dom"

    def extract_from_heuristic(self, record):
        return record.get("codigo")

    def extract_from_model(self, record):
        pass