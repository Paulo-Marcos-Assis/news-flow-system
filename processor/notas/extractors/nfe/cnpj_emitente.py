from ..base_extractor import BaseExtractor

class CnpjEmitenteExtractor(BaseExtractor):
    field_name = "cnpj_emitente"
    scope = "nfe"

    def extract(self, record):
        return record.get("CNPJ_EMITENTE")
