from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class NumeroProcessoLicitatorioExtractor(BaseExtractor):
    field_name = "numero_processo_licitatorio"

    def extract(self, record):
        return record.get("processo", DEFAULT_VALUE)