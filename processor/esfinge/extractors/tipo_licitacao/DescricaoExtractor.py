from ..base_extractor import BaseExtractor

class DescricaoTipoLicitacaoExtractor(BaseExtractor):
    field_name = "descricao"
    scope = "tipo_licitacao"
    
    def extract(self, record):
        tipo_data = record.get('tipo_licitacao', {})
        return tipo_data.get('descricao')
