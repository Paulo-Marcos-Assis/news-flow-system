from ..base_extractor import BaseExtractor

class ValorSeguroExtractor(BaseExtractor):
    field_name = "valor_seguro"
    scope = "item"

    def extract(self, record):
        return record.get("VALOR_SEGURO")
