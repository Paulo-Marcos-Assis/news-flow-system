from ..base_nested_extractor import BaseNestedExtractor


class ConvenioNestedExtractor(BaseNestedExtractor):
    field_name = "convenio"
    scope = "unidade_gestora"
    nested_key = "convenio"
    nested_scope = "convenio"
