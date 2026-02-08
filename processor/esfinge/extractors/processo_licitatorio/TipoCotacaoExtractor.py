from ..base_nested_extractor import BaseNestedExtractor


class TipoCotacaoNestedExtractor(BaseNestedExtractor):
    field_name = "tipo_cotacao"
    scope = "processo_licitatorio"
    nested_key = "tipo_cotacao"
    nested_scope = "tipo_cotacao"
