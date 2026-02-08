from ..base_verifier import BaseVerifier

class DataPublicacaoDomVerifier(BaseVerifier):
    verification_name = "data_publicacao_dom"

    def verify(self, record):
        if record['extracted']['documento']['data_emissao'] is None:
            return False, "O campo Data Publicação DOM não foi extraído do registro original."
        if record['extracted']['documento']['data_emissao'] != record["raw"]["data"]:
            return False, f"O valor extraído da Data Publicação DOM ({record['extracted']['documento']['data_emissao']}) está diferente do campo no registro original ({record['raw']['data']})."

        return True, None