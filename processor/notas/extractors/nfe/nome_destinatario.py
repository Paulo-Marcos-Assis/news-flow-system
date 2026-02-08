from ..base_extractor import BaseExtractor

class NomeDestinatarioExtractor(BaseExtractor):
    field_name = "nome_destinatario"
    scope = "nfe"

    def extract(self, record):
        return record.get("NOME_DESTINATARIO")
