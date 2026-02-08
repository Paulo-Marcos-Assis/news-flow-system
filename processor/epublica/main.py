import importlib
import inspect
import json
import os
import traceback
from datetime import datetime, timezone
from venv import logger

from extractors.base_extractor import BaseExtractor
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService


class ProcessorEpublica(BasicProducerConsumerService):
    def __init__(self):
        super().__init__()
        self.structured_data = {}

    def load_extractors(self):
        extractors = {}
        base_path = "extractors"

        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    # módulo relativo: converte caminho em formato ponto
                    rel_path = os.path.relpath(os.path.join(root, file), base_path)
                    module_name = rel_path.replace(os.path.sep, ".")[:-3]  # remove .py
                    module = importlib.import_module(f"extractors.{module_name}")

                    # Procura classes que herdam de BaseExtractor
                    for attr in dir(module):
                        cls = getattr(module, attr)
                        if isinstance(cls, type) and issubclass(cls, BaseExtractor) and cls is not BaseExtractor:
                            extractors[cls.field_name] = cls(self.logger)
        return extractors

    def _send_error(self, message, error_msg, tb=None, severity="ERROR", service=None, stage=None, queue=None):
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
        if queue is None: queue = self.error_queue
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
        self.queue_manager.publish_message(
            queue,
            json.dumps(error_payload, ensure_ascii=False))
        self.logger.error(json.dumps(error_payload, ensure_ascii=False))

    def _parse_json_message(self, message):
        if isinstance(message, bytes):
            message = message.decode("utf-8")
        if isinstance(message, str):
            return json.loads(message)
        elif isinstance(message, dict):
            return message
        else:
            raise TypeError(f"Unsupported message type: {type(message)}")


    def normalize_record(self, record, extractors):
        self.structured_data = {}

        # Aplicar todos os extratores
        for field_name, extractor in extractors.items():
            if not extractor.scope:
                continue

            try:
                extracted_value = extractor.extract(record)

                # Caso A: O extrator retorna uma LISTA (ex: documentos, unidades gestoras).
                if isinstance(extracted_value, list):
                    self.structured_data[extractor.scope] = extracted_value

                # Caso B: O extrator retorna um DICIONÁRIO (ex: campos para processo_licitatorio).
                elif isinstance(extracted_value, dict):
                    self.structured_data.setdefault(extractor.scope, {}).update(extracted_value)

                else:
                    scope_dict = self.structured_data.setdefault(extractor.scope, {})
                    
                    scope_dict[field_name] = extracted_value

            except Exception as e:
                self.logger.warning(f"Erro ao extrair {field_name}: {e}")
                self.structured_data.setdefault(extractor.scope, {})
                   
        return self.structured_data


    def process_message(self, message):
        self.logger.info("Nova mensagem Epublica recebida para processamento.")

        try:
            extractors = self.load_extractors()
            self.logger.info(f"{len(extractors)} extratores Epublica carregados.")

            full_message_data = self._parse_json_message(message)

            raw_data_id = full_message_data.get("raw_data_id")
            data_source = full_message_data.get("data_source")

            if not raw_data_id:
                self.logger.warning("Mensagem recebida sem 'raw_data_id'. Verifique o serviço anterior.")
                # return None se for crucial ter esse campo
            if not data_source:
                self.logger.warning("Mensagem recebida sem 'data_source'. Verifique o serviço anterior (splitter).")
                # return None se for crucial ter esse campo

            record_to_process = full_message_data.get("payload", {}).get("registro")
            if not record_to_process:
                self.logger.warning("Payload ou registro não encontrado na mensagem. Pulando.")
                return None

            structured_data = self.normalize_record(record_to_process, extractors)

            # # Remove chaves de nível superior que tenham valores vazios (como o `licitacao: {}`)
            # cleaned_data = {key: value for key, value in structured_data.items() if value}

            if raw_data_id: # Adiciona apenas se o ID foi encontrado
                structured_data['raw_data_id'] = raw_data_id

            if data_source:   # Adiciona apenas se o data font foi encontrado
                structured_data['data_source'] = data_source

            # Converte diretamente o dicionário de dados estruturados para JSON
            message_to_send = json.dumps(structured_data, ensure_ascii=False)
            self.queue_manager.publish_message(self.output_queue, message_to_send)
            
            self.logger.info(f"Mensagem Epublica processada e enviada para a fila: {self.output_queue}")
            return None

        except Exception as e:
            self.logger.error(f"Erro inesperado no processamento Epublica: {str(e)}")
            self._send_error(message, str(e), traceback.format_exc())
            return None


if __name__ == '__main__':
    title = " Processor Epublica Started "
    print(title.center(60, "#"))
    processor = ProcessorEpublica()
    processor.logger.info(title.center(60, "#"))
    processor.start()
