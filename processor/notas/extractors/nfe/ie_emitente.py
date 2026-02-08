from ..base_extractor import BaseExtractor

class IeEmitenteExtractor(BaseExtractor):
    field_name = "ie_emitente"
    scope = "nfe"

    def extract(self, record):
        return record.get("IE_EMITENTE")
