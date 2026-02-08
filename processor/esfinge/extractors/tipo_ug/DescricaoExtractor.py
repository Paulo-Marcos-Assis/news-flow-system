from ..base_extractor import BaseExtractor

class Descricao_Tipo_Ug_Extractor(BaseExtractor):
    field_name = "descricao"
    scope = "tipo_ug"
    
    def extract(self, record):
        tipo_ug_data = record.get('tipo_unidade', {})
        return tipo_ug_data.get('tipo_unidade')
