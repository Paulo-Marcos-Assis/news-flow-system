from ..base_extractor import BaseExtractor

class IeStEmitenteExtractor(BaseExtractor):
    field_name = "ie_st_emitente"
    scope = "nfe"

    def extract(self, record):
        return record.get("IE_ST_EMITENTE")
