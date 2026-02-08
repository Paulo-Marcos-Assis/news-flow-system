from ..base_extractor import BaseExtractor

class TipoItemExtractor(BaseExtractor):
    field_name = "tipo_item"
    scope = "item_licitacao"

    def extract(self, record):
        item_licitacao_data = record.get('item_licitacao', {})
        return item_licitacao_data.get('tipo_item')

