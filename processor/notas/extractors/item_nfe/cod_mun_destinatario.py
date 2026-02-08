from ..base_extractor import BaseExtractor

class CodMunDestinatarioExtractor(BaseExtractor):
    field_name = "cod_mun_destinatario"
    scope = "item"

    def extract(self, record):
        return record.get("COD_MUNICIPIO_DESTINO")
