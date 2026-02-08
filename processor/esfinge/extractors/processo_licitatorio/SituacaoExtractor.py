from ..base_extractor import BaseExtractor

class SituacaoExtractor(BaseExtractor):
    field_name = "situacao"
    scope = "processo_licitatorio"
    
    def extract(self, record):
        processo_licitatorio_data = record.get('processo_licitatorio', {})
        situacao = processo_licitatorio_data.get('situacao_processo_licitatorio', [{}])[0]
        return situacao.get('descricao')
