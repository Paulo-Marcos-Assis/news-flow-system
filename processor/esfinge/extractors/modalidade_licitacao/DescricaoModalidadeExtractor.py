from ..base_extractor import BaseExtractor

class DescricaoExtractor(BaseExtractor):
    field_name = "descricao"
    scope = "modalidade_licitacao"
    
    def extract(self, record):
        modalidade_data = record.get('modalidade_licitacao', {})
        return modalidade_data.get('descricao')