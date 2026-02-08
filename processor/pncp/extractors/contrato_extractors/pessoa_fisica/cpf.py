from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class CpfExtractor(BaseExtractor):
    field_name = "cpf"
    
    def extract(self, record):
        tipo_pessoa = record.get("tipoPessoa",DEFAULT_VALUE)
        if tipo_pessoa == "PF":
            return record.get("niFornecedor",DEFAULT_VALUE)
        else: 
            return DEFAULT_VALUE 
