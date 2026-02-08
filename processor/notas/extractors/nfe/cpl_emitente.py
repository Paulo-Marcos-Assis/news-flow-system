from ..base_extractor import BaseExtractor

class CplEmitenteExtractor(BaseExtractor):
    field_name = "cpl_emitente"
    scope = "nfe"

    def extract(self, record):
        return record.get("CPL_EMITENTE")
