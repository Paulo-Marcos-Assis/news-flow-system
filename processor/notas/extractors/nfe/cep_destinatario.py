from ..base_extractor import BaseExtractor

class CepDestinatarioSExtractor(BaseExtractor):
    field_name = "cep_destinatario"
    scope = "nfe"
    
    def extract(self, record):
        return record.get("CEP_DEST")
