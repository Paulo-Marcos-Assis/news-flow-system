from ..base_extractor import BaseExtractor

class ChaveAcessoExtractor(BaseExtractor):
    field_name = "chave_acesso"
    scope = "nfe"

    def extract(self, record):
        chave = record.get("CHAVE_ACESSO")
        
        # Garante que, se a chave existir, ela seja retornada como uma string.
        # Se for nula ou não existir, retorna None.
        if chave is not None:
            return str(chave)
            
        return None