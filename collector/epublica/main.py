import os
import io
import s3fs
import boto3
import pandas as pd
from dotenv import load_dotenv
from botocore.client import Config
import sentry_sdk
import json

from decimal import Decimal



from service_essentials.utils.logger import Logger
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService

import requests
from datetime import datetime
import time



class CollectorEpublica(BasicProducerConsumerService):
    def __init__(self):
        super().__init__()
        self.MAX_RETRIES = 5
        self.DELAY = 5

    def process_message(self, message):
        title = " Collector Epublica Started "
        logger.info(title.center(60, "#"))

        api_url = message
        self.logger.info(f"Iniciando coleta URL: {api_url}")

        for attempt in range(self.MAX_RETRIES):
            try:
                # Faz a requisição HTTP com um timeout para não ficar preso indefinidamente
                response = requests.get(api_url, timeout=60)
                
                # Lança uma exceção para códigos de erro HTTP (4xx ou 5xx)
                response.raise_for_status()
                
                # Extrai os dados JSON da resposta
                licitacoes_data = response.json()
                
                self.logger.info(f"Sucesso! Coletadas {len(licitacoes_data)} licitações da URL.")

                # Estrutura a mensagem de retorno com metadados úteis
                result = {
                    "source": "epublica",
                    "collection_date": datetime.now().isoformat(),
                    "source_url": api_url,
                    "payload": licitacoes_data
                }
                
                return result # Retorna o resultado para ser enviado para a próxima fila

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Falha na tentativa {attempt + 1}/{self.MAX_RETRIES} para a URL {api_url}: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    self.logger.info(f"Aguardando {self.RETRY_DELAY_SECONDS} segundos para tentar novamente...")
                    time.sleep(self.RETRY_DELAY_SECONDS)
                else:
                    self.logger.error(f"Número máximo de tentativas atingido para {api_url}. Desistindo da mensagem.")
                    # Retornar None ou lançar uma exceção pode ser usado para descartar a mensagem
                    return None
        
        # Este ponto não deve ser alcançado em condições normais
        return None

if __name__ == '__main__':
    logger = Logger(log_to_console=True)
    title = " Collector E-publica Started "
    logger.info(title.center(60, "#"))
    processor = CollectorEpublica()
    processor.start()
