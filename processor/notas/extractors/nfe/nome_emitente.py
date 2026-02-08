from ..base_extractor import BaseExtractor

class NomeEmitenteExtractor(BaseExtractor):
    field_name = "nome_emitente"
    scope = "nfe"

    def extract(self, record):
        return record.get("NOME_EMITENTE")
