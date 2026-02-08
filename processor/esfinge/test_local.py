#!/usr/bin/env python3
"""Local test script for debugging the esfinge processor."""
import sys
import json
import importlib
import os

# Add the processor path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extractors.base_extractor import BaseExtractor
from extractors.base_nested_extractor import BaseNestedExtractor

class MockLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def warning(self, msg): print(f"WARN: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")
    def debug(self, msg): print(f"DEBUG: {msg}")

ROOT_FIELDS = {'data_source', 'entity_type', 'raw_data_collection', '_id', 'raw_data_id', 'collect_id'}

def load_extractors():
    extractors_by_scope = {}
    nested_extractor_classes = []
    base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extractors")
    
    for root, dirs, files in os.walk(base_path):
        if 'config' in root:
            continue
        for file in files:
            if file.endswith(".py") and file not in ("__init__.py", "base_extractor.py", "base_nested_extractor.py"):
                rel_path = os.path.relpath(os.path.join(root, file), base_path)
                module_name = rel_path.replace(os.path.sep, ".")[:-3]
                try:
                    module = importlib.import_module(f"extractors.{module_name}")
                except Exception as e:
                    print(f"Failed to import extractors.{module_name}: {e}")
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
                            extractors_by_scope[scope][field] = cls(MockLogger())
    
    for scope, field, cls in nested_extractor_classes:
        extractors_by_scope.setdefault(scope, {})
        extractors_by_scope[scope][field] = cls(MockLogger(), extractors_by_scope)
    
    return extractors_by_scope

def hierarchical_to_plan(message_data):
    entity_type = message_data.get('entity_type')
    if not entity_type:
        raise ValueError("Input message must contain 'entity_type' field")
    
    if entity_type in message_data and isinstance(message_data[entity_type], dict):
        return message_data
    
    transformed = {}
    for field in ROOT_FIELDS:
        if field in message_data:
            transformed[field] = message_data[field]
    
    transformed[entity_type] = {}
    items_to_process = []
    
    for key, value in message_data.items():
        if key in ROOT_FIELDS or key == entity_type:
            continue
        if isinstance(value, dict):
            transformed[key] = value
        else:
            items_to_process.append((key, value))
    
    for key, value in items_to_process:
        transformed[entity_type][key] = value
    
    return transformed

def process_message(message, extractors):
    # Transform to hierarchical
    transformed = hierarchical_to_plan(message)
    
    # Process with extractors
    result = {}
    for field in ROOT_FIELDS:
        if field in transformed:
            result[field] = transformed[field]
    
    entity_type = transformed.get('entity_type')
    scope_extractors = extractors.get(entity_type, {})
    
    print(f"\nProcessing entity_type: {entity_type}")
    print(f"Available extractors: {list(scope_extractors.keys())}")
    
    scope_data = {}
    for field_name, extractor in scope_extractors.items():
        try:
            extracted_value = extractor.extract(transformed)
            if extracted_value is not None:
                scope_data[field_name] = extracted_value
                if isinstance(extracted_value, list):
                    print(f"  ✓ {field_name}: {len(extracted_value)} items")
                else:
                    print(f"  ✓ {field_name}: extracted")
        except Exception as e:
            print(f"  ✗ {field_name}: ERROR - {e}")
    
    if scope_data:
        result[entity_type] = scope_data
    
    return result

if __name__ == "__main__":
    print("Loading extractors...")
    extractors = load_extractors()
    print(f"Loaded scopes: {list(extractors.keys())}")
    
    # Test with input_1.json
    test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../test/esfinge/input_1.json")
    
    if os.path.exists(test_file):
        with open(test_file) as f:
            raw_data = json.load(f)
        
        # Simulate server message format
        message = {
            'entity_type': 'processo_licitatorio',
            'data_source': 'esfinge',
            **raw_data
        }
        
        print(f"\nInput message keys: {list(message.keys())}")
        
        result = process_message(message, extractors)
        
        print(f"\n--- RESULT ---")
        print(f"Result keys: {list(result.keys())}")
        
        pl = result.get('processo_licitatorio', {})
        print(f"processo_licitatorio fields: {list(pl.keys())}")
        
        items = pl.get('item_licitacao', [])
        print(f"\nitem_licitacao: {len(items)} items")
        if items and items[0].get('pessoa'):
            print(f"  First item has {len(items[0]['pessoa'])} pessoas")
            if items[0]['pessoa'][0].get('cotacao'):
                print(f"  First pessoa has {len(items[0]['pessoa'][0]['cotacao'])} cotacoes")
    else:
        print(f"Test file not found: {test_file}")
        print("Provide a JSON file path as argument to test")
