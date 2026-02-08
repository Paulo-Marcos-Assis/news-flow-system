from ..base_extractor import BaseExtractor

class DataVencimentoExtractor(BaseExtractor):
    field_name = "data_vencimento"
    scope = "contrato"

    def extract(self, record):
        contrato_data = record.get('contrato', {})
        return contrato_data.get('data_vencimento')
