from verifiers.base_verifier import BaseVerifier

class UnidadeGestoraCnpjVerifier(BaseVerifier):
    """Verifier for the 'cnpj' destination field in 'unidade_gestora' table."""
    destination_field = "cnpj"
    destination_table = "unidade_gestora"

    def verify(self, data):
        value = data.get(self.destination_table, {}).get(self.destination_field, None)
        if value is None:
            return True, None
        if not isinstance(value, str):
            return False, f"Field '{self.destination_field}' must be a string, but got {type(value).__name__}."
        
        return True, None
