from ..base_verifier import BaseVerifier
class CfopProdutoVerifier(BaseVerifier):
    field_name = "cfop"
    scope = "item"


    def verify(self, record):
        if not record:
            return True, None

        # força string e remove espaços/quebras
        record = str(record).strip()

        # Cfop esperado no formato XXXX.00 → 7 caracteres
        if len(record) != 4:
            return False, "Código Cfop com número inválido de dígitos"

        return True, None
