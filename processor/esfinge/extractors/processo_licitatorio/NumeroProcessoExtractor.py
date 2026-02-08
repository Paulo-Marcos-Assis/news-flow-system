from ..base_extractor import BaseExtractor

class NumeroProcessoLicitatorioExtractor(BaseExtractor):
    field_name = "numero_processo_licitatorio"
    scope = "processo_licitatorio"

    def extract(self, record):
        processo_licitatorio_data = record.get('processo_licitatorio', {})
        return processo_licitatorio_data.get('numero_processo_licitatorio')
