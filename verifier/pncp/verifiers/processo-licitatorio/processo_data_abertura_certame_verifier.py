from verifiers.base_verifier import BaseVerifier

class ProcessoDataAberturaCertameVerifier(BaseVerifier):
    """Verifier for the 'data_abertura_certame' destination field."""
    destination_field = "data_abertura_certame"
    destination_table = "processo_licitatorio"

    def verify(self, data):
        value = data.get(self.destination_table, {}).get(self.destination_field, None)
        if value is None:
            return True, None
        if not isinstance(value, str):
            return False, f"Field '{self.destination_field}' must be a string, but got {type(value).__name__}."
        
        return True, None
