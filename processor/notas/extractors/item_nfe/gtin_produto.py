from ..base_extractor import BaseExtractor

class GtinProdutoExtractor(BaseExtractor):
    field_name = "gtin_produto"
    scope = "item"

    # to-do: Ver se precisa de mais algum tratamento
    def extract(self, record):
        gtin = record.get("GTIN_PRODUTO")

        # Garante que, se a gtin existir, ela seja retornada como uma string.
        # Se for nula ou não existir, retorna None.
        if gtin is not None:
            return str(gtin)
        return
