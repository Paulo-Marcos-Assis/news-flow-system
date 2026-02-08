from ..base_extractor import BaseExtractor

class NomeMunDestinatarioExtractor(BaseExtractor):
    field_name = "nome_mun_destinatario"
    scope = "nfe"

    def extract(self, record):
        return record.get("NOME_MUN_DESTINATARIO")
