from ..base_extractor import BaseExtractor

class CodPaisDestinatarioExtractor(BaseExtractor):
    field_name = "cod_pais_destinatario"
    scope = "nfe"

    def extract(self, record):
        return record.get("COD_PAIS_DESTINATARIO")
