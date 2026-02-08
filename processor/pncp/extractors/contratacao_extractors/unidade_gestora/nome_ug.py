from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class NomeUgExtractor(BaseExtractor):
    field_name = "nome_ug"

    def extract(self, record):
        return record.get("orgaoEntidade", {}).get("razaoSocial", DEFAULT_VALUE)