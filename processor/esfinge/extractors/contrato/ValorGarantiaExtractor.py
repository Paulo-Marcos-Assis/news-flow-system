from ..base_extractor import BaseExtractor

class ValorGarantiaExtractor(BaseExtractor):
    field_name = "valor_garantia"
    scope = "contrato"

    def extract(self, record):
        contrato_data = record.get('contrato', {})
        return contrato_data.get('valor_garantia_execucao')
