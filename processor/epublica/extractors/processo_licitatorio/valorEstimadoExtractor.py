from ..base_extractor import BaseExtractor

class ValorEstimadoExtractor(BaseExtractor):
    field_name = "valor_total_previsto"
    scope = "processo_licitatorio"

    def extract(self, record):
        return record.get("licitacao", {}).get("valorEstimado")