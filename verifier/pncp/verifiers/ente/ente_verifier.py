from verifiers.base_verifier import BaseVerifier

class EnteVerifier(BaseVerifier):
    """Verifier for the 'ente' destination field in 'ente' table."""
    destination_field = "ente"
    destination_table = "ente"

    def verify(self, data):
        value = data.get(self.destination_table, {}).get(self.destination_field, None)
        if value is None:
            return True, None
        if not isinstance(value, str):
            return False, f"Field '{self.destination_field}' must be a string, but got {type(value).__name__}."
        
        return True, None
