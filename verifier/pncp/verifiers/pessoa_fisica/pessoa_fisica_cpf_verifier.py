from verifiers.base_verifier import BaseVerifier

class PessoaFisicaCpfVerifier(BaseVerifier):
    """Verifier for the 'cpf' field in the 'pessoa_fisica' table."""
    destination_field = "cpf"
    destination_table = "pessoa_fisica"

    def verify(self, data):
        value = data.get(self.destination_table, {}).get(self.destination_field, None)
        
        if value is None:
            return True, None

        if not isinstance(value, str):
            return False, f"Field '{self.destination_field}' in table '{self.destination_table}' must be a string, but got {type(value).__name__}."
        
        return True, None
