from ..base_extractor import BaseExtractor

class DescricaoObjetoExtractor(BaseExtractor):
    field_name = "descricao_objeto"
    scope = "processo_licitatorio"

    def extract(self, record):
        processo_licitatorio_data = record.get('processo_licitatorio', {})
        return processo_licitatorio_data.get('descricao_objeto_licitacao')
