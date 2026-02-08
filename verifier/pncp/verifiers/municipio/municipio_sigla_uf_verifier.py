from verifiers.base_verifier import BaseVerifier

class MunicipioSiglaUfVerifier(BaseVerifier):
    """Verifier for the 'sigla_uf' destination field in 'municipio' table."""
    destination_field = "sigla_uf"
    destination_table = "municipio"

    def verify(self, data):
        value = data.get(self.destination_table, {}).get(self.destination_field, None)
        if value is None:
            return True, None
        if not isinstance(value, str):
            return False, f"Field '{self.destination_field}' must be a string, but got {type(value).__name__}."
        
        return True, None
