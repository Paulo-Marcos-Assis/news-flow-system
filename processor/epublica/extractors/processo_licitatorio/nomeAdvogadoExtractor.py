from ..base_extractor import BaseExtractor
#campo ainda não modelado no estático, vai para o dinâmico
class NomeAdvogado(BaseExtractor):
    field_name = "responsavel_juridico"
    scope = "processo_licitatorio"

    def extract(self, record):
        return record.get("advogado", {}).get("pessoa", {}).get("nome")
