from ..base_extractor import BaseExtractor

class NomePaisEmitenteExtractor(BaseExtractor):
    field_name = "nome_pais_emitente"
    scope = "nfe"

    def extract(self, record):
        return record.get("NOME_PAIS_EMITENTE")
