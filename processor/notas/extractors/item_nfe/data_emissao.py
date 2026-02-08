from ..base_extractor import BaseExtractor

class DataEmissaoExtractor(BaseExtractor):
    field_name = "data_emissao"
    scope = "item"
    
    def extract(self, record):
        return record.get("DATA_EMISSAO_NOTA")
