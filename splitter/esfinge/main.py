import inspect
import json
import traceback
from datetime import datetime, timezone

from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService
from service_essentials.mongodb_ingestor.mongo_ingestor import MongoDBIngestor


class SplitterEsfinge(BasicProducerConsumerService):
    """
    Service responsible for:
    - Receiving messages from the Collector containing lists of records.
    - Dividing the records into atomic units.
    - Inserting the raw records into MongoDB.
    - Sending each atomic unit to the processing queue (Processor).
    """

    def __init__(self):
        super().__init__()
        self.mongo = MongoDBIngestor("ESFINGE")
        self.count_atomic_record_fail = 0
        self.count_atomic_record = 0

    # ==========================================================
    #  MÉTODOS AUXILIARES
    # ==========================================================

    def _send_error(self, message, error_msg, tb=None, severity="ERROR", service=None, stage=None):
        """
        Sends an error to the error queue in standardized JSON format.
        """

        # Identifica automaticamente o service e stage de origem se não forem informados
        if service is None or stage is None:
            frame = inspect.currentframe()
            caller_frame = inspect.getouterframes(frame, 2)[1]
            if service is None and 'self' in caller_frame.frame.f_locals:
                service = caller_frame.frame.f_locals['self'].__class__.__name__
            if stage is None:
                stage = caller_frame.function

        # Timestamp padronizado UTC
        timestamp_utc = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

        error_payload = {
            "timestamp": timestamp_utc,
            "service": service,
            "stage": stage,
            "severity": severity,
            "error": error_msg,
            "message": message if isinstance(message, (dict, str)) else str(message),
            "traceback": tb
        }

        # Publica na fila de erros e loga localmente
        self.queue_manager.publish_message(self.error_queue, json.dumps(error_payload, ensure_ascii=False))
        self.logger.error(json.dumps(error_payload, ensure_ascii=False))

    # ==========================================================
    #  PROCESSAMENTO PRINCIPAL
    # ==========================================================

    def process_message(self, message):
        """
        Processes messages received from the queue:
        - Expects a list of records (datasets).
        - Each record is saved in MongoDB and sent to the Processor queue.
        """

        self.logger.info("### Message received by SPLITTER ESFINGE ###")

        try:
            # Decodifica mensagem (caso venha como bytes)
            if isinstance(message, bytes):
                message = message.decode("utf-8")

            # Garante que seja um JSON válido
            if isinstance(message, list):
                records = message
            else:
                records = json.loads(message)

            if not isinstance(records, list):
                error_msg = "Invalid message format: expected a JSON array of records."
                self._send_error(message, error_msg, traceback.format_exc())
                return None

            total_records = len(records)
            self.logger.info(f"Received {total_records} records for atomic splitting.")

            # Contadores de execução
            self.count_atomic_record_fail = 0
            self.count_atomic_record = 0

            # Processa cada registro individualmente
            for record in records:
                try:
                    # Salva no MongoDB (mantendo cópia bruta)
                    mongo_id = self.mongo.ingest_json(record)

                    # Adiciona metadados de rastreabilidade
                    record["raw_data_id"] = str(mongo_id)
                    record["data_source"] = "esfinge"

                    # Publica na fila de saída (Processor)
                    self.queue_manager.publish_message(
                        self.output_queue,
                        json.dumps(record, ensure_ascii=False)
                    )

                    self.count_atomic_record += 1
                    self.logger.debug(f"Sent atomic record to queue '{self.output_queue}' (raw_data_id={mongo_id})")

                except Exception as e:
                    self.count_atomic_record_fail += 1
                    self._send_error(record, str(e), traceback.format_exc(), severity="FAIL")
                    self.logger.error(f"Failed to process record: {str(e)}")
                    continue

            # Log de resumo
            self.logger.info(json.dumps({
                "success": True,
                "service": self.__class__.__name__,
                "processed_records": self.count_atomic_record,
                "failed_records": self.count_atomic_record_fail,
                "output_queue": self.output_queue
            }, ensure_ascii=False))

        except Exception as e:
            # Falha geral do processamento
            self._send_error(message, str(e), traceback.format_exc(), severity="FAIL")
            self.logger.error(f"General processing error: {str(e)}")

        return None


# ==========================================================
#  EXECUÇÃO DIRETA
# ==========================================================
if __name__ == '__main__':
    title = " Splitter Esfinge Started "
    print(title.center(60, "#"))
    processor = SplitterEsfinge()
    processor.logger.info(title.center(60, "#"))
    processor.start()
