from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class NcmProdutoExtractor(BaseExtractor):
    field_name = "ncm_produto"

    def extract(self, item):
        return item.get("codigoNCM", DEFAULT_VALUE)
