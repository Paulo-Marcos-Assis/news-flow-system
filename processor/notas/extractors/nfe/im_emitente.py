from ..base_extractor import BaseExtractor

class ImEmitenteExtractor(BaseExtractor):
    field_name = "im_emitente"
    scope = "nfe"

    def extract(self, record):
        return record.get("IM_EMITENTE")
