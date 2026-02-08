from ..base_extractor import BaseExtractor

class UfEmitenteExtractor(BaseExtractor):
    field_name = "uf_emitente"
    scope = "nfe"

    def extract(self, record):
        return record.get("UF_EMITENTE")
