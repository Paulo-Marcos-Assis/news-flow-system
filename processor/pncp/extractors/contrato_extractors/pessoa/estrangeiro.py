from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class EstrangeiroExtractor(BaseExtractor):
    field_name = "estrangeiro"
    
    def extract(self, record):
        tipo_pessoa = record.get("tipoPessoa",DEFAULT_VALUE)
        if tipo_pessoa == "PE":
            return True
        elif tipo_pessoa == "PF" or tipo_pessoa == "PJ":
            return False
        else:
            return DEFAULT_VALUE
