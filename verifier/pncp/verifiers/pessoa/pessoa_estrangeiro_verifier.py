from verifiers.base_verifier import BaseVerifier

class PessoaEstrangeiroVerifier(BaseVerifier):
    """Verifier for the 'estrangeiro' field in the 'pessoa' table."""
    destination_field = "estrangeiro"
    destination_table = "pessoa"

    def verify(self, data):
        value = data.get(self.destination_table, {}).get(self.destination_field, None)
        
        if value is None:
            return True, None

        if not isinstance(value, bool):
            return False, f"Field '{self.destination_field}' in table '{self.destination_table}' must be a boolean, but got {type(value).__name__}."
        
        return True, None
