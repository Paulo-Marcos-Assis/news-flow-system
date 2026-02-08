from ..base_extractor import BaseExtractor

class DataSaidaExtractor(BaseExtractor):
    field_name = "data_saida"
    scope = "nfe"

    def extract(self, record):
        return record.get("DATA_SAIDA")
