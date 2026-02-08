from ..base_extractor import BaseExtractor


class MunicipioExtractor(BaseExtractor):
    field_name = "municipio"
    scope = "ente"
    
    def extract(self, record):
        ente_data = record.get('ente', {})
        return ente_data.get('municipio')
