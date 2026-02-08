from ..base_extractor import BaseExtractor

class DescricaoExtractor(BaseExtractor):
    field_name = "descricao"
    scope = "tipo_cotacao"
    
    def extract(self, record):
        tipo_data = record.get('tipo_cotacao', {})
        return tipo_data.get('descricao')
