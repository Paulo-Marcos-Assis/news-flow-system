from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class CnpjExtractor(BaseExtractor):
    field_name = "cnpj"

    def extract(self, record):
        tipo_pessoa = record.get("tipoPessoa",DEFAULT_VALUE)
        if tipo_pessoa == "PJ":
            return record.get("niFornecedor",DEFAULT_VALUE)
        else: 
            return DEFAULT_VALUE 
