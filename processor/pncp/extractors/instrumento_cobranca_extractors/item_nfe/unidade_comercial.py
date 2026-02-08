from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class UnidadeComercialExtractor(BaseExtractor):
    field_name = "unidade_comercial"

    def extract(self, item):
        return item.get("unidade", DEFAULT_VALUE)
