from verifiers.base_verifier import BaseVerifier

class NfeDataEmissaoVerifier(BaseVerifier):
    """Verifier for the 'data_emissao' field in the 'nfe' table."""
    destination_field = "data_emissao"
    destination_table = "nfe"

    def verify(self, data):
        value = data.get(self.destination_table, {}).get(self.destination_field, None)
        
        if value is None:
            return True, None

        if not isinstance(value, str):
            return False, f"Field '{self.destination_field}' in table '{self.destination_table}' must be a string, but got {type(value).__name__}."
        
        return True, None
