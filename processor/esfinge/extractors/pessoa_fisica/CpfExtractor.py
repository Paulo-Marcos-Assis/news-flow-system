from ..base_extractor import BaseExtractor


class CpfPessoaFisicaExtractor(BaseExtractor):
    field_name = "cpf"
    scope = "pessoa_fisica"

    def extract(self, record):
        data = record.get('pessoa_fisica', {})
        id_tipo_pessoa = data.get('id_tipo_pessoa')
        if str(id_tipo_pessoa) == '1':
            return data.get('codigo_cic_participante')
        return None
