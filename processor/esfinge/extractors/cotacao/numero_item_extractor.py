from ..base_extractor import BaseExtractor

class NumeroItemCotacaoExtractor(BaseExtractor):
    field_name = "numero_item"
    scope = "cotacao"

    def extract(self, record):
        cotacao_data = record.get('cotacao', {})
        return cotacao_data.get('numero_item')
