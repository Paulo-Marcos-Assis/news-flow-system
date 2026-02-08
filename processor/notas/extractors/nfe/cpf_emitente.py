from ..base_extractor import BaseExtractor

class CpfEmitenteExtractor(BaseExtractor):
    field_name = "cpf_emitente"
    scope = "nfe"

    def extract(self, record):
        return record.get("CPF_EMITENTE")
