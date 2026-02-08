from ..base_extractor import BaseExtractor

class QtdItemLicitacaoExtractor(BaseExtractor):
    field_name = "qtd_item_licitacao"
    scope = "item_licitacao"

    def extract(self, record):
        item_licitacao_data = record.get('item_licitacao', {})
        return item_licitacao_data.get('qtd_item_licitado')

