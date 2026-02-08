from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class NomeExtractor(BaseExtractor):
    field_name = "nome"

    def extract(self, record):
        return record.get("nomeRazaoSocialFornecedor",DEFAULT_VALUE)
 
   
