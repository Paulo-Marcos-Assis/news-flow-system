from ..base_extractor import BaseExtractor

class DataAberturaCertameExtractor(BaseExtractor):
    field_name = "data_abertura_certame"
    scope = "processo_licitatorio"
    
    def extract(self, record):
        processo_licitatorio_data = record.get('processo_licitatorio', {})
        return processo_licitatorio_data.get('data_abertura_certame')
