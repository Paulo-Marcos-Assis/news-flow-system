from ..base_extractor import BaseExtractor

class PrestacaoContasExtractor(BaseExtractor):
    field_name = "prestacao_contas"
    scope = "empenho"


    def extract(self, record):
        empenho_data = record.get('empenho', {})
        # cotacao.prestacao
        prestacao_boolean = empenho_data.get('prestacao_contas')
        if prestacao_boolean is not None:  # Verifica explicitamente por None
            try:
                if prestacao_boolean == '-1':
                    return True

                else:
                    return False
            except (ValueError, TypeError):
                self.logger.info(f"Field not found in record")
        return False
