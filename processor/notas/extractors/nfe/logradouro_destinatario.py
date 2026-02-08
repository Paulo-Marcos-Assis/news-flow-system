from ..base_extractor import BaseExtractor

class LogradouroDestinatarioExtractor(BaseExtractor):
    field_name = "logradouro_destinatario"
    scope = "nfe"

    def extract(self, record):
        return record.get("LOGR_DEST")
