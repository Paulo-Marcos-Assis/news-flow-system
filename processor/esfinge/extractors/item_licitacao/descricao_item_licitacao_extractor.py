from ..base_extractor import BaseExtractor

class DescricaoItemLicitacaoExtractor(BaseExtractor):
    field_name = "descricao_item_licitacao"
    scope = "item_licitacao"

    def extract(self, record):
        item_licitacao_data = record.get('item_licitacao', {})
        return item_licitacao_data.get('descricao_item_licitacao')

