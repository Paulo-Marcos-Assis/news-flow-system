from ..base_extractor import BaseExtractor, DEFAULT_VALUE

class NomeArquivoExtractor(BaseExtractor):
    field_name = "nome_arquivo"

    def extract(self, data):
        return data.get("titulo", DEFAULT_VALUE)
