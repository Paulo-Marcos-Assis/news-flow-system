from verifiers.base_verifier import BaseVerifier

class LiquidacaoValorLiquidacaoVerifier(BaseVerifier):
    """Verifier for the 'valor_liquidacao' field in the 'liquidacao' table."""
    destination_field = "valor_liquidacao"
    destination_table = "liquidacao"

    def verify(self, data):
        value = data.get(self.destination_table, {}).get(self.destination_field, None)
        
        if value is None:
            return True, None

        if not isinstance(value, (int, float)):
            return False, f"Field '{self.destination_field}' in table '{self.destination_table}' must be a number, but got {type(value).__name__}."
        
        return True, None
