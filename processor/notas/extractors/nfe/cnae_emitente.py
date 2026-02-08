from ..base_extractor import BaseExtractor

class CnaeEmitenteExtractor(BaseExtractor):
    field_name = "cnae_emitente"
    scope = "nfe"

    def extract(self, record):
        # TODO: Alteração temporária para evitar erro de chave estrangeira.
        # Esta linha ignora o valor original e sempre retorna None.
        # Descomente a linha original quando a tabela de CNAE estiver populada.
        
        return None

        # Linha original (comentada):
        # return record.get("CNAE_EMITENTE")