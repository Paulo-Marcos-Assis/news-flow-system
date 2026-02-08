
import time
import json
from datetime import datetime, timedelta
import sys
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

# 1. Setup paths to find 'service_essentials' and the JSON config
# This ensures the script works regardless of where you run it from (root or folder)
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Path to the JSON configuration file
config_trigger_path = os.path.join(base_dir, "noticias.json")
output_queue = "noticias_collector"

from service_essentials.queue_manager.queue_manager_factory import QueueManagerFactory

def generate_messages(config_file):
    """
    Reads the JSON config and prepares the messages for the queue.
    Prioritizes 'specific_date' if present; otherwise defaults to Yesterday (Day-1).
    """
    # Error handling in case file doesn't exist
    if not os.path.exists(config_file):
        print(f"ERRO: Arquivo de configuração não encontrado: {config_file}")
        sys.exit(1)

    with open(config_file, 'r') as file:
        config = json.load(file)

    portals = config.get('portals', [])
    messages = []
    
    # --- DATE LOGIC START ---
    specific_date_str = config.get('specific_date') # Reads from JSON
    
    if specific_date_str:
        try:
            # Try to parse the specific date
            date_obj = datetime.strptime(specific_date_str, '%d/%m/%Y')
            target_date_str = date_obj.strftime('%d/%m/%Y')
            print(f">>> MODO MANUAL: Usando data específica do JSON: {target_date_str}")
        except ValueError:
            # If format is wrong, fallback to yesterday
            date_obj = datetime.now() - timedelta(days=1)
            target_date_str = date_obj.strftime('%d/%m/%Y')
            print(f"AVISO: Data '{specific_date_str}' inválida. Usando Day-1: {target_date_str}")
    else:
        # Default mode (Automatic)
        date_obj = datetime.now() - timedelta(days=1)
        target_date_str = date_obj.strftime('%d/%m/%Y')
        print(f">>> MODO AUTOMÁTICO: Nenhuma data específica. Usando Day-1: {target_date_str}")
    # --- DATE LOGIC END ---

    for portal in portals:
        messages.append({
            "portal_name": portal,
            "date": target_date_str,
            "folder_path": config.get('folder_path'),
            "entity_type": config.get('entity_type'),
            "collect_all_nsc": config.get('collect_all_nsc')
        })

    return messages

# Main Execution Block
if __name__ == "__main__":
    print("--- Iniciando Trigger de Notícias ---")
    
    # 1. Generate Messages
    messages = generate_messages(config_trigger_path)
    
    if not messages:
        print("Nenhuma mensagem gerada. Verifique se 'portals' está preenchido no JSON.")
        sys.exit(0)

    # 2. Connect to RabbitMQ
    try:
        queue_manager = QueueManagerFactory.get_queue_manager()
        queue_manager.connect()
        print(f"Conectando à fila: {output_queue}...")
        queue_manager.declare_queue(output_queue)
        print("...conectado com sucesso.")

        # 3. Send Messages
        for i, message in enumerate(messages):
            print(f"Enviando mensagem #{i+1} para {output_queue}:")
            print(json.dumps(message, indent=4))
            queue_manager.publish_message(output_queue, json.dumps(message, indent=4))
            
        print("--- Envio concluído ---")
        
    except Exception as e:
        print(f"ERRO CRÍTICO ao conectar ou enviar para o RabbitMQ: {e}")
        # Hint for the user if it fails locally
        print("DICA: Se estiver rodando localmente, verifique se exportou as variáveis RABBITMQ_HOST, etc.")