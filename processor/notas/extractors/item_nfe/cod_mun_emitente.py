from ..base_extractor import BaseExtractor

class CodMunEmitenteExtractor(BaseExtractor):
    field_name = "cod_mun_emitente"
    scope = "item"

    def extract(self, record):
        return record.get("COD_MUNICIPIO_ORIGEM")
