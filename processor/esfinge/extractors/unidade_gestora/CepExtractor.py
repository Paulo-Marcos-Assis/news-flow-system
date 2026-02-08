from ..base_extractor import BaseExtractor

class CepExtractor(BaseExtractor):
    field_name = "cep"
    scope = "unidade_gestora"
    
    def extract(self, record):
        unidade_gestora_data = record.get('unidade_gestora', {})
        return unidade_gestora_data.get('cep')
