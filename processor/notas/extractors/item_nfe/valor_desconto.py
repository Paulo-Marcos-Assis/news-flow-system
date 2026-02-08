from ..base_extractor import BaseExtractor

class ValorDescontoExtractor(BaseExtractor):
    field_name = "valor_desconto"
    scope = "item"

    def extract(self, record):
        return record.get("VALOR_DESCONTO")
