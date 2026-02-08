from ..base_extractor import BaseExtractor


class CnpjPessoaJuridicaExtractor(BaseExtractor):
    field_name = "cnpj"
    scope = "pessoa_pessoa_juridica"

    def extract(self, record):
        data = record.get('pessoa_pessoa_juridica', {})
        id_tipo_pessoa = data.get('id_tipo_pessoa')
        if str(id_tipo_pessoa) == '2':
            return data.get('codigo_cic_participante')
        return None
