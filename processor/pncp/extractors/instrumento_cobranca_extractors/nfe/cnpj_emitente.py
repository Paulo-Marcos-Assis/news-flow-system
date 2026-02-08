from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class CnpjEmitenteExtractor(BaseExtractor):
    field_name = "cnpj_emitente"

    def extract(self, record):
        return record.get("notaFiscalEletronica", {}).get("niEmitente", DEFAULT_VALUE)
