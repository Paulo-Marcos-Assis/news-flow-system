from ..base_extractor import BaseExtractor

class NumeroSequencialItemExtractor(BaseExtractor):
    field_name = "numero_sequencial_item"
    scope = "item_licitacao"

    def extract(self, record):
        item_licitacao_data = record.get('item_licitacao', {})
        return item_licitacao_data.get('nro_sequencial_item')

