from ..base_extractor import BaseExtractor


class NomePessoaExtractor(BaseExtractor):
    field_name = "nome"
    scope = "pessoa"

    def extract(self, record):
        pessoa_data = record.get('pessoa', {})
        return pessoa_data.get('nome_participante')