import os
import json
from datetime import date

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from typing import Any

from ..base_alert import BaseAlert
from ..utils_execution_query import UtilsExecutionQuery
from service_essentials.exceptions.fail_queue_exception import FailQueueException

class AlertaBasicoNoticiasProcessoLicitatorio(BaseAlert):

    alert_type = "alerta_basico_noticias_processo_licitatorio"
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alerta_config.json")

    def execute_alert(self, query_execute: dict[str, Any], objetos_analise: dict[str, Any], metodo_analise: dict[str, Any], cursor: RealDictCursor) -> dict[str, Any]:

        try:
            id_objeto = objetos_analise['processo_licitatorio']
            id_noticia = objetos_analise['noticia']

            execucao_alerta = {
                "execucao_metodo": {
                    "id_metodo_analise": metodo_analise.get('id_metodo_analise'),
                    "data_execucao": str(date.today())
                },
                "objeto_analise": {
                    "nome_objeto": "Processo Licitatório",
                    "id_processo_licitatorio": id_objeto
                }
            }

            execucao_alerta["alerta"] = {
                "nome": self.alert_type,
                "nivel": 3,
                "descricao_longa": f"O processo licitatório {id_objeto} possui a noticia {id_noticia} associada",
                "descricao_curta": f"O processo licitatório {id_objeto} possui a noticia {id_noticia} associada",
                "data_ultima_execucao": str(date.today())
            }

            return execucao_alerta
        except Exception as e:
            raise FailQueueException(f"Erro ao executar a consulta do alerta {self.alert_type}: {e}")

    def validate_alert(self, query_validate: dict[str, Any], objetos_analise: dict[str, Any], cursor: RealDictCursor) -> bool:

        try:
            query_formatted = UtilsExecutionQuery.get_simple_query(query_validate, objetos_analise)

            cursor.execute(query_formatted)
            result = cursor.fetchone()

            if result:
                return True
            else:
                return False
        except Exception as e:
            raise FailQueueException(f"Erro ao validar a consulta do alerta {self.alert_type}: {e}")

    def generate_alert(self, data: dict[str, Any], cursor: RealDictCursor):

        try:
            with open(self.config_file, 'r') as file:
                config = json.load(file)

            metodo_analise = config.get('metodo_analise')

            tabela= "metodo_analise"
            pk_column = f"id_metodo_analise"
            id_metodo_analise = metodo_analise['id_metodo_analise']

            query_ma = sql.SQL("SELECT {} FROM {} WHERE {} LIMIT 1").format(
                sql.Identifier(pk_column),
                sql.Identifier(tabela),
                sql.SQL("{} = {}").format(sql.Identifier(pk_column), sql.Literal(id_metodo_analise))
            )

            cursor.execute(query_ma)
            result_ma = cursor.fetchone()

            if not result_ma or not result_ma[pk_column]:
                raise FailQueueException(f"O método de análise informado para o alerta ({self.alert_type}) não existe.")

            objetos_analise = {}
            execution_config = config['execution_config']

            insert = data.get('insert')

            if insert:
                for tb in insert:
                    if tb in execution_config['insert']:
                        objetos_analise[tb] = insert[tb]

            query_pl = sql.SQL("SELECT {} FROM {} WHERE {} LIMIT 1").format(
                sql.Identifier('id_processo_licitatorio'),
                sql.Identifier('noticia'),
                sql.SQL("{} = {}").format(sql.Identifier('id_noticia'), sql.Literal(objetos_analise['noticia']))
            )

            cursor.execute(query_pl)
            result_pl = cursor.fetchone()

            if result_pl and result_pl['id_processo_licitatorio']:
                objetos_analise["processo_licitatorio"] = result_pl['id_processo_licitatorio']

            if not objetos_analise or 'noticia' not in objetos_analise or 'processo_licitatorio' not in objetos_analise:
                raise FailQueueException(f"A mensagem recebida não possui os dados necessários para gerar o alerta {self.alert_type}")

            query_execution = UtilsExecutionQuery.validate_execution_alerta(metodo_analise, objetos_analise)

            cursor.execute(query_execution)
            result = cursor.fetchone()

            if not result:
                query_execute = config['query_execute']
                result_execute = self.execute_alert(query_execute, objetos_analise, metodo_analise, cursor)

                return result_execute
            else:
                raise FailQueueException(
                    f"O alerta {self.alert_type}/v.{metodo_analise['versao']} já foi gerado para os objetos {objetos_analise}.")
        except Exception as e:
            raise FailQueueException(f"Erro ao gerar o alerta {self.alert_type}: {e}.")