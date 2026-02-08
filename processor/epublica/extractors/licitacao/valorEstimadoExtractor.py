from ..base_extractor import BaseExtractor

class ValorEstimadoExtractor(BaseExtractor):
    field_name = "valor_estimado_item"
    scope = "item_licitacao"

    def extract(self, record):
        return record.get("licitacao", {}).get("valorEstimado")
        # try:
        #     # Garante que o valor seja um float, ou None se não for possível converter
        #     #return float(value) if value is not None else None
             
        # except (ValueError, TypeError):
        #     return None