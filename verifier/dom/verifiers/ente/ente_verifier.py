from ..base_verifier import BaseVerifier

class EnteVerifier(BaseVerifier):
    verification_name = "ente"

    def verify(self, record):
        if record['extracted']['ente']['ente'] != record["raw"]["municipio"]:
            return False, f"O valor extraído do Ente ({record['extracted']['ente']['ente']}) está diferente do campo no registro original ({record['raw']['municipio']})."

        return True, None