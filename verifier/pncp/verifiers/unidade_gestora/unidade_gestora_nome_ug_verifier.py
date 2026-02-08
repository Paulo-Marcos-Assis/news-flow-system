from verifiers.base_verifier import BaseVerifier

class UnidadeGestoraNomeUgVerifier(BaseVerifier):
    """Verifier for the 'nome_ug' destination field in 'unidade_gestora' table."""
    destination_field = "nome_ug"
    destination_table = "unidade_gestora"

    def verify(self, data):
        value = data.get(self.destination_table, {}).get(self.destination_field, None)
        if value is None:
            return True, None
        if not isinstance(value, str):
            return False, f"Field '{self.destination_field}' must be a string, but got {type(value).__name__}."
        
        return True, None
