from ..base_extractor import BaseExtractor

class DataEmpenhoExtractor(BaseExtractor):
    field_name = "data_empenho"
    scope = "empenho"

    def extract(self, record):
        empenho_data = record.get('empenho', {})
        return empenho_data.get('data_empenho')
