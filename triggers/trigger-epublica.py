import json
import os
from datetime import datetime
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from service_essentials.utils.logger import Logger
from service_essentials.queue_manager.queue_manager_factory import QueueManagerFactory


# Caminho absoluto para o diretório do script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Configuration for the trigger
config_trigger = os.path.join(SCRIPT_DIR, 'configEpublica.json')  # Nome do arquivo de configuração JSON
disponiveis_triggers = os.path.join(SCRIPT_DIR, "disponiveisEpublica.json")

output_queue = "epublica_collector"

disponiveis = json.load(open(disponiveis_triggers, 'r'))


def mapeamento():
    # chamar função criada lá no jupyter aqui, talvez fazer um arquivo
    # TODO implementar função mapeamento (atualizar json entidades_disponiveis e endpoints_disponiveis em disponiveisEpublica) com base no CSV criado
    pass


def generate_messages(config_file):
    ultima_verificacao_str = disponiveis.get("ultima_verificacao")
    ultima_verificacao_date = datetime.strptime(ultima_verificacao_str, '%d-%m-%Y')

    today_data = datetime.today().strftime('%d-%m-%Y')
    today_data_as_datetime = datetime.strptime(today_data, '%d-%m-%Y')

    time_difference = today_data_as_datetime - ultima_verificacao_date

    if time_difference.days >= 60:
        # chamar função mapeamento que muda os jsons de disponiveis
        mapeamento()
        disponiveis["ultima_verificacao"] = today_data

    config = json.load(open(config_trigger, 'r'))

    data_inicial = datetime.strptime(config.get('data_inicial'), "%d-%m-%Y")
    data_final = datetime.strptime(config.get('data_final'), "%d-%m-%Y")

    # se for all, pegar todos os endpoints do json disponiveisEpublica.json
    if config.get('endpoint') == ["all"]:
        endpoints = disponiveis_triggers.get('endpoints_disponiveis')  # lista de todas os endpoints disponiveis
    else:
        endpoints = config.get('endpoint')  # lista de endpoints config

    # licitacao e contrato utilizam formato dd/mm/yyyy
    # outros endpoints utilizam formato mm/yyyy
    # TODO Verficar como fazer isso nas chamadas

    # se for all, pegar todas as prefeituras do json disponiveis no disponiveisEpublica.json
    if config.get('prefeituras') == ["all"]:
        prefeituras = disponiveis.get('entidades_disponiveis')  # lista de todas as prefeituras disponiveis
    else:
        prefeituras = config.get('prefeituras')  # lista de prefeituras config

    # FORMATO: https://transparencia.e-publica.net/epublica-portal/rest/ENTIDADE/api/v1/ENDPOINT
    # FORMATO: https://transparencia.e-publica.net/epublica-portal/rest/ENTIDADE/api/v1/ENDPOINT?periodo_inicial=01/01/2019&periodo_final=01/02/2019
    
    #TAMBÉM É POSSÍVEL APLICAR UM FILTRO DE UNIDADE GESTORA, COMO EXEMPLO A SEGUIR:
    #https://transparencia.e-publica.net/epublica-portal/rest/balneario_camboriu/api/v1/licitacao?periodo_inicial=01/10/2024&periodo_final=02/10/2024&codigo_unidade=1
    #CONFERIR NO PORTAL OU POR MEIO DE TESTES QUAIS SÃO AS UNIDADES GESTORAS DISPONÍVEIS, SE UM REGISTRO POSSUI MAIS DE UMA UNIDADE GESTORA RELACIONADA ELA PODERÁ ENTRAR REPETIDAS VEZES
    #EX: REG = UNIDADES GESTORAS 1,2. VAI ENTRAR NO FILTRO DO 1 E DO 2.

    api_url_inicio = "https://transparencia.e-publica.net/epublica-portal/rest/"
    api_url_fim = "/api/v1/"

    messages = []
    for pref in prefeituras:
        for endp in endpoints:
            if endp == "licitacao" or endp == "contrato":
                # formato dd/mm/yyyy
                messages.append(
                    f"{api_url_inicio}{pref}{api_url_fim}{endp}?periodo_inicial={data_inicial.strftime('%d/%m/%Y')}&periodo_final={data_final.strftime('%d/%m/%Y')}")
            else:
                # formato mm/yyyy
                messages.append(
                    f"{api_url_inicio}{pref}{api_url_fim}{endp}?periodo_inicial={data_inicial.strftime('%m/%Y')}&periodo_final={data_final.strftime('%m/%Y')}")

    return messages


if __name__ == "__main__":
    print("################## Trigger started for the flow: epublica ##################")
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
