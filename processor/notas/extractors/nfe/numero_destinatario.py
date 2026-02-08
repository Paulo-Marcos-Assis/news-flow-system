from ..base_extractor import BaseExtractor

class NumeroDestinatarioExtractor(BaseExtractor):
    field_name = "numero_destinatario"
    scope = "nfe"

    def extract(self, record):
        return record.get("NRO_DEST")
