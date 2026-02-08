from verifiers.base_verifier import BaseVerifier

class ContratoValorContratoVerifier(BaseVerifier):
    """Verifier for the 'valor_contrato' field in the 'contrato' table."""
    destination_field = "valor_contrato"
    destination_table = "contrato"

    def verify(self, data):
        value = data.get(self.destination_table, {}).get(self.destination_field, None)
        
        # Allow None values
        if value is None:
            return True, None

        if not isinstance(value, (int, float)):
            return False, f"Field '{self.destination_field}' in table '{self.destination_table}' must be a number, but got {type(value).__name__}."
        
        return True, None
