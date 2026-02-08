from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class DescricaoProdutoExtractor(BaseExtractor):
    field_name = "descricao_produto"

    def extract(self, item):
        return item.get("descricaoProdutoServico", DEFAULT_VALUE)
