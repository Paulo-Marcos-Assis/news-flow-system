from ..base_extractor import BaseExtractor


class DataValidadePropostaExtractor(BaseExtractor):
    field_name = "data_validade_proposta"
    scope = "processo_licitatorio_pessoa"

    def extract(self, record):
        data = record.get('participante_licitacao', {})
        return data.get('data_validade_proposta')
