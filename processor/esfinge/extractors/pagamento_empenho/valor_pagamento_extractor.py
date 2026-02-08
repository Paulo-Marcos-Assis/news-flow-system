from ..base_extractor import BaseExtractor


class ValorPagamentoExtractor(BaseExtractor):
    field_name = "valor_pagamento"
    scope = "pagamento_empenho"

    def extract(self, record):
        pagamento_empenho_data = record.get('pagamento_empenho', {})
        return pagamento_empenho_data.get('valor_pagamento')

