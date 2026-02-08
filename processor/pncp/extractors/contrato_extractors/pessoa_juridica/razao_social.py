from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class RazaoSocialExtractor(BaseExtractor):
    field_name = "razao_social"

    def extract(self, record):
        tipo_pessoa = record.get("tipoPessoa",DEFAULT_VALUE)
        if tipo_pessoa == "PJ":
            return record.get("nomeRazaoSocialFornecedor",DEFAULT_VALUE)
        else: 
            return DEFAULT_VALUE
