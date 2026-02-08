from ..base_nested_extractor import BaseNestedExtractor


class ModalidadeLicitacaoNestedExtractor(BaseNestedExtractor):
    field_name = "modalidade_licitacao"
    scope = "processo_licitatorio"
    nested_key = "modalidade_licitacao"
    nested_scope = "modalidade_licitacao"
