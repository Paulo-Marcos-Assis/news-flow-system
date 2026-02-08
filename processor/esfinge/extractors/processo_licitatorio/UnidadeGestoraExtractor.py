from ..base_nested_extractor import BaseNestedExtractor


class UnidadeGestoraNestedExtractor(BaseNestedExtractor):
    field_name = "unidade_gestora"
    scope = "ente"  # Changed from processo_licitatorio - now extracts from ente
    nested_key = "unidade_gestora"
    nested_scope = "unidade_gestora"
