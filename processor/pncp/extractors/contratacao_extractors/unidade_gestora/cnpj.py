from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class CnpjExtractor(BaseExtractor):
    field_name = "cnpj"

    def extract(self, record):
        return record.get("orgaoEntidade", {}).get("cnpj", DEFAULT_VALUE)
