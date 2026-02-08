from ..base_extractor import BaseExtractor


class IdSubempenhoLiquidacaoExtractor(BaseExtractor):
    field_name = "id_subempenho_liquidacao"
    scope = "liquidacao"

    def extract(self, record):
        liquidacao_data = record.get('liquidacao', {})
        return liquidacao_data.get('id_subempenho_liquidacao')
