from ..base_extractor import BaseExtractor, DEFAULT_VALUE

class DescricaoExtractor(BaseExtractor):
    field_name = "descricao"

    def extract(self, data):
        if data.get("tipoDocumentoNome", DEFAULT_VALUE) == "Outros Documentos":
            return "Outros Documentos do Processo"    
            
        return data.get("tipoDocumentoNome", DEFAULT_VALUE)