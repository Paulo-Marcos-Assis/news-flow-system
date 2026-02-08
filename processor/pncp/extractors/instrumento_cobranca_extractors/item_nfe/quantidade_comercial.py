from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class QuantidadeComercialExtractor(BaseExtractor):
    field_name = "quantidade_comercial"

    def extract(self, item):
        try:
         return float(item.get("quantidade", DEFAULT_VALUE))
        except (ValueError, TypeError):
         return DEFAULT_VALUE
    
