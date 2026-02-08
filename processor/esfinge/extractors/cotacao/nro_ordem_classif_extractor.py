from ..base_extractor import BaseExtractor

class OrdemClassifExtractor(BaseExtractor):
    field_name = "classificacao"
    scope = "cotacao"

    def extract(self, record):
        cotacao_data = record.get('cotacao', {})
        return cotacao_data.get('nro_ordem_classificacao')

