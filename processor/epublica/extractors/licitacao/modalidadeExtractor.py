from ..base_extractor import BaseExtractor

class ModalidadeLicitacaoExtractor(BaseExtractor):
    field_name = "descricao"
    scope = "modalidade_licitacao"

    def extract(self, record):
        return record.get("licitacao", {}).get("modalidade")