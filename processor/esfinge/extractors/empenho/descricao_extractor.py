from ..base_extractor import BaseExtractor

class DescricaoEmpenhoExtractor(BaseExtractor):
    field_name = "descricao"
    scope = "empenho"

    def extract(self, record):
        empenho_data = record.get('empenho', {})
        return empenho_data.get('descricao_historico_empenho')
