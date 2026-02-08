from ..base_extractor import BaseExtractor

class NomePaisDestinatarioExtractor(BaseExtractor):
    field_name = "nome_pais_destinatario"
    scope = "nfe"

    def extract(self, record):
        return record.get("NOME_PAIS_DESTINATARIO")
