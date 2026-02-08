from verifiers.base_verifier import BaseVerifier

class TipoDocumentoDescricaoVerifier(BaseVerifier):
    """Verifier for the 'descricao' field in the 'tipo_documento' table."""
    destination_field = "descricao"
    destination_table = "tipo_documento"

    def verify(self, data):
        value = data.get(self.destination_table, {}).get(self.destination_field, None)
        if value is None:
            return True, None
        if not isinstance(value, str):
            return False, f"Field '{self.destination_field}' must be a string, but got {type(value).__name__}."
        
        return True, None
