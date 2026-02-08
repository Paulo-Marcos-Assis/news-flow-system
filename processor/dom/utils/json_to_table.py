
class JsonToTable:

    @staticmethod
    def get_table_schema_json(table, fields):

        if table == "processo_licitatorio":
            return JsonToTable.processo_licitatorio_table(fields)
        elif table == "tipo_documento":
            return JsonToTable.tipo_documento_table(fields)
        elif table == "modalidade_licitacao":
            return JsonToTable.modalide_table(fields)
        elif table == "ente":
            return JsonToTable.ente_table(fields)
        elif table == "unidade_gestora":
            return JsonToTable.unidade_gestora_table(fields)
        elif table == "documento":
            return JsonToTable.documento_table(fields)
        else:
            return None


    @staticmethod
    def processo_licitatorio_table(fields):

        processo_licitatorio = {
            "numero_processo_licitatorio": fields.get("numero_processo"),
            "numero_edital": fields.get("numero_edital"),
            "data_limite": fields.get("data_limite_propostas"),
            "descricao_objeto": fields.get("objeto"),
            "data_abertura_certame": fields.get("data_abertura_propostas"),
            "data_inicio_propostas": fields.get("data_inicio_propostas"),
            "codigo_sfinge": fields.get("codigo_sfinge")
        }

        return processo_licitatorio

    @staticmethod
    def modalide_table(fields):

        modalidade = {
            "descricao": fields.get("descricao")
        }

        return modalidade

    @staticmethod
    def ente_table(fields):

        ente = {
            "ente": fields.get("ente")
        }

        return ente

    @staticmethod
    def unidade_gestora_table(fields):

        unidade_gestora = {
            "nome_ug": fields.get("nome_ug")
        }

        return unidade_gestora

    @staticmethod
    def documento_table(fields):

        documento = {
            "codigo_documento": fields.get("codigo_dom"),
            "nome_arquivo": fields.get("titulo_dom"),
            "data_emissao": fields.get("data_publicacao_dom"),
            "local_acesso_arquivo": fields.get("url_pdf_dom"),
            "url_dom": fields.get("url_dom")
        }

        return documento
    
    @staticmethod
    def tipo_documento_table(fields):

        tipo_documento = {
            "descricao": fields.get("tipo_documento")
        }

        return tipo_documento