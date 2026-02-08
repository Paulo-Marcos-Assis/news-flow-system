from ..base_extractor import BaseExtractor

class DescricaoExtractor(BaseExtractor):
    field_name = "descricao"
    scope = "tipo_objeto_licitacao"
    
    def extract(self, record):
        tipo_data = record.get('tipo_objeto_licitacao', {})
        return tipo_data.get('descricao')
