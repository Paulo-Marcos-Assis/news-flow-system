from ..base_extractor import BaseExtractor

class TipoOperacaoExtractor(BaseExtractor):
    field_name = "tipo_operacao"
    scope = "nfe"

    def extract(self, record):
        return record.get("TIPO_OPERACAO")
