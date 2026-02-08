from ..base_extractor import BaseExtractor

class DataAssinaturaExtractor(BaseExtractor):
    field_name = "data_assinatura"
    scope = "contrato"

    def extract(self, record):
        contrato_data = record.get('contrato', {})
        return contrato_data.get('data_assinatura')
