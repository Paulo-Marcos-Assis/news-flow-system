from ..base_extractor import BaseExtractor

class ValorTotalLiquidoExtractor(BaseExtractor):
    field_name = "valor_total_liquido"
    scope = "item"

    def extract(self, record):
        return record.get("Valor_Total_Liquido")
