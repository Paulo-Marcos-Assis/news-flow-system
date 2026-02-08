from ..base_extractor import BaseExtractor

class NomeUgExtractor(BaseExtractor):
    field_name = "nome_ug"
    scope = "unidade_gestora"

    def extract(self, record):
        unidade_gestora_data = record.get('unidade_gestora', {})
        return unidade_gestora_data.get('unidade_gestora')