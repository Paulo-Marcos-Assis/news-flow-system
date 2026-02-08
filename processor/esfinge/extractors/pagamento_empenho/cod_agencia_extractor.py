from ..base_extractor import BaseExtractor


class CodAgenciaExtractor(BaseExtractor):
    field_name = "cod_agencia"
    scope = "pagamento_empenho"

    def extract(self, record):
        pagamento_empenho_data = record.get('pagamento_empenho', {})
        return pagamento_empenho_data.get('cod_agencia')

