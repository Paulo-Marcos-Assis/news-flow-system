from ..base_extractor import BaseExtractor


class DataLiquidacaoExtractor(BaseExtractor):
    field_name = "data_liquidacao"
    scope = "liquidacao"

    def extract(self, record):
        liquidacao_data = record.get('liquidacao', {})
        return liquidacao_data.get('data_liquidacao')
