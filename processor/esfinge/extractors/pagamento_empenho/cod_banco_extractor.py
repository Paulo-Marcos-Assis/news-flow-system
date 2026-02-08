from ..base_extractor import BaseExtractor


class CodBancoExtractor(BaseExtractor):
    field_name = "cod_banco"
    scope = "pagamento_empenho"

    def extract(self, record):
        pagamento_empenho_data = record.get('pagamento_empenho', {})
        return pagamento_empenho_data.get('cod_banco')

