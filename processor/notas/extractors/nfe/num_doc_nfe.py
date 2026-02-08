from ..base_extractor import BaseExtractor

class NumeroDocNfeExtractor(BaseExtractor):
    field_name = "num_doc_nfe"
    scope = "nfe"

    def extract(self, record):
        return record.get("NUM_DOC_NFE")
