from ..base_extractor import BaseExtractor

class DescricaoUnidadeMedidaExtractor(BaseExtractor):
    field_name = "descricao_unidade_medida"
    scope = "item_licitacao"

    def extract(self, record):
        item_licitacao_data = record.get('item_licitacao', {})
        return item_licitacao_data.get('descricao_unidade_medida')












