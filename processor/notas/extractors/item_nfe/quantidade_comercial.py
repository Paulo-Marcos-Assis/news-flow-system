from ..base_extractor import BaseExtractor

class QuantidadeComercialExtractor(BaseExtractor):
    field_name = "quantidade_comercial"
    scope = "item"

    def extract(self, record):
        return record.get("QUANTIDADE_COMERCIAL")
