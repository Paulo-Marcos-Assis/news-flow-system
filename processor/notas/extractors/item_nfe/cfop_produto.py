from ..base_extractor import BaseExtractor

class CfopProdutoExtractor(BaseExtractor):
    field_name = "cfop_produto"
    scope = "item"

    def extract(self, record):
        return record.get("CFOP_PRODUTO")
