from ..base_extractor import BaseExtractor

class ValorOutrasDespesasExtractor(BaseExtractor):
    field_name = "valor_outras_despesas"
    scope = "item"

    def extract(self, record):
        return record.get("VALOR_OUTRAS_DESPESAS")
