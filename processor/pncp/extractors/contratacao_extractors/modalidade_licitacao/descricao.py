from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class DescricaoExtractor(BaseExtractor):
    field_name = "descricao"

    def extract(self, record):
        modalidade_nome = record.get("modalidadeNome", DEFAULT_VALUE)
        
        if modalidade_nome == "Inexigibilidade":
            return "Inexigibilidade de Licitacao"
        elif modalidade_nome == "Dispensa":
            return "Dispensa de Licitacao"
        else:
            return modalidade_nome