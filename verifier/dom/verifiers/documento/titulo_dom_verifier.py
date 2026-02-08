from ..base_verifier import BaseVerifier

class TituloVerifier(BaseVerifier):
    verification_name = "titulo"

    def verify(self, record):
        if record['extracted']['documento']['nome_arquivo'] is None:
            return False, "O campo Título não foi extraído do registro original."
        if record['extracted']['documento']['nome_arquivo'] != record["raw"]["nome_arquivo"]:
            return False, f"O valor extraído do Título ({record['extracted']['documento']['nome_arquivo']}) está diferente do campo no registro original ({record['raw']['titulo']})."

        return True, None