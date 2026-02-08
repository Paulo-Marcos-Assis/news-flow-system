from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class DataVencimentoExtractor(BaseExtractor):
    field_name = "data_abertura_certame"

    def extract(self, record):
        return record.get("dataAberturaProposta", DEFAULT_VALUE)