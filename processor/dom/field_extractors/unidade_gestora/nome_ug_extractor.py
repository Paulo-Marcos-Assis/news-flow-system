from ..base_extractor import BaseExtractor

class EnteExtractor(BaseExtractor):

    field = "nome_ug"

    def extract_from_heuristic(self, record):
        return record.get("entidade")

    def extract_from_model(self, record):
        pass