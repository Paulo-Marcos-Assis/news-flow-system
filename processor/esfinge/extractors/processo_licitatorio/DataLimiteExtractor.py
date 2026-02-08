from ..base_extractor import BaseExtractor

class DataLimiteExtractor(BaseExtractor):
    field_name = "data_limite"
    scope = "processo_licitatorio"
    
    def extract(self, record):
        processo_licitatorio_data = record.get('processo_licitatorio', {})
        return processo_licitatorio_data.get('data_limite_entrega_propostas')
