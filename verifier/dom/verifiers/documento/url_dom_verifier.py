from ..base_verifier import BaseVerifier

class UrlDomVerifier(BaseVerifier):
    verification_name = "url_dom"

    def verify(self, record):
        if record['extracted']['documento']['url_dom'] is None:
            return False, "O campo Url DOM não foi extraído do registro original."
        if record['extracted']['documento']['url_dom'] != record["raw"]["link"]:
            return False, f"O valor extraído da Url DOM ({record['extracted']['documento']['url_dom']}) está diferente do campo no registro original ({record['raw']['link']})."

        return True, None