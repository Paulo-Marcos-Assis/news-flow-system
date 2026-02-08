from ..base_extractor import BaseExtractor

class NcmProdutoExtractor(BaseExtractor):
    field_name = "ncm_produto"
    scope = "item"

    # to-do: Ver se precisa de mais algum tratamento
    def extract(self, record):
        return record.get("NCM_PRODUTO")
