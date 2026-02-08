from ..base_extractor import BaseExtractor

class CnpjExtractor(BaseExtractor):
    field_name = "cnpj"
    scope = "unidade_gestora"

    def extract(self, record):
        unidade_gestora_data = record.get('unidade_gestora', {})
        return unidade_gestora_data.get('cnpj_unidade_gestora')

