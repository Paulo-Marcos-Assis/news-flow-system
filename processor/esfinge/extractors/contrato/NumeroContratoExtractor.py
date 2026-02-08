from ..base_extractor import BaseExtractor

class NumeroContratoExtractor(BaseExtractor):
    field_name = "numero_contrato"
    scope = "contrato"
    
    def extract(self, record):
        contrato_data = record.get('contrato', {})
        return contrato_data.get('numero_contrato')
