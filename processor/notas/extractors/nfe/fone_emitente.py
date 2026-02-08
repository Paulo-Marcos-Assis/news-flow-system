from ..base_extractor import BaseExtractor

class FoneEmitenteExtractor(BaseExtractor):
    field_name = "fone_emitente"
    scope = "nfe"

    def extract(self, record):
        return record.get("FONE_EMITENTE")
