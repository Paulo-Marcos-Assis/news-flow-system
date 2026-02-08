from verifiers.base_verifier import BaseVerifier

class ProcessoDescricaoObjetoVerifier(BaseVerifier):
    """Verifier for the 'descricao_objeto' destination field."""
    destination_field = "descricao_objeto"
    destination_table = "processo_licitatorio"

    def verify(self, data):
        value = data.get(self.destination_table, {}).get(self.destination_field, None)
        if value is None:
            return True, None
        if not isinstance(value, str):
            return False, f"Field '{self.destination_field}' must be a string, but got {type(value).__name__}."
        
        return True, None
