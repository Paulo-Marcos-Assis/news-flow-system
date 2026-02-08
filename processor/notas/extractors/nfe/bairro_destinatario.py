from ..base_extractor import BaseExtractor

class BairroDestinatarioExtractor(BaseExtractor):
    field_name = "bairro_destinatario"
    scope = "nfe"
    
    def extract(self, record):
        return record.get("BAIRRO_DEST")
