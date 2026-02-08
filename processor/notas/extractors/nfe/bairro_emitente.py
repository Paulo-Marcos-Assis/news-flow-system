from ..base_extractor import BaseExtractor

class BairroEmitenteExtractor(BaseExtractor):
    field_name = "bairro_emitente"
    scope = "nfe"
    
    def extract(self, record):
        return record.get("BAIRRO_EMITENTE")
