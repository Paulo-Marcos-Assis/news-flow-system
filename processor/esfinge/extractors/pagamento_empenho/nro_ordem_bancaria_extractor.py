from ..base_extractor import BaseExtractor


class NumeroOrdemBancariaExtractor(BaseExtractor):
    field_name = "nro_ordem_bancaria"
    scope = "pagamento_empenho"

    def extract(self, record):
        pagamento_empenho_data = record.get('pagamento_empenho', {})
        return pagamento_empenho_data.get('nro_ordem_bancaria')

