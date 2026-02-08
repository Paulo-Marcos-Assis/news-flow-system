from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class UfNomeExtractor(BaseExtractor):
    field_name = "nome_uf"

    def extract(self, record):
        return record.get("unidadeOrgao", {}).get("ufNome", DEFAULT_VALUE)
