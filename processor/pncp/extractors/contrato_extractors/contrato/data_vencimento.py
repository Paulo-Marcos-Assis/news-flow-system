from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class DataVencimentoExtractor(BaseExtractor):
    field_name = "data_vencimento"

    def extract(self, record):
        return record.get("dataVigenciaFim", DEFAULT_VALUE)
