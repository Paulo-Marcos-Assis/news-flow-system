from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class ValorUnitarioComercialExtractor(BaseExtractor):
    field_name = "valor_unitario_comercial"

    def extract(self, item):
        try:
         return float(item.get("valorUnitario", DEFAULT_VALUE))
        except (ValueError, TypeError):
         return DEFAULT_VALUE
