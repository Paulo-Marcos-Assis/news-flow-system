from ..base_extractor import BaseExtractor

class ValorCotadoExtractor(BaseExtractor):
    field_name = "valor_cotado"
    scope = "cotacao"

    def extract(self, record):
        cotacao_data = record.get('cotacao', {})
        return cotacao_data.get('valor_total_cotado_item')

