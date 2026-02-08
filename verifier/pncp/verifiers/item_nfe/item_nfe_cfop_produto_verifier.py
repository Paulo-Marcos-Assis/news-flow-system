from verifiers.base_verifier import BaseVerifier

class ItemNfeCfopProdutoVerifier(BaseVerifier):
    """Verifier for the 'cfop_produto' field in the 'item_nfe' table."""
    destination_field = "cfop_produto"
    destination_table = "item_nfe"

    def verify(self, data):
        # This field can appear in a list of items
        item_list = data.get(self.destination_table, [])
        if not item_list:
            return True, None

        for i, item in enumerate(item_list):
            value = item.get(self.destination_field, None)
            
            if value is None:
                continue

            if not isinstance(value, (str, int)):
                return False, f"In item_nfe at index {i}, field '{self.destination_field}' must be a string or integer, but got {type(value).__name__}."
        
        return True, None
