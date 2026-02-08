from ..base_nested_extractor import BaseNestedExtractor


class EnteNestedExtractor(BaseNestedExtractor):
    field_name = "ente"
    scope = "processo_licitatorio"
    nested_key = "ente"
    nested_scope = "ente"
