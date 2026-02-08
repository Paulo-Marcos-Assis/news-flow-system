from ..base_extractor import BaseExtractor

class VencedorExtractor(BaseExtractor):
    field_name = "vencedor"
    scope = "cotacao"

    def extract(self, record):
        cotacao_data = record.get('cotacao', {})
        # cotacao.vencedor
        vencedor_boolean = cotacao_data.get('vencedor')
        if vencedor_boolean is not None:  # Verifica explicitamente por None
            try:
                if vencedor_boolean == '-1':
                    return True

                else:
                    return False
            except (ValueError, TypeError):
                self.logger.info(f"Field not found in record")
        return False
