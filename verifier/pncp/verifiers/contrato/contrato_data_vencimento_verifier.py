from verifiers.base_verifier import BaseVerifier

class ContratoDataVencimentoVerifier(BaseVerifier):
    """Verifier for the 'data_vencimento' field in the 'contrato' table."""
    destination_field = "data_vencimento"
    destination_table = "contrato"

    def verify(self, data):
        value = data.get(self.destination_table, {}).get(self.destination_field, None)
        
        # Allow None values
        if value is None:
            return True, None

        if not isinstance(value, str):
            return False, f"Field '{self.destination_field}' in table '{self.destination_table}' must be a string, but got {type(value).__name__}."
        
        return True, None
