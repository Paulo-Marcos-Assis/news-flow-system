import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any

import time
# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from service_essentials.queue_manager.queue_manager_factory import QueueManagerFactory
from service_essentials.utils.logger import Logger

logger = Logger(log_to_console=True)

COLLECTOR_QUEUE = "pncp_collector"
PROCESSOR_QUEUE_TO_MONITOR = "pncp_processor" 

CONTRATACOES_URL = 'https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao'
CONTRATOS_URL = 'https://pncp.gov.br/api/consulta/v1/contratos'
INSTRUMENTOS_COBRANCA_URL = 'https://pncp.gov.br/api/consulta/v1/instrumentoscobranca/inclusao'

# Calculate yesterday and today dynamically
today_date_dynamic = datetime.now()
yesterday_date_dynamic = today_date_dynamic - timedelta(days=1)

start_date = yesterday_date_dynamic.strftime("%Y%m%d")
end_date = today_date_dynamic.strftime("%Y%m%d")

def generate_contratacoes_message(start_date: str, end_date: str) -> list[dict[str, Any]]:
    """Generates a list of messages for each modality for a specific date range."""
    messages = []
    for modalidade in range(1, 14):
        messages.append({
            "api_url": CONTRATACOES_URL,
            "modalidade": modalidade,
            "uf": "sc",
            "data_inicial": start_date,
            "data_final": end_date,
        })
    return messages

def generate_contrato_message(start_date: str, end_date: str) -> list[dict[str, Any]]:
    """Generates a message for the contratos endpoint for a specific date range."""
    messages = [{
        "api_url": CONTRATOS_URL,
        "data_inicial": start_date,
        "data_final": end_date,
    }]
    return messages 

def generate_instrumento_cobranca_message(start_date: str, end_date: str) -> list[dict[str, Any]]:
    """Generates a message for the instrumentoscobranca endpoint for a specific date range."""
    messages = [{
        "api_url": INSTRUMENTOS_COBRANCA_URL,
        "data_inicial": start_date,
        "data_final": end_date,
    }]
    return messages

def connect_to_queue(queues_to_declare: list[str]) -> QueueManagerFactory:
    """Establishes a connection and declares all specified queues."""
    queue_manager = QueueManagerFactory.get_queue_manager() 
    logger.info(f"Connecting to RabbitMQ...")
    queue_manager.connect()
    for queue in queues_to_declare:
        queue_manager.declare_queue(queue)
    logger.info("...connected and all queues declared successfully.")
    return queue_manager

def send_message_to_queue(messages: list[dict[str, Any]], queue_manager: QueueManagerFactory, queue_name: str):
    """Publishes a list of messages to the specified message queue."""
    for i, message in enumerate(messages):
        logger.info(f"Sending message #{i+1} to {queue_name}: {message}")
        queue_manager.publish_message(queue_name, json.dumps(message, indent=4))
    logger.info(f"...Sent {len(messages)} messages successfully to {queue_name}.")

def wait_for_processor_to_finish(queue_manager: QueueManagerFactory):
    """Waits for the processor's input queue to become empty."""
    logger.info(f"Waiting for processor's input queue '{PROCESSOR_QUEUE_TO_MONITOR}' to become empty...")
    while True:
        try:
            queue_state = queue_manager.channel.queue_declare(queue=PROCESSOR_QUEUE_TO_MONITOR, passive=True)
            message_count = queue_state.method.message_count
            
            if message_count == 0:
                logger.info(f"Queue '{PROCESSOR_QUEUE_TO_MONITOR}' is empty. Proceeding.")
                break
            else:
                logger.info(f"Queue '{PROCESSOR_QUEUE_TO_MONITOR}' still has {message_count} messages. Waiting for 15 seconds...")
                time.sleep(15)
        except Exception as e:
            logger.warning(f"Could not check queue status for '{PROCESSOR_QUEUE_TO_MONITOR}'. Retrying in 60s. Error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    logger.info("################## Trigger PNCP Started ###############")
    logger.info(f"Collecting data for range: {start_date} to {end_date}")
    queue_manager = None
    try:
        # 1. Connect and declare all necessary queues
        queues = [COLLECTOR_QUEUE, PROCESSOR_QUEUE_TO_MONITOR]
        queue_manager = connect_to_queue(queues)

        # 2. Collect CONTRATACOES
        logger.info("--- Step 1: Triggering CONTRATACOES collection ---")
        contratacoes_messages = generate_contratacoes_message(start_date, end_date)
        send_message_to_queue(contratacoes_messages, queue_manager, COLLECTOR_QUEUE)
        
        # 3. Wait for CONTRATACOES to be processed
        wait_for_processor_to_finish(queue_manager)

        # 4. Collect CONTRATOS
        logger.info("--- Step 2: Triggering CONTRATOS collection ---")
        contrato_messages = generate_contrato_message(start_date, end_date)
        send_message_to_queue(contrato_messages, queue_manager, COLLECTOR_QUEUE)
        
        # 5. Wait for CONTRATOS to be processed
        wait_for_processor_to_finish(queue_manager)

        # 6. Collect INSTRUMENTOS COBRANCA
        logger.info("--- Step 3: Triggering INSTRUMENTOS COBRANCA collection ---")
        instrumento_cobranca_messages = generate_instrumento_cobranca_message(start_date, end_date)
        send_message_to_queue(instrumento_cobranca_messages, queue_manager, COLLECTOR_QUEUE)

        # 7. Wait for INSTRUMENTOS COBRANCA to be processed
        wait_for_processor_to_finish(queue_manager)

        logger.info("All trigger messages have been sent successfully.")

    except Exception as e:
        logger.exception(f"...an error occurred: {e}")
    finally:
        if queue_manager:
            logger.info("Closing queue connection.")
            queue_manager.close_connection()

