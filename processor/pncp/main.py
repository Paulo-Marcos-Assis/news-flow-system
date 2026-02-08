import importlib
import os
import logging
from typing import Any, Dict, List
from collections import defaultdict

from service_essentials.exceptions.fail_queue_exception import FailQueueException
from extractors.base_extractor import BaseExtractor, DEFAULT_VALUE
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService

# Setup logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProcessorPNCP(BasicProducerConsumerService):
    """
    A service to process raw bid data from PNCP.

    It uses a modular extractor pattern to normalize the raw data into a structured format,
    loading extractors based on a directory structure convention.
    """

    def __init__(self):
        """
        Initializes the ProcessorPNCP service.
        """
        super().__init__()
        self.extractors_by_entity, self.common_extractors = self.load_extractors()

    def load_extractors(self) -> tuple[Dict[str, List[BaseExtractor]], List[BaseExtractor]]:
        """
        Dynamically loads all extractor classes from the 'extractors' directory.
        It separates them into entity-specific and common extractors based on folder naming.
        Folders named '<entity_type>_extractors' contain entity-specific extractors.
        
        Returns:
            tuple[Dict[str, List[BaseExtractor]], List[BaseExtractor]]: 
                A tuple containing:
                - A dictionary mapping entity types to a list of their specific extractors.
                - A list of common extractors.
        """
        path = "extractors"
        entity_extractors = defaultdict(list)
        common_extractors = []

        for root, dirs, files in os.walk(path):
            # We only process directories that contain extractor python files
            if not any(f.endswith(".py") and not f.startswith("__") for f in files):
                continue

            path_parts = root.split(os.path.sep)
            # Path examples:
            # - ['extractors', 'contratacao_extractors', 'ente']
            # - ['extractors', 'documento']

            is_entity_specific = False
            is_common = False

            if len(path_parts) > 2 and path_parts[1].endswith('_extractors'):
                # This is an entity-specific extractor directory, e.g., 'extractors/contratacao_extractors/ente'
                is_entity_specific = True
                entity_type = path_parts[1].replace('_extractors', '')
                table_name = path_parts[2]
            elif len(path_parts) == 2 and not path_parts[1].endswith('_extractors'):
                # This is a common extractor directory, e.g., 'extractors/documento'
                is_common = True
                table_name = path_parts[1]
            else:
                # This is an intermediate directory like 'extractors/contratacao_extractors' or the root 'extractors'.
                # We skip processing files here and let os.walk continue to subdirectories.
                continue

            for file in files:
                if file.endswith(".py") and not file.startswith("__") and file != "base_extractor.py":
                    module_name = f"{root.replace(os.path.sep, '.')}.{file[:-3]}"
                    try:
                        module = importlib.import_module(module_name)
                        for attr in dir(module):
                            cls = getattr(module, attr)
                            if isinstance(cls, type) and issubclass(cls, BaseExtractor) and cls is not BaseExtractor:
                                instance = cls(logger, self.object_storage_manager)
                                instance.table_name = table_name
                                
                                if is_entity_specific:
                                    entity_extractors[entity_type].append(instance)
                                    logger.info(f"Successfully loaded entity extractor: {instance.field_name} for entity {entity_type}, table {table_name}")
                                elif is_common:
                                    common_extractors.append(instance)
                                    logger.info(f"Successfully loaded common extractor: {instance.field_name} for table {table_name}")
                    except Exception as e:
                        logger.error(f"Failed to load extractor from {module_name}: {e}")
        
        return dict(entity_extractors), common_extractors


    def process_message(self, message: dict[str, Any]) -> dict[str, Any]:
        """
        Processes a raw message by applying all loaded extractors for its entity_type.
        Args:
            message (dict[str, Any]): The raw message (bid data).
        Returns:
            dict[str, Any]: A dictionary containing the extracted data, grouped by table name.
        Raises:
            FailQueueException: If a critical error occurs during processing.
        """
        self.retrieve_fk_data(message)

        # Acha o objeto da mensagem para extração dos dados
        message_to_process = message
        if message.get("entity_type") == "contrato" and "contratacao" in message and isinstance(message["contratacao"], dict):
            logger.info("Contrato com 'contratacao' encontrada. Achateando os dados para extração.")
            # Achata mesclando, com as chaves da mensagem original tendo precedência
            flattened_message = {**message["contratacao"], **message}
            flattened_message.pop("contratacao", None)
            message_to_process = flattened_message
        elif message.get("entity_type") == "instrumento_cobranca" and "contrato" in message and isinstance(message["contrato"], dict):
            logger.info("Instrumento de cobrança com 'contrato' encontrado. Achateando os dados para extração.")
            # Lógica similar para achatar os dados do contrato
            flattened_message = {**message["contrato"], **message}
            flattened_message.pop("contrato", None)
            message_to_process = flattened_message

        formatted_record = {}
        raw_data_id = message_to_process.get("raw_data_id")
        data_source = message_to_process.get("data_source")
        entity_type = message_to_process.get("entity_type")

        if not raw_data_id or not data_source or not entity_type:
            raise FailQueueException("A mensagem precisa de 'raw_data_id', 'data_source', ou 'entity_type'")

        # Carrega extratores para o tipo de entidade
        active_extractors = self.extractors_by_entity.get(entity_type, [])

        # Lógica para incluir extratores de entidades pai
        if entity_type == 'contrato':
            logger.info("Tipo de entidade é 'contrato', garantindo que os extratores de 'contratacao' sejam incluídos.")
            contratacao_extractors = self.extractors_by_entity.get('contratacao', [])
            active_extractors = contratacao_extractors + active_extractors
        elif entity_type == 'instrumento_cobranca':
            logger.info("Tipo de entidade é 'instrumento_cobranca', garantindo que os extratores de 'contrato' e 'contratacao' sejam incluídos.")
            contrato_extractors = self.extractors_by_entity.get('contrato', [])
            contratacao_extractors = self.extractors_by_entity.get('contratacao', [])
            active_extractors = contratacao_extractors + contrato_extractors + active_extractors
        
        all_extractors = active_extractors + self.common_extractors
        
        if not all_extractors:
            logger.warning(f"Não foram encontrados extratores para o entity_type: {entity_type}.")

        try:
            # Agrupa extratores por nome de tabela
            extractors_by_table = defaultdict(list)
            for ext in all_extractors:
                extractors_by_table[ext.table_name].append(ext)

            # Processa todas as tabelas, exceto as de documentos
            for table_name, extractors_list in extractors_by_table.items():
                if table_name in ['documento', 'tipo_documento']:
                    continue

                if entity_type == "instrumento_cobranca" and table_name == 'item_nfe':
                    raw_items = message_to_process.get('notaFiscalEletronica', {}).get('itens', [])
                    item_nfe_records = []
                    for raw_item in raw_items:
                        item_rec = {}
                        for extractor in extractors_list:
                            extracted_value = extractor.extract(raw_item)
                            if extracted_value is not DEFAULT_VALUE:
                                item_rec[extractor.field_name] = extracted_value
                        if item_rec:
                            item_nfe_records.append(item_rec)
                    if item_nfe_records:
                        formatted_record['item_nfe'] = item_nfe_records
                    continue

                # Processamento genérico
                record = {}
                for extractor in extractors_list:
                    extracted_value = extractor.extract(message_to_process)
                    if extracted_value is not DEFAULT_VALUE:
                        record[extractor.field_name] = extracted_value
                if record:
                    formatted_record[table_name] = record
            
            # Processa tabelas de documentos
            docs = message_to_process.get('documentos', [])
            if docs:
                documento_extractors = extractors_by_table.get('documento', [])
                tipo_documento_extractors = extractors_by_table.get('tipo_documento', [])
                
                documento_records, tipo_documento_records = [], []
                for doc_item in docs:
                    doc_rec = {}
                    for extractor in documento_extractors:
                        extracted_value = extractor.extract(doc_item)
                        if extracted_value is not DEFAULT_VALUE:
                            doc_rec[extractor.field_name] = extracted_value
                    if doc_rec:
                        documento_records.append(doc_rec)

                    tipo_doc_rec = {}
                    for extractor in tipo_documento_extractors:
                        extracted_value = extractor.extract(doc_item)
                        if extracted_value is not DEFAULT_VALUE:
                            tipo_doc_rec[extractor.field_name] = extracted_value
                    if tipo_doc_rec:
                        tipo_documento_records.append(tipo_doc_rec)
                
                if documento_records:
                    formatted_record['documento'] = documento_records
                if tipo_documento_records:
                    formatted_record['tipo_documento'] = tipo_documento_records

            extracted_data = {
                "raw_data_id": raw_data_id,
                "data_source": data_source,
                "entity_type": entity_type,
                **formatted_record
            }
            return extracted_data
        
        except Exception as e:
            logger.error(f"Ocorreu um erro crítico ao processar o registro: {e}", exc_info=True)
            raise FailQueueException(f"Erro ao processar o registro: {e}")

if __name__ == '__main__':
    processor = ProcessorPNCP()
    processor.start()
