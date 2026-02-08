from ..base_extractor import BaseExtractor

class CepEmitenteExtractor(BaseExtractor):
    field_name = "cep_emitente"
    scope = "nfe"

    def extract(self, record):
        return record.get("CEP_EMITENTE")
