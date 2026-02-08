from ..base_extractor import BaseExtractor

class RegularizacaoOrcamentariaExtractor(BaseExtractor):
    field_name = "regularizacao_orcamentaria"
    scope = "empenho"

    def extract(self, record):
        empenho_data = record.get('empenho', {})
        # cotacao.regularizacao
        regularizacao_boolean = empenho_data.get('regularizacao_orcamentaria')
        if regularizacao_boolean is not None:  # Verifica explicitamente por None
            try:
                if regularizacao_boolean == '-1':
                    return True

                else:
                    return False
            except (ValueError, TypeError):
                self.logger.info(f"Field not found in record")
        return False
