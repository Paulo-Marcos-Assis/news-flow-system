from ..base_extractor import BaseExtractor

class NumeroSerieNfeExtractor(BaseExtractor):
    field_name = "num_serie_nfe"
    scope = "nfe"

    def extract(self, record):
        return record.get("NUM_SERIE_NFE")
