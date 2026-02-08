from verifiers.base_verifier import BaseVerifier

class DocumentoCodigoDocumentoVerifier(BaseVerifier):
    """Verifier for the 'codigo_documento' field in the 'documento' table."""
    destination_field = "codigo_documento"
    destination_table = "documento"

    def verify(self, data):
        document_list = data.get(self.destination_table, [])
        if not document_list:
            return True, None  # No documents to verify

        for i, doc in enumerate(document_list):
            value = doc.get(self.destination_field, None)
            
            # Allow None values
            if value is None:
                continue

            if not isinstance(value, int):
                return False, f"In document at index {i}, field '{self.destination_field}' must be an integer, but got {type(value).__name__}."
        
        return True, None
