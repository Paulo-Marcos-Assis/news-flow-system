from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class DataAssinaturaExtractor(BaseExtractor):
    field_name = "data_assinatura"

    def extract(self, record):
        return record.get("dataAssinatura", DEFAULT_VALUE)
