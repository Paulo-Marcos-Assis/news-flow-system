from ..base_extractor import BaseExtractor

class NumeroEditalExtractor(BaseExtractor):
    field_name = "numero_edital"
    scope = "processo_licitatorio"
    
    def extract(self, record):
        processo_licitatorio_data = record.get('processo_licitatorio', {})
        return processo_licitatorio_data.get('numero_edital')
