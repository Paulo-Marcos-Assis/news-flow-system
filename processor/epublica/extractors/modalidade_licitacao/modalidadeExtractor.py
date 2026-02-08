from ..base_extractor import BaseExtractor

class ModalidadeLicitacaoExtractor(BaseExtractor):
    field_name = "descricao"
    scope = "modalidade_licitacao"

    MODALIDADE_MAP = {
        "Inexigibilidade": "Inexigibilidade de Licitação",
        "Dispensa": "Dispensa de Licitação",
        "Pregão": "Pregão Eletrônico"
    }

    def extract(self, record):
        message = record.get("licitacao", {}).get("modalidade")
        
        return self.MODALIDADE_MAP.get(message, message)