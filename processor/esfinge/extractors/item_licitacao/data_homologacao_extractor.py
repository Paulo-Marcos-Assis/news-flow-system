from ..base_extractor import BaseExtractor

class DataHomologacaoExtractor(BaseExtractor):
    field_name = "data_homologacao"
    scope = "item_licitacao"

    def extract(self, record):
        item_licitacao_data = record.get('item_licitacao', {})
        return item_licitacao_data.get('data_homologacao_item')

