from ..base_extractor import BaseExtractor

class ObjetoResumidoExtractor(BaseExtractor):
    field_name = "descricao_objeto"
    scope = "processo_licitatorio"

    def extract(self, record):
        return record.get("licitacao", {}).get("objetoResumido")