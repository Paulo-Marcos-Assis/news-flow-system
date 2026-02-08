from ..base_extractor import BaseExtractor

class LogradouroEmitenteExtractor(BaseExtractor):
    field_name = "logradouro_emitente"
    scope = "nfe"

    def extract(self, record):
        return record.get("LOGRADOURO_EMITENTE")
