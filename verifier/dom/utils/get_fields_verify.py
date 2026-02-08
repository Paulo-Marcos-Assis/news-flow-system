class GetFieldsVerify:

    @staticmethod
    def get_fields_verify(table):
        if table == "documento":
            return ['codigo_dom', 'data_publicacao_dom', 'titulo_dom', 'url_dom']
        elif table == "tipo_documento":
            return ['tipo_documento']
        elif table == "ente":
            return ['ente']
        elif table == "modalidade_licitacao":
            return ['descricao']
        elif table == "processo_licitatorio":
            return ['identificador', 'codigo_sfinge']
        elif table == "unidade_gestora":
            return ['nome_ug']
        else:
            return None