from ..base_verifier import BaseVerifier

class UnidadeGestoraVerifier(BaseVerifier):
    verification_name = "nome_ug"

    def verify(self, record):
        if record['extracted']['unidade_gestora']['nome_ug'] is None:
            return False, "O campo Unidade Gestora não foi extraído do registro original."
        if record['extracted']['unidade_gestora']['nome_ug'] != record["raw"]["entidade"]:
            return False, f"O valor extraído da Unidade Gestora ({record['extracted']['unidade_gestora']['nome_ug']}) está diferente do campo no registro original ({record['raw']['entidade']})."

        return True, None