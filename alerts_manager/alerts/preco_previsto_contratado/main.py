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

class AlertaBasicoPrecoPrevistoContratado(BaseAlert):

    alert_type = "alerta_basico_preco_previsto_contratado"
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alerta_config.json")

    def execute_alert(self, query_execute: dict[str, Any], objetos_analise: dict[str, Any], metodo_analise: dict[str, Any], cursor: RealDictCursor) -> dict[str, Any]:

        try:
            id_objeto = objetos_analise['processo_licitatorio']

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

            query_formatted = UtilsExecutionQuery.get_simple_query(query_execute, objetos_analise)

            cursor.execute(query_formatted)
            result = cursor.fetchone()

            self.logger.info(f"{query_formatted}")

            if result and result['valor_total_previsto']:

                diff_valores_percent = (result['valor_contrato'] - result['valor_total_previsto'])/result['valor_total_previsto']
                
                if diff_valores_percent >= 0.3:
                    nivel = 3
                elif diff_valores_percent >= 0.2:
                    nivel = 2
                elif diff_valores_percent >= 0.1:
                    nivel = 1
                else:
                    raise FailQueueException(f"A diferença de preço não é suficiente para gerar um alerta")
                
                execucao_alerta["alerta"] = {
                    "nome": self.alert_type,
                    "nivel": nivel,
                    "descricao_longa": f"O processo licitatório {id_objeto} possui valor de contrato acima da média",
                    "descricao_curta": f"O processo licitatório {id_objeto} possui valor de contrato acima da média",
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
            update = data.get('update')

            if insert:
                for tb in insert:
                    if tb in execution_config['insert']:
                        objetos_analise[tb] = insert[tb]

            if update:
                for tb in update:
                    for field in update[tb]:
                        if field != 'id' and f"{tb}.{field}" in execution_config['update']:
                            objetos_analise[tb] = update[tb]['id']

            if 'processo_licitatorio' not in objetos_analise and 'contrato' in objetos_analise:
                query = sql.SQL("""
                    SELECT 
                        c.id_processo_licitatorio 
                    FROM 
                        contrato c 
                    WHERE 
                        c.id_contrato = {id_contrato}
                    """).format(id_contrato = sql.Literal(objetos_analise['contrato']))
                
                cursor.execute(query)
                result_contrato = cursor.fetchone()

                if result_contrato:
                    objetos_analise['processo_licitatorio'] = result_contrato.get('id_processo_licitatorio')
                    del objetos_analise['contrato']

            if not objetos_analise or 'processo_licitatorio' not in objetos_analise:
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

                    return result_execute
                else:
                    raise FailQueueException(f"Os objetos {objetos_analise} não possuem as informações necessárias para gerar o alerta {self.alert_type}/v.{metodo_analise['versao']}")
            else:
                raise FailQueueException(f"O alerta {self.alert_type}/v.{metodo_analise['versao']} já foi gerado para os objetos {objetos_analise}.")
        except Exception as e:
            raise FailQueueException(f"Erro ao gerar o alerta {self.alert_type}: {e}.")