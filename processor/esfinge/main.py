import importlib
import inspect
import json
import os
import traceback
from datetime import datetime, timezone

from extractors.base_extractor import BaseExtractor
from extractors.base_nested_extractor import BaseNestedExtractor
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService


class ProcessorEsfinge(BasicProducerConsumerService):

    def __init__(self):
        super().__init__()
        self.structured_data = {}
        # campos que sempre devem ir para o nível raiz
        self.ROOT_FIELDS = {'data_source', 'entity_type', 'raw_data_collection', '_id', 'raw_data_id',
                            'collect_id'}
        self.field_mappings = self._load_field_mappings()
        self._extractors = self._initialize_extractors()  # Load extractors at init

    def _initialize_extractors(self):
        """
        Loads the extractors, grouping them by scope.
        Two-pass approach: first load regular extractors, then nested extractors with extractors_by_scope.
        Returns: dict(scope -> dict(field_name -> extractor_instance))
        """
        extractors_by_scope = {}
        nested_extractor_classes = []  # Store nested extractors for second pass
        base_path = "extractors"

        # First pass: load all regular extractors
        for root, dirs, files in os.walk(base_path):
            # Skip config directory
            if 'config' in root:
                continue
            for file in files:
                if file.endswith(".py") and file not in ("__init__.py", "base_extractor.py",
                                                         "base_nested_extractor.py"):
                    # caminho relativo do módulo
                    rel_path = os.path.relpath(os.path.join(root, file), base_path)
                    module_name = rel_path.replace(os.path.sep, ".")[:-3]  # remove .py
                    try:
                        module = importlib.import_module(f"extractors.{module_name}")
                    except Exception as e:
                        self.logger.error(f"Failed to import module extractors.{module_name}: {e}")
                        continue

                    # Procura classes que herdam de BaseExtractor
                    for attr in dir(module):
                        cls = getattr(module, attr)
                        if isinstance(cls, type) and issubclass(cls, BaseExtractor) and cls not in (BaseExtractor,
                                                                                                    BaseNestedExtractor):
                            scope = getattr(cls, "scope", None) or "default"
                            field = getattr(cls, "field_name", None) or attr.lower()

                            # Check if it's a nested extractor
                            if issubclass(cls, BaseNestedExtractor):
                                nested_extractor_classes.append((scope, field, cls))
                            else:
                                extractors_by_scope.setdefault(scope, {})
                                if field in extractors_by_scope[scope]:
                                    self.logger.warning(
                                        f"Duplicate extractor for field '{field}' in scope '{scope}'. "
                                        f"Previous: {extractors_by_scope[scope][field].__class__.__name__}, "
                                        f"New: {cls.__name__}. Using new one."
                                    )
                                try:
                                    extractors_by_scope[scope][field] = cls(self.logger)
                                except Exception as e:
                                    self.logger.error(f"Failed to instantiate extractor {cls} for {scope}.{field}: {e}")

        # Second pass: instantiate nested extractors with extractors_by_scope
        for scope, field, cls in nested_extractor_classes:
            extractors_by_scope.setdefault(scope, {})
            try:
                extractors_by_scope[scope][field] = cls(self.logger, extractors_by_scope)
            except Exception as e:
                self.logger.error(f"Failed to instantiate nested extractor {cls} for {scope}.{field}: {e}")

        self.logger.info(f"Loaded extractors for scopes: {list(extractors_by_scope.keys())}")
        return extractors_by_scope

    def load_extractors(self):
        """Return cached extractors."""
        return self._extractors

    def normalize_record(self, record, current_scope=None, strict_mode=True):
        """
        Normalizes a record using our optimized scope-based approach.
        Optimized for high-volume processing of millions of records.

        Args:
            record: The record to normalize (already pre-processed to ensure consistent structure)
            extractors_by_scope: Dictionary of extractors by scope
            current_scope: Kept for interface compatibility (not used in new approach)
            strict_mode: If True, use extractors; if False, return all fields without processing

        Returns:
            dict: Normalized record with ROOT_FIELDS at the top
        """
        # For non-root levels or strict_mode=False with nested processing,
        # we assume the pre-processor already handled the structure
        if current_scope is not None:
            # If we need nested processing in non-strict mode, use simplified version
            if not strict_mode:
                return self._simple_normalize_nested(record, self._extractors, current_scope)
            else:
                # For strict mode in nested levels, return empty as extractors handle everything at root
                return {}

        # MAIN OPTIMIZED PATH - Root level processing
        if strict_mode:
            # STRICT MODE: Use our extractor-based approach (fast)
            return self._strict_mode_processing(record)
        else:
            # NON-STRICT MODE: Return all fields without extractors (fastest)
            return self._non_strict_mode_processing(record)

    def _strict_mode_processing(self, record):
        """
        Optimized strict mode processing using our scope-based extractors.
        Only processes the entity_type scope - nested extractors handle sub-scopes.
        """
        result = {}

        # 1. Add ROOT_FIELDS at the beginning
        for field in self.ROOT_FIELDS:
            if field in record:
                result[field] = record[field]

        # 2. Get the entity type to determine which scope to process
        entity_type = record.get('entity_type')
        if not entity_type:
            return result

        # 3. Only extract for the entity_type scope (e.g., processo_licitatorio)
        # Nested extractors will handle their own sub-scopes
        extractors = self._extractors.get(entity_type, {})
        if not extractors:
            self.logger.warning(f"No extractors found for entity_type: {entity_type}")
            return result

        scope_data = {}
        for field_name, extractor in extractors.items():
            try:
                extracted_value = extractor.extract(record)
                if extracted_value is not None:
                    scope_data[field_name] = extracted_value
            except Exception as e:
                self.logger.warning(f"Extractor error in {entity_type}.{field_name}: {str(e)}")

        if scope_data:
            result[entity_type] = scope_data

        return result

    def _non_strict_mode_processing(self, record):
        """
        Fast non-strict mode - returns all fields without extractor processing.
        """
        result = {}

        # 1. Add ROOT_FIELDS first
        for field in self.ROOT_FIELDS:
            if field in record:
                result[field] = record[field]

        # 2. Add all other fields (simple copy)
        for key, value in record.items():
            if key not in self.ROOT_FIELDS and value is not None:
                result[key] = value

        return result

    def _simple_normalize_nested(self, record, current_scope):
        """
        Simplified nested processing for non-strict mode only.
        Used when we have nested structures in non-strict mode.
        """
        if not isinstance(record, dict):
            return record

        result = {}

        for key, value in record.items():
            if isinstance(value, dict):
                # Recursively process nested dictionaries
                processed = self._simple_normalize_nested(value, self._extractors, key)
                if processed:
                    result[key] = processed
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # Process lists of dictionaries
                processed_list = [
                    self._simple_normalize_nested(item, self._extractors, key)
                    for item in value
                ]
                processed_list = [item for item in processed_list if item]
                if processed_list:
                    result[key] = processed_list
            elif value is not None:
                # Copy simple values
                result[key] = value

        return result if result else None

    def _send_error(self, message, error_msg, tb=None, severity="ERROR", service=None, stage=None, queue=None):
        """
        Sends an error to the error queue in standardized JSON format.
        """
        # Automatiza service e stage se não fornecidos
        if service is None or stage is None:
            frame = inspect.currentframe()
            caller_frame = inspect.getouterframes(frame, 2)[1]
            if service is None and 'self' in caller_frame.frame.f_locals:
                service = caller_frame.frame.f_locals['self'].__class__.__name__
            if stage is None:
                stage = caller_frame.function
        if queue is None:
            queue = self.error_queue
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
        self.queue_manager.publish_message(queue, json.dumps(error_payload, ensure_ascii=False))
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

    def _load_field_mappings(self):
        """
        Loads the field mappings from the configuration file.
        
        Returns:
            dict: Dictionary containing field mappings for each nested item
        """
        # Try multiple possible paths for the config file
        possible_paths = [
            # Relative to the current file
            os.path.join(os.path.dirname(__file__), 'extractors', 'config', 'field_mappings.json'),
            # Relative to the project root
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'extractors', 'config',
                         'field_mappings.json'),
            # Absolute path (as a fallback)
            '/app/processor/esfinge/extractors/config/field_mappings.json'
        ]

        for config_path in possible_paths:
            try:
                # self.logger.info(f"Trying to load field mappings from: {config_path}")
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        mappings = json.load(f)
                        # self.logger.info(f"Successfully loaded field mappings: {mappings}")
                        return mappings
                else:
                    self.logger.warning(f"Config file not found at: {config_path}")
            except Exception as e:
                self.logger.error(f"Error loading field mappings from {config_path}: {str(e)}")

        self.logger.error("Could not load field mappings from any known location")
        return {}

    def _rename_nested_fields(self, message, parent_key=None):
        """
        Recursively renames fields in nested dictionaries based on field_mappings.

        Args:
            message: The message or nested dictionary to process
            parent_key: The parent key for nested context (used internally)

        Returns:
            The processed message with renamed fields
        """
        if not isinstance(message, dict):
            return message

        result = {}
        entity_type = message.get('entity_type', parent_key)

        for key, value in message.items():
            # Get the new field name from mappings, or use original
            new_key = self.field_mappings.get(entity_type, {}).get(key, key)

            # Recursively process nested dictionaries and lists
            if isinstance(value, dict):
                result[new_key] = self._rename_nested_fields(value, entity_type)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                result[new_key] = [self._rename_nested_fields(item, key) for item in value]
            else:
                result[new_key] = value

        return result

    def _hierarchical_to_plan(self, message_data):
        """
        Transforms the input message into the desired format.
        Handles both flat and already-hierarchical input formats.

        Args:
            message_data (dict): The input message to be transformed

        Returns:
            dict: The transformed message in the desired format
        """
        if not isinstance(message_data, dict):
            raise ValueError("Input message must be a dictionary")

        # Get the entity type
        entity_type = message_data.get('entity_type')
        if not entity_type:
            raise ValueError("Input message must contain 'entity_type' field")

        # Check if input is already hierarchical (entity_type key exists as a dict)
        if entity_type in message_data and isinstance(message_data[entity_type], dict):
            # Input is already hierarchical - just return it as-is
            return message_data

        # Input is flat - transform to hierarchical format
        transformed = {}

        # Add root fields to the transformed message
        for field in self.ROOT_FIELDS:
            if field in message_data:
                transformed[field] = message_data[field]

        # Initialize the entity container
        transformed[entity_type] = {}

        # Create a list of items to process to avoid modifying dict during iteration
        items_to_process = []

        # First pass: collect items and move nested dicts to root
        for key, value in message_data.items():
            if key in self.ROOT_FIELDS or key == entity_type:
                if key == 'ente':
                    items_to_process.append((key, value))
                continue
            if isinstance(value, dict):
                # Move nested objects to root level
                transformed[key] = value
            else:
                # Collect non-dict fields to add to entity later
                items_to_process.append((key, value))

        # Second pass: add non-dict fields to entity
        for key, value in items_to_process:
            transformed[entity_type][key] = value

        return transformed

    def process_message(self, message):
        try:
            # self.logger.info(" Message received on the PROCESSOR ESFINGE ".center(84, "#"))
            # self.logger.info(message)

            # 1. Parse the message if needed
            parsed_message = self._parse_json_message(message) if not isinstance(message, dict) else message

            # 2. Convert to hierarchical format
            plan_message = self._hierarchical_to_plan(parsed_message)

            # 3. Apply field renaming to the flat message first
            renamed_message = self._rename_nested_fields(plan_message)

            # 4. Normalize the record
            normalized_record = self.normalize_record(renamed_message, strict_mode=True)

            return normalized_record

        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            self.logger.error(traceback.format_exc())
            self._send_error(message, str(e), traceback.format_exc(), severity="FAIL", queue=self.fail_queue)
            return None


if __name__ == '__main__':
    title = " Processor Esfinge Started "
    print(title.center(60, "#"))
    processor = ProcessorEsfinge()
    processor.logger.info(title.center(60, "#"))
    processor.start()
