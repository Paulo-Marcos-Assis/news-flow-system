from ..base_extractor import BaseExtractor

class ValorEmpenhoExtractor(BaseExtractor):
    field_name = "valor_empenho"
    scope = "empenho"

    def extract(self, record):
        empenho_data = record.get('empenho', {})
        return empenho_data.get('valor_empenho')
