from ..base_extractor import BaseExtractor

class DescricaoTipoEspecificacaoUGExtractor(BaseExtractor):
    field_name = "descricao"
    scope = "tipo_especificacao_ug"
    
    def extract(self, record):
        unidade_gestora_data = record.get('unidade_gestora', {})
        return unidade_gestora_data.get('nome_unidade_orcamentaria')
