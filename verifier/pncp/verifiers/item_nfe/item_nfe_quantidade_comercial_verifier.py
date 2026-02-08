from verifiers.base_verifier import BaseVerifier

class ItemNfeQuantidadeComercialVerifier(BaseVerifier):
    """Verifier for the 'quantidade_comercial' field in the 'item_nfe' table."""
    destination_field = "quantidade_comercial"
    destination_table = "item_nfe"

    def verify(self, data):
        item_list = data.get(self.destination_table, [])
        if not item_list:
            return True, None

        for i, item in enumerate(item_list):
            value = item.get(self.destination_field, None)
            if value is not None and not isinstance(value, (int, float)):
                return False, f"In item_nfe at index {i}, field '{self.destination_field}' must be a number, but got {type(value).__name__}."
        
        return True, None
