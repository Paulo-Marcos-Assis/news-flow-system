from ..base_extractor import BaseExtractor

class ValorFreteExtractor(BaseExtractor):
    field_name = "valor_frete"
    scope = "item"

    def extract(self, record):
        return record.get("VALOR_FRETE")
