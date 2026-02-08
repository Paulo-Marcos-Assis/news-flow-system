from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class DescricaoObjetivoExtractor(BaseExtractor):
    field_name = "descricao_objetivo"

    def extract(self, record):
        return record.get("objetoContrato", DEFAULT_VALUE)
