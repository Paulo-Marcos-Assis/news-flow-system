from verifiers.base_verifier import BaseVerifier

class ProcessoValorTotalPrevistoVerifier(BaseVerifier):
    """Verifier for the 'valor_total_previsto' destination field."""
    destination_field = "valor_total_previsto"
    destination_table = "processo_licitatorio"

    def verify(self, data):
        value = data.get(self.destination_table, {}).get(self.destination_field, None)
        if value is None:
            return True, None
        if not isinstance(value, (float, int)):
            return False, f"Field '{self.destination_field}' must be a number, but got {type(value).__name__}."
        
        if value < 0:
            return False, f"Field '{self.destination_field}' must be non-negative."

        return True, None
