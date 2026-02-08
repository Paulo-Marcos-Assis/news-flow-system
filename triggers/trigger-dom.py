import json
import os
import sys
from calendar import monthrange
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from service_essentials.utils.logger import Logger
from service_essentials.queue_manager.queue_manager_factory import QueueManagerFactory

config_trigger = "config_dates.json"  # Nome do arquivo de configuração JSON
output_queue ="dom_collector"

# Função para corrigir datas inexistentes.

def parse_date(date_str, first_day = False, date_format="%d/%m/%Y"):
    try:
        return datetime.strptime(date_str, date_format)
    except ValueError:
        day, month, year = map(int, date_str.split('/'))

        # Se start_date não existir, ela será substituida pelo primeiro dia do mês.
        if first_day:
            return datetime(year, month, 1)
        else:
            # Se end_date não existir, ela será substituida pelo último dia do mês.

            last_day = monthrange(year, month)[1]
            day = min(day, last_day)
            return datetime(year, month, day)


# Função para gerar a lista de mensagens
def generate_messages(config_file):
    with open(config_file, 'r') as file:
        config = json.load(file)

    start_date = parse_date(config.get('start_date'), True)
    end_date = start_date if not config.get('end_date') else parse_date(config.get('end_date'))

    # throw exception start_date > end_date

    date_range = end_date - start_date
    date_list = [start_date + timedelta(days=i) for i in range(date_range.days + 1)]

    messages = []
    for date in date_list:
        messages.append({
            "api_url": "https://dados.ciga.sc.gov.br/api/3/action/package_show?id=",
            "date": f"{date.day:02d}/{date.month:02d}/{date.year}",
            "package_name": f"{'' if date.year < 2023 else 'domsc-'}publicacoes-de-{date.month:02d}-{date.year}"
        })

    return messages

# Exemplo de uso
messages = generate_messages(config_trigger)
logger = Logger(log_to_console=True)

queue_manager = QueueManagerFactory.get_queue_manager()
queue_manager.connect()
logger.info(f"Connecting to queue: {output_queue}...")
queue_manager.declare_queue(output_queue)
logger.info("...connected to queues successfully.")

# enviar mensagens de coleta para a fila
for i,message in enumerate(messages):
    logger.info(f"Sending collecting message #{i} to {output_queue}: {message}")
    queue_manager.publish_message(output_queue, json.dumps(message,indent=4))
