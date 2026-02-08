from ..base_extractor import BaseExtractor

class IeDestinatarioExtractor(BaseExtractor):
    field_name = "ie_destinatario"
    scope = "nfe"

    def extract(self, record):
        return record.get("IE_DESTINATARIO")
