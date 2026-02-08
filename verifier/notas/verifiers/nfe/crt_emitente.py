from ..base_verifier import BaseVerifier
class CrtEmitenteVerifier(BaseVerifier):
    scope = "nfe"
    field_name = "crt_emitente"

    def verify(self, record):
        # Se for None ou uma string vazia/com espaços, considera válido e encerra.
        if record is None or str(record).strip() == "":
            return True, None
        
        try:
            # Tenta converter para float primeiro para lidar com casos como "1.0"
            # e depois para int para remover as casas decimais.
            record_int = int(float(record))
            if record_int < 1 or record_int > 4:
                return False, "Número de crt não cadastrado"
            return True, None
        except (ValueError, TypeError):
            # Captura erros de conversão para int ou float
            return False, f"Valor '{record}' não é um número inteiro válido para CRT."