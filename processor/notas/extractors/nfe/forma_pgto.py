from ..base_extractor import BaseExtractor

class FormaPgtoExtractor(BaseExtractor):
    field_name = "forma_pgto"
    scope = "nfe"

    def extract(self, record):
        return record.get("FORMA_PGTO")

