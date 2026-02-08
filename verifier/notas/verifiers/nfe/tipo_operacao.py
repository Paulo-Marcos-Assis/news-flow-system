from ..base_verifier import BaseVerifier
class TipoOperacaoVerifier(BaseVerifier):
    scope = "nfe"
    field_name = "tipo_operacao"
    
    def verify(self, record):
        if not record and record != "": # Permite que string vazia seja validada abaixo
            return True, None
            
        # Força string e remove espaços/quebras
        record = str(record).strip()

        # Lista de valores permitidos
        valores_permitidos = ['S', 's', 'E', 'e', '']

        # Verifica se o valor NÃO ESTÁ na lista de permitidos
        if record not in valores_permitidos:
            return False, "Tipo de operação não cadastrada"
            
        # Se chegou até aqui, o valor é válido
        return True, None