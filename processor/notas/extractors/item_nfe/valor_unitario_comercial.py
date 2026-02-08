from ..base_extractor import BaseExtractor

class ValorUnitarioComercialExtractor(BaseExtractor):
    field_name = "valor_unitario_comercial"
    scope = "item"

    def extract(self, record):
        return record.get("VALOR_UNITARIO_COMERCIAL")
