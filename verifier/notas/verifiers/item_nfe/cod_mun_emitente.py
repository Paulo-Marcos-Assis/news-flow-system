from ..base_verifier import BaseVerifier
class CodMunEmitenteVerifier(BaseVerifier):
    scope = "item"
    field_name = "cod_mun_emitente"

    def verify(self, record):
        if not record:
            return True, None

        # força string e remove espaços/quebras
        record = str(record).strip()

        # Codigo esperado no formato XXXXXXX.00 → 10 caracteres
        if len(record) != 7:
            return False, "Código do municipio emitente com numero invalido de digitos"

        return True, None







