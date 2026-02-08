from ..base_nested_extractor import BaseNestedExtractor


class PessoaExtractor(BaseNestedExtractor):
    field_name = "pessoa"
    scope = "processo_licitatorio_pessoa"
    nested_key = None  # We don't use the default nested extraction
    nested_scope = None

    def extract(self, record):
        data = record.get('participante_licitacao', {})
        if not data:
            return None

        pessoa = {
            'nome': data.get('nome_participante')
        }

        id_tipo_pessoa = str(data.get('id_tipo_pessoa', ''))

        if id_tipo_pessoa == '1':
            pessoa['pessoa_fisica'] = {
                'cpf': data.get('codigo_cic_participante')
            }
        elif id_tipo_pessoa == '2':
            pessoa['pessoa_pessoa_juridica'] = {
                'cnpj': data.get('codigo_cic_participante')
            }

        # Extract cotacao using cotacao scope extractors
        cotacao_list = data.get('cotacao', [])
        if cotacao_list:
            cotacao_extractors = self.extractors_by_scope.get('cotacao', {})
            extracted_cotacoes = []
            for cot in cotacao_list:
                temp_record = {'cotacao': cot}
                extracted_cot = {}
                for field_name, extractor in cotacao_extractors.items():
                    try:
                        value = extractor.extract(temp_record)
                        if value is not None:
                            extracted_cot[field_name] = value
                    except:
                        pass
                if extracted_cot:
                    extracted_cotacoes.append(extracted_cot)
            if extracted_cotacoes:
                pessoa['cotacao'] = extracted_cotacoes

        return pessoa
