from ..base_extractor import BaseExtractor, DEFAULT_VALUE

class DataEmissaoExtractor(BaseExtractor):
    field_name = "data_emissao"

    def extract(self, data):
        return data.get("dataPublicacaoPncp", DEFAULT_VALUE)
