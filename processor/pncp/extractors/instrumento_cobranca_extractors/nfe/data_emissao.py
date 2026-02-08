from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class DataEmissaoExtractor(BaseExtractor):
    field_name = "data_emissao"

    def extract(self, record):
        return record.get("notaFiscalEletronica", {}).get("dataEmissao", DEFAULT_VALUE)
