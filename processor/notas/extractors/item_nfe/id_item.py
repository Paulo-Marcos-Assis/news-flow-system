from ..base_extractor import BaseExtractor

class IdItemExtractor(BaseExtractor):
    field_name = "id_item"
    scope = "item"

    def extract(self, record):
        return record.get("ITEM_ID")
