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

class AlertaBasicoBaixaCompetitividade(BaseAlert):

    alert_type = "alerta_basico_baixa_competitividade"
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alerta_config.json")

    def execute_alert(self, query_execute: dict[str, Any], objetos_analise: dict[str, Any], metodo_analise: dict[str, Any], cursor: RealDictCursor) -> dict[str, Any]:

        try:

            id_processo_licitatorio = objetos_analise['processo_licitatorio']
            id_item_licitacao = objetos_analise['item_licitacao']

            execucao_alerta = {
                "execucao_metodo": {
                    "id_metodo_analise": metodo_analise['id_metodo_analise'],
                    "data_execucao": str(date.today())
                },
                "objeto_analise": {
                    "nome_objeto": "Item Licitação/Processo Licitatório",
                    "id_item_licitacao": id_item_licitacao,
                    "id_processo_licitatorio": id_processo_licitatorio
                }
            }

            query_formatted = UtilsExecutionQuery.get_simple_query(query_execute, objetos_analise)

            cursor.execute(query_formatted)
            result = cursor.fetchone()

            if result:
                result_lances = result['lances']

                if result_lances < 10:
                    nivel_alerta = 3 if result_lances <= 3 else (2 if 3 < result_lances <= 6 else 1)

                    execucao_alerta["alerta"] = {
                        "nome": self.alert_type,
                        "nivel": nivel_alerta,
                        "descricao_longa": f"O item {id_item_licitacao} do processo licitatório {id_processo_licitatorio} possui apenas {result_lances} lances (baixa competitividade)",
                        "descricao_curta": f"O item {id_item_licitacao} do processo licitatório {id_processo_licitatorio} possui apenas {result_lances} lances (baixa competitividade)",
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

            objetos_analise = {}

            for objeto in metodo_analise['objetos_analise']:
                insert = data.get('insert')
                update = data.get('update')

                if not insert and not update:
                    raise FailQueueException(f"Erro de formatação da mensagem recebida {data}")

                if insert and objeto in insert:
                    objetos_analise[objeto] = insert.get(objeto)

                if update and objeto in update:
                    objetos_analise[objeto] = update.get(objeto).get('id')

            if 'item_licitacao' not in objetos_analise:
                raise FailQueueException(f"A mensagem recebida não possui os dados necessários para gerar o alerta {self.alert_type}.")

            if 'inserted_ids' in data and 'processo_licitatorio' in data.get('inserted_ids'):
                objetos_analise['processo_licitatorio'] = data.get('inserted_ids').get('processo_licitatorio')

            if 'processo_licitatorio' not in objetos_analise:
                query_processo = sql.SQL(
                    """
                    SELECT
                        il.id_processo_licitatorio
                    from
                        item_licitacao il
                    where
                        il.id_item_licitacao = {id_item_licitacao}
                    """
                ).format(
                    id_item_licitacao=sql.Literal(objetos_analise['item_licitacao'])
                )

                cursor.execute(query_processo)
                result_processo = cursor.fetchone()

                if result_processo.get('id_processo_licitatorio'):
                    objetos_analise['processo_licitatorio'] = result_processo.get('id_processo_licitatorio')
                else:
                    raise FailQueueException(f"O item de licitação {objetos_analise['item_licitacao']} não foi encontrado")

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
                    raise FailQueueException(
                        f"Os objetos {objetos_analise} não possuem as informações necessárias para gerar o alerta {self.alert_type}/v.{metodo_analise['versao']}")
            else:
                raise FailQueueException(
                    f"O alerta {self.alert_type}/v.{metodo_analise['versao']} já foi gerado para os objetos {objetos_analise}.")
        except Exception as e:
            raise FailQueueException(f"Erro ao gerar o alerta {self.alert_type}: {e}.")