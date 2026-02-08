from ..base_extractor import BaseExtractor


class DataPublicacaoJustificativaExtractor(BaseExtractor):
    field_name = "data_publicacao_justificativa"
    scope = "pagamento_empenho"

    def extract(self, record):
        pagamento_empenho_data = record.get('pagamento_empenho', {})
        return pagamento_empenho_data.get('data_publicacao_justificativa')
