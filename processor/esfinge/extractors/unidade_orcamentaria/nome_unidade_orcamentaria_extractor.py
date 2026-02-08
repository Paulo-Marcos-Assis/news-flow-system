from ..base_extractor import BaseExtractor

class NomeUnidadeOrcamentariaExtractor(BaseExtractor):
    field_name = "nome_unidade_orcamentaria"
    scope = "unidade_orcamentaria"

    def extract(self, record):
        unidade_orcamentaria_data = record.get('unidade_orcamentaria', {})
        return unidade_orcamentaria_data.get('nome_unidade_orcamentaria')
