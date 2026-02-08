from ..base_extractor import BaseExtractor


class NumeroContaBancariaPagadoraExtractor(BaseExtractor):
    field_name = "nro_conta_bancaria_pagadora"
    scope = "pagamento_empenho"

    def extract(self, record):
        pagamento_empenho_data = record.get('pagamento_empenho', {})
        return pagamento_empenho_data.get('nro_conta_bancaria_pagadora')

