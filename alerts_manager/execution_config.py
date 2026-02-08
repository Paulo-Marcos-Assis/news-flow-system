

class ExecutionConfig():

    @staticmethod
    def get_alert_execution_config():
        execution_config = {
            "tipologia_83": {
                "insert": ["processo_licitatorio"],
                "update": ["processo_licitatorio.id_modalidade_licitacao", "processo_licitatorio.situacao"]
            },
            "vencedor_contumaz": {
                "insert": ["cotacao", "pessoa"],
                "update": ["cotacao.vencedor"]
            },
            "perdedor_contumaz": {
                "insert": ["cotacao", "pessoa"],
                "update": ["cotacao.vencedor"]
            },
            "preco_previsto_contratado": {
                "insert": ["contrato"],
                "update": ["contrato.valor_contrato"]
            },
            "sig": {
                "insert": ["sig_processo_licitatorio"],
                "update": []
            },
            "noticia_municipio": {
                "insert": ["noticia_municipio"],
                "update": []
            },
            "proximidade_datas": {
                "insert": ["processo_licitatorio_pessoa"],
                "update": ["processo_licitatorio_pessoa"]
            },
            "baixa_competitividade": {
                "insert": ["item_licitacao"],
                "update": ["item_licitacao"]
            },
            "noticia_processo_licitatorio": {
                "insert": ["noticia"],
                "update": []
            }
        }

        return execution_config