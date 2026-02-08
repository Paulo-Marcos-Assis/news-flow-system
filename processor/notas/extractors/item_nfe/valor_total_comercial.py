from ..base_extractor import BaseExtractor

class ValorTotalComercialExtractor(BaseExtractor):
    field_name = "valor_total_comercial"
    scope = "item"

    def extract(self, record):
        return record.get("Valor_Total_Comercial")
