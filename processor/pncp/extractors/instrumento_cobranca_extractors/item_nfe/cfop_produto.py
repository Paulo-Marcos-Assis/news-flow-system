from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class CfopProdutoExtractor(BaseExtractor):
    field_name = "cfop_produto"

    def extract(self, item):
        return item.get("cfop", DEFAULT_VALUE)
