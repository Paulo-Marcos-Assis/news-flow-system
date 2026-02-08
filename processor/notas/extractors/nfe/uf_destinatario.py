from ..base_extractor import BaseExtractor

class UfDestinatarioExtractor(BaseExtractor):
    field_name = "uf_destinatario"
    scope = "nfe"

    def extract(self, record):
        return record.get("UF_DESTINATARIO")
