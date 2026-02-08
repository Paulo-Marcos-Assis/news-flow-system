import os
import importlib
import json

from alerts.base_alert import BaseAlert
from execution_config import ExecutionConfig

from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService
from service_essentials.exceptions.fail_queue_exception import FailQueueException

import psycopg2
from psycopg2.extras import RealDictCursor

class AlertsService(BasicProducerConsumerService):

    def __init__(self):
        super().__init__()

        self.DB_CONFIG = {
            "dbname": os.getenv("DATABASE_PG"),
            "user": os.getenv("USERNAME_PG"),
            "password": os.getenv("SENHA_PG"),
            "host": os.getenv("HOST_PG"),
            "port": os.getenv("PORT_PG")
        }

        # --- OTIMIZAÇÃO: Conectar ao banco de dados na inicialização ---
        self.pg_connection = None
        self.connect_to_postgres()

    def connect_to_postgres(self):
        """Metodo para criar e armazenar a conexão com o PostgreSQL."""
        try:
            self.logger.info("Conectando ao banco de dados PostgreSQL...")
            self.pg_connection = psycopg2.connect(**self.DB_CONFIG)
            self.logger.info("Conexão com o PostgreSQL estabelecida com sucesso.")
        except psycopg2.Error as e:
            self.logger.error(f"Falha ao conectar com o PostgreSQL na inicialização: {e}")
            self.pg_connection = None

    def shutdown(self):
        """Metodo para fechar recursos (conexões) de forma limpa."""
        self.logger.info("Iniciando o desligamento do serviço de alertas...")
        if self.pg_connection and not self.pg_connection.closed:
            self.pg_connection.close()
            self.logger.info("Conexão com o PostgreSQL fechada.")

    @staticmethod
    def load_alerts(validate_execution):

        execution_config = ExecutionConfig.get_alert_execution_config()

        alerts = {}

        for alert, config in execution_config.items():
            path = f"alerts.{alert}.main"

            execute_alert = False

            for operation in config:
                if any(x in config[operation] for x in validate_execution[operation]):
                    execute_alert = True

                if execute_alert:
                    module_name = f"{path}"
                    module = importlib.import_module(module_name)

                    for attr in dir(module):
                        cls = getattr(module, attr)
                        if isinstance(cls, type) and issubclass(cls, BaseAlert) and cls is not BaseAlert:
                            alerts[cls.alert_type] = cls()

        return alerts


    def process_message(self, message):

        data = message.get('ids_gerados_db').get('data')

        if "insert" not in data and "update" not in data:
            raise FailQueueException(f"A mensagem recebida pelo gerenciador de alertas possui a estrutura incorreta.")

        self.logger.info(f"Serviço de alertas recebeu a mensagem: {data}")

        list_insert = []
        list_update = []
        validate_execution = {}

        for op in data:
            for table in data[op]:
                if op == 'update':
                    for column in data[op][table]:
                        list_update.append(f"{table}.{column}")
                elif op == 'insert':
                    list_insert.append(f"{table}")
                else:
                    raise FailQueueException(f"A mensagem recebida pelo gerenciador de alertas não possui a estrutura correta.")

        validate_execution['insert'] = list_insert
        validate_execution['update'] = list_update

        alerts = self.load_alerts(validate_execution)

        if not alerts:
            raise FailQueueException(f"A mensagem recebida não possui as informações necessárias para gerar os alertas cadastrados no sistema.")

        if not self.pg_connection or self.pg_connection.closed:
            self.logger.warning("Conexão com o PostgreSQL perdida. Tentando reconectar...")
            self.connect_to_postgres()

            if not self.pg_connection:
                self.logger.error("Não foi possível reconectar ao PostgreSQL. Abortando processamento da mensagem.")
                return {}

        with self.pg_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            for alert_type, alert in alerts.items():
                try:
                    self.logger.info(f"Executando alerta {alert_type}")
                    result = alert.generate_alert(data, cursor)

                    if result:
                        self.logger.info(f"O alerta {alert_type} gerou o seguinte resultado: {result}")
                        self.queue_manager.publish_message(self.output_queue, json.dumps(result,indent=4))
                except Exception as e:
                    self.logger.warning(e)

        return None


if __name__ == '__main__':

    service = AlertsService()
    service.logger.info("Iniciando o serviço de geração de alertas...")

    try:
        service.logger.info("Iniciando o serviço de geração de alertas...")
        service.start()
    except KeyboardInterrupt:
        service.logger.info("Serviço interrompido pelo usuário.")
    finally:
        service.shutdown()
