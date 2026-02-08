from ..base_extractor import BaseExtractor

class DescricaoObjetivoExtractor(BaseExtractor):
    field_name = "descricao_objetivo"
    scope = "contrato"
    
    def extract(self, record):
        contrato_data = record.get('contrato', {})
        return contrato_data.get('descricao_objetivo')