from ..base_extractor import BaseExtractor

class SituacaoNfeExtractor(BaseExtractor):
    field_name = "situacao_nfe"
    scope = "nfe"

    def extract(self, record):
        return record.get("SITUACAO_ID")
