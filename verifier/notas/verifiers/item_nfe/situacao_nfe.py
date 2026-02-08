from ..base_verifier import BaseVerifier
class SituacaoNfeVerifier(BaseVerifier):
    scope = "item"
    field_name = "situacao_nfe"

    def verify(self, record):
        if record is None:
            return True, None  # deixa passar o None
        try:
            record = int(record)
            if record < 1 or record > 11:
                return False, "Situacao de pagamento não cadastrada"
            return True, None
        except ValueError:
            return False, "Não foi possivel converter para int"
