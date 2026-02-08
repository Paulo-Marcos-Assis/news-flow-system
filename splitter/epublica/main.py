from datetime import datetime, timezone
import inspect
import os
import json

import sentry_sdk
import traceback


from dotenv import load_dotenv
from service_essentials.utils.logger import Logger
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService
from service_essentials.mongodb_ingestor.mongo_ingestor import MongoDBIngestor


class SplitterEpublica(BasicProducerConsumerService):
    def __init__(self):
        super().__init__() 
        self.mongo = MongoDBIngestor("EPUBLICA")

    def _send_error(self, message, error_msg, tb=None, severity="ERROR", service=None, stage=None):
        """
        Envia erro para a fila de erros no formato JSON padronizado.
        """
        # Automatiza service e stage se não fornecidos
        if service is None or stage is None:
            frame = inspect.currentframe()
            caller_frame = inspect.getouterframes(frame, 2)[1]
            if service is None and 'self' in caller_frame.frame.f_locals:
                service = caller_frame.frame.f_locals['self'].__class__.__name__
            if stage is None:
                stage = caller_frame.function

        timestamp_utc = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

        error_payload = {
            "timestamp": timestamp_utc,
            "service": service,
            "stage": stage,
            "severity": severity,
            "error": error_msg,
            "message": message if isinstance(message, (dict, str)) else str(message),
            # "raw_message": json.dumps(message, ensure_ascii=False) if not isinstance(message, str) else message,
            "traceback": tb
        }
        # raise ErrorQueueException(error_payload)
        self.queue_manager.publish_message(
            self.error_queue,
            json.dumps(error_payload, ensure_ascii=False))
        self.logger.error(json.dumps(error_payload, ensure_ascii=False))

    def process_message(self, message):
        title = " Splitter E-publica Started "
        self.logger.info(title.center(60, "#"))

        #SEPARA CADA REGISTRO EM UMA ÚNICA MENSAGEM
        try:
                
            dataDict = message

            registros = dataDict.get('payload', {}).get('registros',[])

            if not isinstance(registros, list) or not registros:
                    self.logger.warning("Sem dados em'payload.registros' ou não é lista. Pulando message.")
                    return None

            self.logger.info(f"Achados {len(registros)} registros to split e enviar individualmente.")

            
            for registroItem in registros:
                
                try:
                    

                    individualMessagePayload = {
                        "source": dataDict.get("source"),
                        "collection_date": dataDict.get("collection_date"),
                        "source_url": dataDict.get("source_url"),
                        "payload": registroItem  
                    }


                    #universal_id = 123456789
                    universal_id = self.mongo.ingest_json(individualMessagePayload)
                    individualMessagePayload["raw_data_id"] = str(universal_id)
                    individualMessagePayload["data_source"] = "epublica"
                    self.mongo.ingest_json(individualMessagePayload)

                    # Converte o dicionário para uma string JSON
                    atomicJsonRecord = json.dumps(individualMessagePayload, ensure_ascii=False)
                    

                    # Publica a mensagem individual na fila de saída
                    self.queue_manager.publish_message(self.output_queue, atomicJsonRecord)


                except Exception as e:
                    self._send_error(message, e)
                    self.logger.error(f"Failed to process one record: {str(e)}\n{traceback.format_exc()}")
                    continue

            self.logger.info(f"Successfully split and sent {len(registros)} records to the queue '{self.output_queue}'.")
            return None

        except json.JSONDecodeError as e:
            self._send_error(message, e)
            self.logger.error(f"Error decoding JSON: {e}\nMessage: {message[:500]}")
            return None

        except Exception as e:
            self._send_error(message, e)
            self.logger.error(f"An unexpected error occurred: {e}\n{traceback.format_exc()}")
            return None


if __name__ == '__main__':

    sentry_URL = os.getenv("URL_SENTRY")
    if sentry_URL:
        sentry_sdk.init(sentry_URL)

    logger = Logger(log_to_console=True)
    title = " Splitter E-publica Started "
    logger.info(title.center(60, "#"))
    processor = SplitterEpublica()
    processor.start()
