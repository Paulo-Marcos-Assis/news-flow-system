from ..base_extractor import BaseExtractor


class NotaLiquidacaoExtractor(BaseExtractor):
    field_name = "nota_liquidacao"
    scope = "liquidacao"

    def extract(self, record):
        liquidacao_data = record.get('liquidacao', {})
        return liquidacao_data.get('nota_liquidacao')
