from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class EditalExtractor(BaseExtractor):
    field_name = "numero_edital"

    def extract(self, record):
        numero_compra = record.get("numeroCompra")
        ano_compra = record.get("anoCompra")

        if numero_compra is not None and ano_compra is not None:
            return f"{numero_compra}/{ano_compra}"
        
        return DEFAULT_VALUE
