from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class DataVencimentoExtractor(BaseExtractor):
    field_name = "data_limite"

    def extract(self, record):
        return record.get("dataEncerramentoProposta", DEFAULT_VALUE)