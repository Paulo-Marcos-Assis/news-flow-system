from ..base_extractor import BaseExtractor

class NomeFantEmitenteExtractor(BaseExtractor):
    field_name = "nome_fant_emitente"
    scope = "nfe"

    def extract(self, record):
        return record.get("NOME_FANT_EMITENTE")
