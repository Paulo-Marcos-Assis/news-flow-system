from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class NomeDestinatarioExtractor(BaseExtractor):
    field_name = "nome_destinatario"

    def extract(self, record):
        return record.get("notaFiscalEletronica", {}).get("nomeOrgaoDestinatario", DEFAULT_VALUE)
