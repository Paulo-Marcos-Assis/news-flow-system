from ..base_extractor import BaseExtractor


class DataValidadeExtractor(BaseExtractor):
    field_name = "data_validade"
    scope = "pagamento_empenho"

    def extract(self, record):
        pagamento_empenho_data = record.get('pagamento_empenho', {})
        return pagamento_empenho_data.get('data_prazo_final_prestacao_contas')
