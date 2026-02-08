from ..base_extractor import BaseExtractor

class ValorTotalPrevistoExtractor(BaseExtractor):
    field_name = "valor_total_previsto"
    scope = "processo_licitatorio"

    def extract(self, record):
        processo_licitatorio_data = record.get('processo_licitatorio', {})
        return processo_licitatorio_data.get('valor_total_previsto')
