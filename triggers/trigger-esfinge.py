import json
import os
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from service_essentials.utils.logger import Logger
from service_essentials.queue_manager.queue_manager_factory import QueueManagerFactory


# Caminho absoluto para o diretório do script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Configuration for the trigger
config_trigger = os.path.join(SCRIPT_DIR, 'esfinge.json')
output_queue = "esfinge_collector"

def generate_messages(config_file):
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        logger.error(f"Arquivo de configuração não encontrado: {config_file}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao interpretar JSON do arquivo {config_file}: {e}")
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao abrir o arquivo {config_file}: {e}")
        raise
    
    year_list = config.get("year", [])
    data_path_list = config.get("data_path", [])
    entity_types = config.get("entity_types", [])

    messages = []

    if entity_types == ["all"]:
        entity_types = [
                        "ente",
                        "pagamento_empenho",
                        "unidade_gestora",
                        "inidoneidade",
                        "processo_licitatorio",
                        "convenio",
                        "participante_convenio",
                        "item_licitacao",
                        "cotacao",
                        "contrato",
                        "empenho",
                        "subempenho",
                        "liquidacao",
                        "estorno_pagamento"
                        ]
    elif entity_types == ["aux"]:
        entity_types = [
            "categoria_economica_despesa",
            "detalhamento_elemento_despesa",
            "elemento_despesa",
            "ente",
            "funcao",
            "poder_orgao",
            "programa",
            "projeto_atividade",
            "remessa_unidade_gestora",
            "situacao_remessa",
            "sub_funcao",
            "tipo_esfera",
            "tipo_unidade",
            "unidade_gestora",
            "unidade_orcamentaria"
        ]

    # Generate one message per entity_type per year per data_path
    for data_path in data_path_list:
        for year in year_list:
            for entity_type in entity_types:
                    messages.append({
                        "data_path": f"{data_path}",
                        "year": f"{year}",
                        "entity_type": entity_type
                    })

    return messages
if __name__ == "__main__":
    print("################## Trigger started for the flow: e-Sfinge ##################")
    # Generate messages based on the configuration file
    messages = generate_messages(config_trigger)
    logger = Logger(log_to_console=True)

    queue_manager = QueueManagerFactory.get_queue_manager()
    queue_manager.connect()
    logger.info(f"Connecting to queue: {output_queue}...")
    queue_manager.declare_queue(output_queue)
    logger.info("...connected to queues successfully.")

    for i, message in enumerate(messages):
        logger.info(f"Sending collecting message #{i} to {output_queue}: {message}")
        queue_manager.publish_message(output_queue, json.dumps(message, indent=4))