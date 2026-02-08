from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class NomeEmitenteExtractor(BaseExtractor):
    field_name = "nome_emitente"

    def extract(self, record):
        return record.get("notaFiscalEletronica", {}).get("nomeEmitente", DEFAULT_VALUE)
