from ..base_nested_extractor import BaseNestedExtractor


class TipoLicitacaoNestedExtractor(BaseNestedExtractor):
    field_name = "tipo_licitacao"
    scope = "processo_licitatorio"
    nested_key = "tipo_licitacao"
    nested_scope = "tipo_licitacao"
