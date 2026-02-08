from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class DescricaoObjetoExtractor(BaseExtractor):
    field_name = "descricao_objeto"

    def extract(self, record):
        return record.get("objetoCompra", DEFAULT_VALUE)
