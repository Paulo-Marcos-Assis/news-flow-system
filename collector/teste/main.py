
from datetime import datetime
import pandas as pd
import os

from service_essentials.basic_service.cached_collector_service import CachedCollectorService


class CollectorTeste(CachedCollectorService):
    service_name = "teste_collector"  # Default service name, can be overridden by environment variable
    
    def __init__(self):
        super().__init__(data_source="teste")

    def collect_data(self, message):
        
        # Get the table name from the message
        tabela = message["tabela"]
        
        # Construct the file path
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_exemplo', f"{tabela}.csv")
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file for table '{tabela}' not found at {file_path}")
        
        # Read CSV and convert to list of dictionaries (JSON-like)
        df = pd.read_csv(file_path)
        df["entity_type"] = tabela
        registros = df.to_dict(orient='records')
        
        
        return registros

    


if __name__ == '__main__':
    processor = CollectorTeste()
    processor.start()
    
