from ..base_verifier import BaseVerifier
class FormaPgtoVerifier(BaseVerifier):
    scope = "nfe"
    field_name = "forma_pgto"

    def verify(self, record):
        # Se for None ou uma string vazia/com espaços, considera válido.
        if record is None or str(record).strip() == "":
            return True, None
            
        try:
            # Converte para float e depois para int
            record_int = int(float(record))
            if record_int < 0 or record_int > 2: # A sua regra original era de 1 a 3
                return False, "Forma de pagamento não cadastrada"
            return True, None
        except (ValueError, TypeError):
            return False, f"Valor '{record}' não é um número inteiro válido para Forma de Pagamento."