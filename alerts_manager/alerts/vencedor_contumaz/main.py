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

class AlertaBasicoVencedorContumaz(BaseAlert):

    alert_type = "alerta_basico_vencedor_contumaz"
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alerta_config.json")

    def execute_alert(self, query_execute: dict[str, Any], objetos_analise: dict[str, Any], metodo_analise: dict[str, Any], cursor: RealDictCursor) -> dict[str, Any]:

        try:

            id_objeto = objetos_analise['pessoa']

            execucao_alerta = {
                "execucao_metodo": {
                    "id_metodo_analise": metodo_analise['id_metodo_analise'],
                    "data_execucao": str(date.today())
                },
                "objeto_analise": {
                    "nome_objeto": "Pessoa",
                    "id_pessoa": id_objeto
                }
            }

            obj = {k: v for k, v in objetos_analise.items() if k == 'pessoa'}
            query_formatted = UtilsExecutionQuery.get_simple_query(query_execute, obj)

            cursor.execute(query_formatted)
            result = cursor.fetchone()

            if result:
                execucao_alerta["alerta"] = {
                    "nome": self.alert_type,
                    "nivel": 2,
                    "descricao_longa": f"A pessoa {id_objeto} é um vencedor contumaz.",
                    "descricao_curta": f"A pessoa {id_objeto} é um vencedor contumaz.",
                    "data_ultima_execucao": str(date.today())
                }

            return execucao_alerta
        except Exception as e:
            raise FailQueueException(f"Erro ao executar a consulta do alerta {self.alert_type}: {e}")

    def validate_alert(self, query_validate: dict[str, Any], objetos_analise: dict[str, Any], cursor: RealDictCursor) -> bool:

        try:
            obj = {k: v for k, v in objetos_analise.items() if k == 'cotacao'}
            query_formatted = UtilsExecutionQuery.get_simple_query(query_validate, obj)

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

            objetos_analise = {}

            insert = data.get('insert')
            update = data.get('update')

            if insert and 'cotacao' in insert:
                objetos_analise.update(insert)

            if update and 'cotacao' in update:
                objetos_analise.update(data.get('update').get('cotacao').get('id'))

            if not objetos_analise:
                raise FailQueueException(f"A mensagem recebida não possui os dados necessários para gerar o alerta {self.alert_type}.")

            query_pessoa = sql.SQL(
                """
                SELECT
                    cot.id_pessoa
                from
                    cotacao cot
                where
                    cot.id_cotacao = {id_cotacao}
                """
            ).format(
                id_cotacao=sql.Literal(objetos_analise['cotacao'])
            )

            cursor.execute(query_pessoa)
            result = cursor.fetchone()

            if result['id_pessoa']:
                objetos_analise['pessoa'] = result['id_pessoa']
            else:
                raise FailQueueException(f"A pessoa que realizou a cotação {objetos_analise['cotacao']} não foi encontrada")

            query_execution = UtilsExecutionQuery.validate_execution_alerta(metodo_analise, objetos_analise)

            cursor.execute(query_execution)
            result = cursor.fetchone()

            if not result:
                query_validate = config['query_validate']
                result_validate = self.validate_alert(query_validate, objetos_analise, cursor)

                if result_validate:
                    query_execute = config['query_execute']
                    result_execute = self.execute_alert(query_execute, objetos_analise, metodo_analise, cursor)

                    return result_execute
                else:
                    raise FailQueueException(f"Os objetos {objetos_analise} não possuem as informações necessárias para gerar o alerta {self.alert_type}/v.{metodo_analise['versao']}")
            else:
                raise FailQueueException(f"O alerta {self.alert_type}/v.{metodo_analise['versao']} já foi gerado para a pessoa {objetos_analise['pessoa']}.")
        except Exception as e:
            raise FailQueueException(f"Erro ao gerar o alerta {self.alert_type}: {e}.")