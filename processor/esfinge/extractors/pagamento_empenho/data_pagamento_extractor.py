from ..base_extractor import BaseExtractor


class DataPagamentoExtractor(BaseExtractor):
    field_name = "data_pagamento"
    scope = "pagamento_empenho"

    def extract(self, record):
        pagamento_empenho_data = record.get('pagamento_empenho', {})
        return pagamento_empenho_data.get('data_pagamento')
        
