from ..base_extractor import BaseExtractor

class CodigoSfingeExtractor(BaseExtractor):

    field = "codigo_sfinge"

    def extract_from_heuristic(self, record):
        return record.get("cod_registro_info_sfinge")

    def extract_from_model(self, record):
        pass