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

import traceback

class AlertaBasicoProximidadeDatas(BaseAlert):

    alert_type = "alerta_basico_proximidade_datas"
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alerta_config.json")

    def execute_alert(self, query_execute: dict[str, Any], objetos_analise: dict[str, Any], metodo_analise: dict[str, Any], cursor: RealDictCursor) -> dict[str, Any]:
        try:

            id_processo_licitatorio = objetos_analise['processo_licitatorio']
            id_pessoa = objetos_analise['pessoa']

            execucao_alerta = {
                "execucao_metodo": {
                    "id_metodo_analise": metodo_analise['id_metodo_analise'],
                    "data_execucao": str(date.today())
                },
                "objeto_analise": {
                    "nome_objeto": "Pessoa/Processo Licitatório",
                    "id_processo_licitatorio": id_processo_licitatorio,
                    "id_pessoa": id_pessoa
                }
            }

            query_formatted = UtilsExecutionQuery.get_simple_query(query_execute, objetos_analise)

            cursor.execute(query_formatted)
            result = cursor.fetchone()

            if result:
                result_diferenca = result['diferenca']

                if result_diferenca < 10:
                    nivel_alerta = 3 if result_diferenca <= 3 else (2 if 3 < result_diferenca <= 6 else 1)

                    execucao_alerta["alerta"] = {
                        "nome": self.alert_type,
                        "nivel": nivel_alerta,
                        "descricao_longa": f"A empresa {id_pessoa} iniciou suas atividades {result_diferenca} meses antes da data de abertura do certame {id_processo_licitatorio}",
                        "descricao_curta": f"A empresa {id_pessoa} iniciou suas atividades {result_diferenca} meses antes da data de abertura do certame {id_processo_licitatorio}",
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

            metodo_analise = config['metodo_analise']

            tabela = "metodo_analise"
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

            insert = data.get('insert')
            update = data.get('update')

            if insert and 'processo_licitatorio_pessoa' in insert:
                objetos_analise = {
                    "processo_licitatorio": insert.get('processo_licitatorio_pessoa').get('id_processo_licitatorio'),
                    "pessoa": insert.get('processo_licitatorio_pessoa').get('id_pessoa')
                }
            elif update and 'processo_licitatorio_pessoa' in update:
                objetos_analise = {
                    "processo_licitatorio": update.get('processo_licitatorio_pessoa').get('id_processo_licitatorio'),
                    "pessoa": update.get('processo_licitatorio_pessoa').get('id_pessoa')
                }
            else:
                raise FailQueueException(f"A mensagem recebida não possui os dados necessários para gerar o alerta {self.alert_type}")

            query_execution = UtilsExecutionQuery.validate_execution_alerta(metodo_analise, objetos_analise)

            cursor.execute(query_execution)
            result = cursor.fetchone()

            if not result:
                query_validate = config['query_validate']
                result_validate = self.validate_alert(query_validate, objetos_analise, cursor)

                if result_validate:
                    query_execute = config['query_execute']
                    result_execute = self.execute_alert(query_execute, objetos_analise, metodo_analise, cursor)

                    if result_execute:
                        return result_execute
                else:
                    raise FailQueueException(f"Os objetos {objetos_analise} não possuem as informações necessárias para gerar o alerta {self.alert_type}/v.{metodo_analise['versao']}")
            else:
                raise FailQueueException(f"O alerta {self.alert_type}/v.{metodo_analise['versao']} já foi gerado para a pessoa {objetos_analise['pessoa']}.")


        except Exception as e:
            raise FailQueueException(f"Erro ao gerar o alerta {self.alert_type}: {e}. {traceback.format_exc()}")