#!/usr/bin/env python3
"""
Auxiliary script to apply processor logic to all individual input messages.
Generates outputs in individual_outputs folder maintaining the date structure.

Usage:
    cd /home/jonata/ceos/main-server
    python test/esfinge/run_processor.py
"""

import json
import os
import sys

# Add project root to path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'processor', 'esfinge'))

# Mock environment variables before importing processor
os.environ.setdefault('INPUT_QUEUE', 'test_input')
os.environ.setdefault('OUTPUT_QUEUE', 'test_output')
os.environ.setdefault('QUEUE_MANAGER', 'mock')
os.environ.setdefault('DOCUMENT_STORAGE_MANAGER', 'mock')


class MockLogger:
    """Simple mock logger for testing"""
    def info(self, msg): print(f"[INFO] {msg}")
    def warning(self, msg): print(f"[WARN] {msg}")
    def error(self, msg): print(f"[ERROR] {msg}")
    def debug(self, msg): pass


def create_processor_for_testing():
    """
    Create a processor instance configured for testing (no queue connections).
    """
    import importlib
    from processor.esfinge.extractors.base_extractor import BaseExtractor
    from processor.esfinge.extractors.base_nested_extractor import BaseNestedExtractor
    
    class TestableProcessor:
        def __init__(self):
            self.logger = MockLogger()
            self.ROOT_FIELDS = {'data_source', 'entity_type', 'raw_data_collection', '_id', 'raw_data_id', 'collect_id'}
            self.field_mappings = self._load_field_mappings()
            self._extractors = self._initialize_extractors()
        
        def _load_field_mappings(self):
            """Load field mappings from config file."""
            config_path = os.path.join(PROJECT_ROOT, 'processor', 'esfinge', 'extractors', 'config', 'field_mappings.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        
        def _initialize_extractors(self):
            """Initialize extractors."""
            extractors_by_scope = {}
            nested_extractor_classes = []
            base_path = os.path.join(PROJECT_ROOT, 'processor', 'esfinge', 'extractors')
            
            for root, dirs, files in os.walk(base_path):
                if 'config' in root:
                    continue
                for file in files:
                    if file.endswith(".py") and file not in ("__init__.py", "base_extractor.py", "base_nested_extractor.py"):
                        rel_path = os.path.relpath(os.path.join(root, file), base_path)
                        module_name = rel_path.replace(os.path.sep, ".")[:-3]
                        try:
                            module = importlib.import_module(f"processor.esfinge.extractors.{module_name}")
                        except Exception as e:
                            self.logger.error(f"Failed to import module: {e}")
                            continue
                        
                        for attr in dir(module):
                            cls = getattr(module, attr)
                            if isinstance(cls, type) and issubclass(cls, BaseExtractor) and cls not in (BaseExtractor, BaseNestedExtractor):
                                scope = getattr(cls, "scope", None) or "default"
                                field = getattr(cls, "field_name", None) or attr.lower()
                                
                                if issubclass(cls, BaseNestedExtractor):
                                    nested_extractor_classes.append((scope, field, cls))
                                else:
                                    extractors_by_scope.setdefault(scope, {})
                                    try:
                                        extractors_by_scope[scope][field] = cls(self.logger)
                                    except Exception as e:
                                        self.logger.error(f"Failed to instantiate extractor {cls}: {e}")
            
            # Second pass: nested extractors
            for scope, field, cls in nested_extractor_classes:
                extractors_by_scope.setdefault(scope, {})
                try:
                    extractors_by_scope[scope][field] = cls(self.logger, extractors_by_scope)
                except Exception as e:
                    self.logger.error(f"Failed to instantiate nested extractor {cls}: {e}")
            
            self.logger.info(f"Loaded extractors for scopes: {list(extractors_by_scope.keys())}")
            return extractors_by_scope
        
        def process_message(self, message):
            """Process a message using the processor logic."""
            if isinstance(message, str):
                message = json.loads(message)
            
            # Infer entity_type if not present
            if 'entity_type' not in message:
                # Find the main entity key (processo_licitatorio, empenho, etc.)
                for key in message.keys():
                    if key not in self.ROOT_FIELDS and isinstance(message[key], dict):
                        message['entity_type'] = key
                        break
            
            # Add data_source if not present
            if 'data_source' not in message:
                message['data_source'] = 'esfinge'
            
            plan_message = self._hierarchical_to_plan(message)
            renamed_message = self._rename_nested_fields(plan_message)
            normalized_record = self.normalize_record(renamed_message, strict_mode=True)
            
            return normalized_record
        
        def _hierarchical_to_plan(self, message_data):
            """Transform input message into hierarchical format."""
            if not isinstance(message_data, dict):
                raise ValueError("Input message must be a dictionary")
            
            entity_type = message_data.get('entity_type')
            if not entity_type:
                raise ValueError("Input message must contain 'entity_type' field")
            
            if entity_type in message_data and isinstance(message_data[entity_type], dict):
                return message_data
            
            transformed = {}
            for field in self.ROOT_FIELDS:
                if field in message_data:
                    transformed[field] = message_data[field]
            
            transformed[entity_type] = {}
            items_to_process = []
            
            for key, value in message_data.items():
                if key in self.ROOT_FIELDS or key == entity_type:
                    if key == 'ente':
                        items_to_process.append((key, value))
                    continue
                if isinstance(value, dict):
                    transformed[key] = value
                else:
                    items_to_process.append((key, value))
            
            for key, value in items_to_process:
                transformed[entity_type][key] = value
            
            return transformed
        
        def _rename_nested_fields(self, message, parent_key=None):
            """Recursively rename fields based on field_mappings."""
            if not isinstance(message, dict):
                return message
            
            result = {}
            entity_type = message.get('entity_type', parent_key)
            
            for key, value in message.items():
                new_key = self.field_mappings.get(entity_type, {}).get(key, key)
                
                if isinstance(value, dict):
                    result[new_key] = self._rename_nested_fields(value, entity_type)
                elif isinstance(value, list) and value and isinstance(value[0], dict):
                    result[new_key] = [self._rename_nested_fields(item, key) for item in value]
                else:
                    result[new_key] = value
            
            return result
        
        def normalize_record(self, record, current_scope=None, strict_mode=True):
            """Normalize a record using extractors."""
            if current_scope is not None:
                return {}
            
            if strict_mode:
                return self._strict_mode_processing(record)
            else:
                return self._non_strict_mode_processing(record)
        
        def _strict_mode_processing(self, record):
            """Process using extractors."""
            result = {}
            
            for field in self.ROOT_FIELDS:
                if field in record:
                    result[field] = record[field]
            
            entity_type = record.get('entity_type')
            if not entity_type:
                return result
            
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
            """Return all fields without extractor processing."""
            result = {}
            
            for field in self.ROOT_FIELDS:
                if field in record:
                    result[field] = record[field]
            
            for key, value in record.items():
                if key not in self.ROOT_FIELDS and value is not None:
                    result[key] = value
            
            return result
    
    return TestableProcessor()


def process_all_inputs():
    """Process all individual input files and generate outputs."""
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, 'individual_inputs')
    output_dir = os.path.join(base_dir, 'individual_outputs')
    
    if not os.path.exists(input_dir):
        print(f"Error: Input directory not found: {input_dir}")
        return
    
    print("Initializing TestableProcessor...")
    processor = create_processor_for_testing()
    
    stats = {'processed': 0, 'errors': 0, 'by_date': {}}
    
    # Process each date folder
    for date_folder in sorted(os.listdir(input_dir)):
        date_path = os.path.join(input_dir, date_folder)
        if not os.path.isdir(date_path):
            continue
        
        # Create corresponding output folder
        output_date_path = os.path.join(output_dir, date_folder)
        os.makedirs(output_date_path, exist_ok=True)
        
        stats['by_date'][date_folder] = {'processed': 0, 'errors': 0}
        
        print(f"\nProcessing {date_folder}/")
        
        # Process each input file in this date folder
        for filename in sorted(os.listdir(date_path)):
            if not filename.endswith('.json'):
                continue
            
            input_filepath = os.path.join(date_path, filename)
            output_filepath = os.path.join(output_date_path, filename)
            
            try:
                # Read input
                with open(input_filepath, 'r', encoding='utf-8') as f:
                    input_data = json.load(f)
                
                # Process message
                output_data = processor.process_message(input_data)
                
                # Write output
                with open(output_filepath, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, ensure_ascii=False, indent=2)
                
                stats['processed'] += 1
                stats['by_date'][date_folder]['processed'] += 1
                print(f"  ✓ {filename}")
                
            except Exception as e:
                stats['errors'] += 1
                stats['by_date'][date_folder]['errors'] += 1
                print(f"  ✗ {filename}: {e}")
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total processed: {stats['processed']}")
    print(f"Total errors: {stats['errors']}")
    print("\nBy date:")
    for date, counts in sorted(stats['by_date'].items()):
        print(f"  {date}: {counts['processed']} processed, {counts['errors']} errors")


if __name__ == '__main__':
    process_all_inputs()
