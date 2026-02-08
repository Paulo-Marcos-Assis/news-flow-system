from ...base_extractor import BaseExtractor, DEFAULT_VALUE
import unicodedata

class EnteExtractor(BaseExtractor):
    field_name = "ente"

    def extract(self, record):
        razao_social_orgao_entidade = record.get("orgaoEntidade", {}).get("razaoSocial", DEFAULT_VALUE)
        normalized_razao_social_orgao_entidade = unicodedata.normalize("NFKD", razao_social_orgao_entidade).encode("ASCII", "ignore").decode().upper()
        
        if "CONSORCIO" in normalized_razao_social_orgao_entidade:
            return razao_social_orgao_entidade
        else:
            return record.get("unidadeOrgao", {}).get("municipioNome", DEFAULT_VALUE)