from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class ValorTotalPrevistoExtractor(BaseExtractor):
    field_name = "valor_total_previsto"

    def extract(self, record):
        return record.get("valorTotalEstimado", DEFAULT_VALUE)
