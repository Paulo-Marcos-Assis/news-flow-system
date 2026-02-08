from verifiers.base_verifier import BaseVerifier

class NfeCnpjEmitenteVerifier(BaseVerifier):
    """Verifier for the 'cnpj_emitente' field in the 'nfe' table."""
    destination_field = "cnpj_emitente"
    destination_table = "nfe"

    def verify(self, data):
        value = data.get(self.destination_table, {}).get(self.destination_field, None)
        
        if value is None:
            return True, None

        if not isinstance(value, str):
            return False, f"Field '{self.destination_field}' in table '{self.destination_table}' must be a string, but got {type(value).__name__}."
        
        return True, None
