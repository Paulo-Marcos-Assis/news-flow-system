from verifiers.base_verifier import BaseVerifier

class ProcessoNumeroProcessoLicitatorioVerifier(BaseVerifier):
    """Verifier for the 'situacao' destination field."""
    destination_field = "numero_processo_licitatorio"
    destination_table = "processo_licitatorio"

    def verify(self, data):
        value = data.get(self.destination_table, {}).get(self.destination_field, None)
        if value is None:
            return True, None
        if not isinstance(value, str):
            return False, f"Field '{self.destination_field}' must be a string, but got {type(value).__name__}."
        
        return True, None