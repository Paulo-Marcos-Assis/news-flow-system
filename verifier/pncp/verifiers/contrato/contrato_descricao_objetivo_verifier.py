from verifiers.base_verifier import BaseVerifier

class ContratoDescricaoObjetivoVerifier(BaseVerifier):
    """Verifier for the 'descricao_objetivo' field in the 'contrato' table."""
    destination_field = "descricao_objetivo"
    destination_table = "contrato"

    def verify(self, data):
        value = data.get(self.destination_table, {}).get(self.destination_field, None)
        
        # Allow None values
        if value is None:
            return True, None

        if not isinstance(value, str):
            return False, f"Field '{self.destination_field}' in table '{self.destination_table}' must be a string, but got {type(value).__name__}."
        
        return True, None
