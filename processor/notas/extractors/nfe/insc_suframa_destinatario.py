from ..base_extractor import BaseExtractor

class InscSuframaDestinatarioExtractor(BaseExtractor):
    field_name = "insc_suframa_destinatario"
    scope = "nfe"

    def extract(self, record):
        return record.get("INSC_SUFRAMA_DESTINATARIO")
