import json
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from service_essentials.utils.logger import Logger
from service_essentials.queue_manager.queue_manager_factory import QueueManagerFactory

# Configuration
config_file = "config_teste.json"  # Nome do arquivo de configuração JSON
output_queue = "teste_collector"  # Fila de saída para o processador de teste

def load_config(config_path):
    """Carrega o arquivo de configuração JSON."""
    try:
        with open(config_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Erro: Arquivo de configuração '{config_file}' não encontrado.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Erro: O arquivo '{config_file}' não é um JSON válido.")
        sys.exit(1)

def main():
    # Carrega a configuração
    config = load_config(os.path.join(os.path.dirname(os.path.abspath(__file__)), config_file))
    
    # Verifica se a tabela foi especificada
    if "tabela" not in config:
        print("Erro: A chave 'tabela' não foi encontrada no arquivo de configuração.")
        sys.exit(1)
    
    # Cria a mensagem com o nome da tabela
    message = {"tabela": config["tabela"], "entity_type": config["tabela"]}
    
    # Configura o logger
    logger = Logger(log_to_console=True)
    
    # Conecta ao gerenciador de filas
    queue_manager = QueueManagerFactory.get_queue_manager()
    queue_manager.connect()
    
    # Declara a fila de saída
    print(f"Conectando à fila: {output_queue}...")
    queue_manager.declare_queue(output_queue)
    print("...conectado à fila com sucesso.")
    
    # Envia a mensagem para a fila
    print(f"Enviando mensagem para {output_queue}: {message}")
    queue_manager.publish_message(output_queue, json.dumps(message, indent=4))
    print("Mensagem enviada com sucesso!")

if __name__ == "__main__":
    main()
