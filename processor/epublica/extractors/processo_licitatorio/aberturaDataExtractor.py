from ..base_extractor import BaseExtractor

class DataAberturaExtractor(BaseExtractor):
    field_name = "data_abertura_certame"
    scope = "processo_licitatorio"

    def extract(self, record):

        return record.get("licitacao", {}).get("aberturaData")