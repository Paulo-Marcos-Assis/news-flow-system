from ..base_verifier import BaseVerifier
class NcmProdutoVerifier(BaseVerifier):
    scope = "item"
    field_name = "ncm_produto"

    def verify(self, record):
        if not record:
            return True, None
        
        # força string e remove espaços/quebras
        record = str(record).strip()
        
        if not record or len(record) != 8:
            return False, "Código NCM com numero invalido de digitos"
        return True, None
