from ..base_extractor import BaseExtractor

class CpfDestinatarioExtractor(BaseExtractor):
    field_name = "cpf_destinatario"
    scope = "nfe"

    def extract(self, record):
        return record.get("CPF__DESTINATARIO")
