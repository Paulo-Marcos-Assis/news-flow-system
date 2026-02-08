from ..base_extractor import BaseExtractor

class DescricaoProdutoExtractor(BaseExtractor):
    field_name = "descricao_produto"
    scope = "item"

    def extract(self, record):
        return record.get("DESCRICAO_PRODUTO")
