from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class SituacaoExtractor(BaseExtractor):
    field_name = "situacao"

    def extract(self, record):
        return record.get("situacaoCompraNome", DEFAULT_VALUE)
