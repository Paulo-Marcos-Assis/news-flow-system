from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class SiglaUfExtractor(BaseExtractor):
    field_name = "sigla_uf"

    def extract(self, record):
        return record.get("unidadeOrgao", {}).get("ufSigla", DEFAULT_VALUE)
