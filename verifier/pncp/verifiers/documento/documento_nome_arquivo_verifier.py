from verifiers.base_verifier import BaseVerifier

class DocumentoNomeArquivoVerifier(BaseVerifier):
    """Verifier for the 'nome_arquivo' field in the 'documento' table."""
    destination_field = "nome_arquivo"
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

            if not isinstance(value, str):
                return False, f"In document at index {i}, field '{self.destination_field}' must be a string, but got {type(value).__name__}."
        
        return True, None
