from ..base_extractor import BaseExtractor

class DataPublicacaoDomExtractor(BaseExtractor):

    field = "data_publicacao_dom"

    def extract_from_heuristic(self, record):
        return record.get("data")

    def extract_from_model(self, record):
        pass