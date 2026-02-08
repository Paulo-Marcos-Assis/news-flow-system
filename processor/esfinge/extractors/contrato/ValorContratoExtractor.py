from ..base_extractor import BaseExtractor

class ValorContratoExtractor(BaseExtractor):
    field_name = "valor_contrato"
    scope = "contrato"

    def extract(self, record):
        contrato_data = record.get('contrato', {})
        return contrato_data.get('valor_contrato')
