from ..base_extractor import BaseExtractor

class ValorUnitarioLiquidoExtractor(BaseExtractor):
    field_name = "valor_unitario_liquido"
    scope = "item"

    def extract(self, record):
        return record.get("Valor_Unitario_Liquido")
