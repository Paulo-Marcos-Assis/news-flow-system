from ..base_nested_extractor import BaseNestedExtractor


class TipoObjetoLicitacaoNestedExtractor(BaseNestedExtractor):
    field_name = "tipo_objeto_licitacao"
    scope = "processo_licitatorio"
    nested_key = "tipo_objeto_licitacao"
    nested_scope = "tipo_objeto_licitacao"
