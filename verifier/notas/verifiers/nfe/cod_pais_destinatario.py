from ..base_verifier import BaseVerifier
class CodPaisDestinatarioVerifier(BaseVerifier):
    scope = "nfe"
    field_name = "cod_pais_destinatario"

    def verify(self, record):
        if not record:
            return True, None

        # força string e remove espaços/quebras
        record = str(record).strip()

        # Codigo esperado no formato XXXXXXX.00 → 7 caracteres
        if len(record) != 4:
            return False, "Código de pais destinatario com numero invalido de digitos"

        return True, None



