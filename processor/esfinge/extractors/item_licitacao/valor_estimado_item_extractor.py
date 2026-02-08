from ..base_extractor import BaseExtractor

class ValorEstimadoItemExtractor(BaseExtractor):
    field_name = "valor_estimado_item"
    scope = "item_licitacao"

    def extract(self, record):
        item_licitacao_data = record.get('item_licitacao', {})
        return item_licitacao_data.get('valor_estimado_item')
