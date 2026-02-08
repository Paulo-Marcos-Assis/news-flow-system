from ..base_verifier import BaseVerifier

class CodigoDomVerifier(BaseVerifier):
    verification_name = "codigo_dom"

    def verify(self, record):
        if record['extracted']['documento']['codigo_documento'] is None:
            return False, "O campo Código DOM não foi extraído do registro original."
        if record['extracted']['documento']['codigo_documento'] != record["raw"]["codigo"]:
            return False, f"O valor extraído do Código DOM ({record['extracted']['documento']['codigo_documento']}) está diferente do campo no registro original ({record['raw']['codigo']})."

        return True, None