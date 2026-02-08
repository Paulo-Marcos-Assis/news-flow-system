import sys
import os
import re
from datetime import datetime

# Import the team's base class
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService
from service_essentials.exceptions.fail_queue_exception import FailQueueException

class VerifierNoticias(BasicProducerConsumerService):
    
    def __init__(self):
        """
        Runs once when the service starts.
        """
        super().__init__()
        self.logger.info("--- STARTING NOTICIAS VERIFIER (With Regex Date Cleaning) ---")

    def normalize_date(self, date_str):
        """
        Usa Regex para extrair a primeira data válida (seja ISO ou BR)
        e a converte para YYYY-MM-DD (padrão PostgreSQL).
        """
        if not date_str:
            return None
        
        # Converte para string caso venha algum objeto estranho
        date_str = str(date_str).strip()

        # 1. Tenta achar formato ISO (ex: 2025-05-30...)
        # Procura por 4 digitos - 2 digitos - 2 digitos
        iso_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", date_str)
        if iso_match:
            # Retorna apenas a parte da data, ignorando horas ou timezones
            return iso_match.group(0)

        # 2. Tenta achar formato Brasileiro (ex: 30/05/2025...)
        # Procura por 2 digitos / 2 digitos / 4 digitos
        br_match = re.search(r"(\d{2})/(\d{2})/(\d{4})", date_str)
        if br_match:
            day, month, year = br_match.groups()
            # Remonta no formato ISO para o Banco
            return f"{year}-{month}-{day}"

        # Se não achou nenhum padrão de data conhecido, retorna None ou o original
        # Retornar o original vai causar erro no banco, o que é bom para alertar na fila de erro
        return date_str

    def process_message(self, record):
        """
        Receives the structured data from Processor.
        Validates AND Cleans data for the Quality Checker / Database.
        """
        
        # 1. Structure Validation
        if "noticia" not in record:
            raise FailQueueException("Validation Error: Missing 'noticia' key in the record structure.")

        noticia_data = record["noticia"]

        # 2. Mandatory Fields Check
        if not noticia_data.get("titulo"):
             raise FailQueueException("Validation Error: News article is missing the 'titulo' field.")
        
        # 2.1. Optional Fields Warning (link is optional but logged)
        if not noticia_data.get("link"):
            self.logger.warning(f"News article without 'link' field. ID: {record.get('raw_data_id')}")

        # 3. Data Cleaning (Robust Regex Fix)
        raw_date = noticia_data.get("data_publicacao")
        
        if raw_date:
            clean_date = self.normalize_date(raw_date)
            
            # Se mudou, loga para debug
            if clean_date != raw_date:
                self.logger.info(f"Data limpa via Regex: '{raw_date}' -> '{clean_date}'")
            
            # Atualiza o JSON com a data limpa
            noticia_data["data_publicacao"] = clean_date

        # 4. Success
        self.logger.info(f"News verified. Sending to Quality Checker. ID: {record.get('raw_data_id')}")
        return record

if __name__ == '__main__':
    verifier = VerifierNoticias()
    verifier.start()