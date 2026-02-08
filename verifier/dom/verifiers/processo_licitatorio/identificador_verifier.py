from ..base_verifier import BaseVerifier

class IdentificadorVerifier(BaseVerifier):

    verification_name = "identificador"

    def verify(self, record):

        numero_processo = record['extracted']['processo_licitatorio']['numero_processo_licitatorio']
        numero_edital = record['extracted']['processo_licitatorio']['numero_edital']

        if not numero_processo and not numero_edital:
            return False, "Não foi possível extrair um identificador para o documento."

        return True, None