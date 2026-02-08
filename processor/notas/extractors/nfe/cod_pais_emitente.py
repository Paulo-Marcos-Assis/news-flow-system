from ..base_extractor import BaseExtractor

class CodPaisEmitenteExtractor(BaseExtractor):
    field_name = "cod_pais_emitente"
    scope = "nfe"

    def extract(self, record):
        return record.get("COD_PAIS_EMITENTE")
