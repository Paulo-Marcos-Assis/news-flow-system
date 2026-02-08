from ..base_extractor import BaseExtractor


class ValorLiquidacaoExtractor(BaseExtractor):
    field_name = "valor_liquidacao"
    scope = "liquidacao"

    def extract(self, record):
        liquidacao_data = record.get('liquidacao', {})
        return liquidacao_data.get('valor_liquidacao')
