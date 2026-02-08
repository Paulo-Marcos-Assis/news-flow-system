from ..base_extractor import BaseExtractor

class NomeMunEmitenteExtractor(BaseExtractor):
    field_name = "nome_mun_emitente"
    scope = "nfe"

    def extract(self, record):
        return record.get("NOME_MUN_EMITENTE")
