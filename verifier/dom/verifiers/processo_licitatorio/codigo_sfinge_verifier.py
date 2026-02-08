from ..base_verifier import BaseVerifier

class CodigoEsfingeVerifier(BaseVerifier):
    verification_name = "codigo_sfinge"

    def verify(self, record):
        if record['extracted']['processo_licitatorio']['codigo_sfinge'] != record["raw"]["cod_registro_info_sfinge"]:
            return False, f"O valor extraído do Código eSfinge ({record['extracted']['processo_licitatorio']['codigo_sfinge']}) está diferente do campo no registro original ({record['raw']['cod_registro_info_sfinge']})."

        return True, None