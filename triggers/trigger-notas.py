import json
import os
import sys
import calendar
import traceback


# Adiciona a raiz do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from service_essentials.utils.logger import Logger
from service_essentials.queue_manager.queue_manager_factory import QueueManagerFactory

# --- Configurações ---
config_trigger = "notas.json"
output_queue = "notas_collector"

def generate_messages(config_file):
    """
    Gera mensagens para cada DIA dentro dos anos/meses especificados no config.
    """
    
    with open(config_file, 'r') as file:
        config = json.load(file)

    year_list = config.get("year", [])
    month_list = config.get("month", [])
    day_list = config.get("day")

    messages = []
    for year in year_list:
        months_to_process = month_list if month_list else range(1, 13)
        for month in months_to_process:
            days_to_process = []
            if day_list:
                days_to_process = day_list
            else:
                num_days = calendar.monthrange(year, month)[1]
                days_to_process = range(1, num_days + 1)

            for day in days_to_process:
                date_str = f"{year}-{month:02d}-{day:02d}"
                messages.append({
                    "url_s3": "https://s3.ceos.ufsc.br/",
                    "bucket": "mpsc",
                    "prefix": "nfesAutoSync/",
                    "cabecalho": "NFECabecalho",
                    "itens": "NFEItens",
                    "format": ".parquet",
                    "date": date_str
                })
    return messages

# --- Bloco Principal de Execução ---
if __name__ == '__main__':
    logger = None
    try:
        logger = Logger(log_to_console=True)
        messages = generate_messages(config_trigger)
        
        if not messages:
            logger.warning(f"Nenhuma mensagem foi gerada. Verifique o conteúdo do arquivo '{config_trigger}'.")
            sys.exit(0)

        logger.info(f"Geradas {len(messages)} mensagens diárias para enviar.")

        queue_manager = QueueManagerFactory.get_queue_manager()
        queue_manager.connect()
        logger.info(f"Conectando à fila: {output_queue}...")
        queue_manager.declare_queue(output_queue)
        logger.info("...conectado com sucesso.")

        for i, message in enumerate(messages):
            logger.info(f"Enviando mensagem #{i+1} de {len(messages)} para {output_queue}: [data: {message['date']}]")
            queue_manager.publish_message(output_queue, json.dumps(message))
        
        logger.info("Todas as mensagens foram enviadas com sucesso.")

    except FileNotFoundError:
        if not logger: logger = Logger(log_to_console=True)
        logger.error(f"ERRO CRÍTICO: O arquivo de configuração '{config_trigger}' não foi encontrado no diretório de trabalho atual.")
        
    except Exception as e:
        if not logger: logger = Logger(log_to_console=True)
        tb_str = traceback.format_exc()
        logger.error(f"Ocorreu um erro fatal no trigger: {e}\nTRACEBACK:\n{tb_str}")