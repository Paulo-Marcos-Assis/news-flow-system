from ..base_extractor import BaseExtractor

class CrtEmitenteExtractor(BaseExtractor):
    field_name = "crt_emitente"
    scope = "nfe"

    def extract(self, record):
        return record.get("CRT_EMITENTE")
