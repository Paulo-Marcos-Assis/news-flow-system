from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class IdTemExtractor(BaseExtractor):
    field_name = "id_tem"

    def extract(self, item):
        try:
         return int(item.get("numeroItem", DEFAULT_VALUE))
        except (ValueError, TypeError):
         return DEFAULT_VALUE
