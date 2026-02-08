from ..base_extractor import BaseExtractor

class EnteExtractor(BaseExtractor):
    field_name = "ente"
    scope = "ente"
    
    def extract(self, record):
        ente_data = record.get('ente', {})
        return ente_data.get('ente')
