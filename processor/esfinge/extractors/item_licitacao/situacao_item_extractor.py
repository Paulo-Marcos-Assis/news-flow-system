from ..base_extractor import BaseExtractor

class SituacaoItemLicitacaoExtractor(BaseExtractor):
    field_name = "situacao_item"
    scope = "item_licitacao"

    def extract(self, record):
        item_licitacao_data = record.get('item_licitacao', {})
        return item_licitacao_data.get('situacao_item')

