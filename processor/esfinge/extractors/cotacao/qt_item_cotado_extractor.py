from ..base_extractor import BaseExtractor

class QtItemCotadoExtractor(BaseExtractor):
    field_name = "qt_item_cotado"
    scope = "cotacao"

    def extract(self, record):
        cotacao_data = record.get('cotacao', {})
        return cotacao_data.get('qtd_item_cotado')
