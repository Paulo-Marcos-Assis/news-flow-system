from ..base_extractor import BaseExtractor

class NumeroLicitacaoExtractor(BaseExtractor):
    field_name = "numero_processo_licitatorio"
    scope = "processo_licitatorio"

    def extract(self, record):
        return record.get("licitacao", {}).get("numero")