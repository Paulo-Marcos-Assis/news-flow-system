import os
import importlib

from field_extractors.base_extractor import BaseExtractor
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService
from service_essentials.exceptions.fail_queue_exception import FailQueueException
from utils.dom_utils import DomUtils
from utils.json_to_table import JsonToTable


class ProcessorDom(BasicProducerConsumerService):

    def process_message(self, record):
        structured_record = {}

        document_fields = DomUtils.get_table_fields('documento')        
        document = self.extract_from_fields('documento', document_fields, record)
        raw_data_id = record["raw_data_id"]
        data_source = record["data_source"]

        if document:
            structured_record['documento'] = document

            document_fields_type = DomUtils.get_table_fields('tipo_documento')
            document_type_fields = self.extract_from_fields('tipo_documento', document_fields_type, record)

            if document_type_fields:
                structured_record['tipo_documento'] = document_type_fields
                
                document_type = document_type_fields.get('descricao')
                doc_table_fields = DomUtils.get_doc_table_fields(document_type)

                if doc_table_fields:

                    for table in doc_table_fields.keys():
                        json_fields = self.extract_from_fields(table, doc_table_fields.get(table), record)

                        if json_fields:
                            if table in structured_record:
                                structured_record.get(table).update(json_fields)
                            else:
                                structured_record[table] = json_fields
                        else:
                            raise FailQueueException(f"Os campos para a tabela ({table}) do documento de tipo ({document_type}) não foram extraídos.")
                else:
                    raise FailQueueException(f"Não foi definida uma lógica de processamento para um documento do tipo ({document_type}).")
            else:
                raise FailQueueException(f"Não foi possível identificar o tipo de documento deste registro.")

        else:
            raise FailQueueException(f"Não foi possível extrair informações sobre o documento deste registro.")

        result = {
            "extracted": structured_record,
            "raw": record,
            "raw_data_id": raw_data_id,
            "data_source": data_source
        }

        return result

    extract_using_model = {
        "objeto"
    }

    def extract_from_fields(self, table, fields, record):
        table_fields = {}
        extractors = self.load_field_extractors(table, fields)

        for field_name, extractor in extractors.items():
            if field_name in self.extract_using_model:
                table_fields[field_name] = extractor.extract_from_model(record)
            elif field_name in fields:
                table_fields[field_name] = extractor.extract_from_heuristic(record)

        if table == 'dynamic':
            json_table = table_fields
        else:
            json_table = JsonToTable.get_table_schema_json(table, table_fields)

        return json_table

    def load_field_extractors(self, table, fields):

        extractors = {}
        path = f"field_extractors.{table}"

        for field in fields:
            module_name = f"{path}.{field}_extractor"
            module = importlib.import_module(module_name)
            for attr in dir(module):
                cls = getattr(module, attr)
                if isinstance(cls, type) and issubclass(cls, BaseExtractor) and cls is not BaseExtractor:
                    extractors[cls.field] = cls(self.logger)
                    
                    if hasattr(self, 'object_storage_manager'):
                        extractors[cls.field].object_storage_manager = self.object_storage_manager

        return extractors

if __name__ == '__main__':
    processor = ProcessorDom()
    processor.start()