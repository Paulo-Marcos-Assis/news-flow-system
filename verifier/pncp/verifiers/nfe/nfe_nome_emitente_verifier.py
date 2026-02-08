from verifiers.base_verifier import BaseVerifier

class NfeNomeEmitenteVerifier(BaseVerifier):
    """Verifier for the 'nome_emitente' field in the 'nfe' table."""
    destination_field = "nome_emitente"
    destination_table = "nfe"

    def verify(self, data):
        value = data.get(self.destination_table, {}).get(self.destination_field, None)
        
        if value is None:
            return True, None

        if not isinstance(value, str):
            return False, f"Field '{self.destination_field}' in table '{self.destination_table}' must be a string, but got {type(value).__name__}."
        
        return True, None
