from .base_extractor import BaseExtractor
import importlib
import os


class BaseNestedExtractor(BaseExtractor):
    """
    Base class for extractors that handle nested records.
    
    Subclasses should define:
        - nested_key: The key in the parent record containing the nested list
        - nested_scope: The scope name for loading extractors (folder name)
        - field_name: The output field name (usually same as nested_key)
        - scope: The parent scope this extractor belongs to
    """
    nested_key = None
    nested_scope = None
    
    def __init__(self, logger, extractors_by_scope=None):
        super().__init__(logger)
        self.extractors_by_scope = extractors_by_scope or {}
    
    def extract(self, record):
        """Extract nested records by applying child extractors to each item."""
        # Get the parent data (e.g., processo_licitatorio dict)
        parent_data = record.get(self.scope, {})
        
        # Get nested list (e.g., item_licitacao list)
        nested_items = parent_data.get(self.nested_key, [])
        
        if not nested_items or not isinstance(nested_items, list):
            return None
        
        # Get extractors for the nested scope
        nested_extractors = self.extractors_by_scope.get(self.nested_scope, {})
        
        if not nested_extractors:
            self.logger.warning(f"No extractors found for nested scope: {self.nested_scope}")
            return None
        
        results = []
        for item in nested_items:
            # Build a temporary record with the nested item as if it were the main record
            temp_record = {self.nested_scope: item}
            
            # Also include the original nested_key for extractors that reference it
            if self.nested_key != self.nested_scope:
                temp_record[self.nested_key] = item
            
            # Also include the original item for nested extractors that need deeper nesting
            for key, value in item.items():
                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                    temp_record[key] = value
            
            extracted_item = {}
            for field_name, extractor in nested_extractors.items():
                try:
                    value = extractor.extract(temp_record)
                    if value is not None:
                        extracted_item[field_name] = value
                except Exception as e:
                    self.logger.warning(f"Error extracting {field_name} from nested {self.nested_scope}: {e}")
            
            if extracted_item:
                results.append(extracted_item)
        
        return results if results else None
