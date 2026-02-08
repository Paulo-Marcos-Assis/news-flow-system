from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class NumeroContratoExtractor(BaseExtractor):
    field_name = "numero_contrato"

    def extract(self, record):
        return record.get("numeroContratoEmpenho", DEFAULT_VALUE)
