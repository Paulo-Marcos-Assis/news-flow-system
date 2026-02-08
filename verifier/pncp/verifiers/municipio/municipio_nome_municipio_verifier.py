from verifiers.base_verifier import BaseVerifier

class MunicipioNomeMunicipioVerifier(BaseVerifier):
    """Verifier for the 'nome_municipio' destination field in 'municipio' table."""
    destination_field = "nome_municipio"
    destination_table = "municipio"

    def verify(self, data):
        value = data.get(self.destination_table, {}).get(self.destination_field, None)
        if value is None:
            return True, None
        if not isinstance(value, str):
            return False, f"Field '{self.destination_field}' must be a string, but got {type(value).__name__}."
        
        return True, None
