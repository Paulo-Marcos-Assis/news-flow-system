from ..base_extractor import BaseExtractor

class NumEmpenhoExtractor(BaseExtractor):
    field_name = "num_empenho"
    scope = "empenho"

    def extract(self, record):
        empenho_data = record.get('empenho', {})
        return empenho_data.get('num_empenho')
