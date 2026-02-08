from ..base_extractor import BaseExtractor

class CplDestinatarioExtractor(BaseExtractor):
    field_name = "cpl_destinatario"
    scope = "nfe"

    def extract(self, record):
        return record.get("CPL_DEST")
