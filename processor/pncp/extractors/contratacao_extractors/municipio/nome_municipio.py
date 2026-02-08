from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class NumeMunicipioExtractor(BaseExtractor):
    field_name = "nome_municipio"

    def extract(self, record):
        return record.get("unidadeOrgao", {}).get("municipioNome", DEFAULT_VALUE)
