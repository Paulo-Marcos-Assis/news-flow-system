from ..base_extractor import BaseExtractor

class NomeAdvogado(BaseExtractor):
    field_name = "nome"
    scope = "pessoa"

    def extract(self, record):
        return record.get("advogado", {}).get("pessoa", {}).get("nome") #LÓGICA advogado->pessoa->nome
        
