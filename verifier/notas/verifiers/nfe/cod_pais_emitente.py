from ..base_verifier import BaseVerifier
class CodPaisEmitenteVerifier(BaseVerifier):
    scope = "nfe"
    field_name = "cod_pais_emitente"

    def verify(self, record):
        if not record:
            return True, None

        # força string e remove espaços/quebras
        record = str(record).strip()

        # Codigo esperado no formato XXXXXXX.00 → 7 caracteres
        if len(record) != 4:
            return False, "Código de pais emitente com numero invalido de digitos"

        return True, None







