import json
import os
from pathlib import Path
from typing import Dict, Optional, List, Any
from service_essentials.data_dependencies_manager.data_dependencies_manager import DataDependenciesManager
from service_essentials.utils.logger import Logger


class JsonDependenciesManager(DataDependenciesManager):
    """
    Implementation of DataDependenciesManager using JSON files.
    
    Loads dependency configuration from JSON files in the data_dependencies directory:
    - dependencies_temporal.json: FK relationships
    - inverted_dependencies_temporal.json: Reverse FK relationships
    - no_dependencies_atemporal.json: Static reference data
    - no_dependencies_temporal.json: Temporal reference data
    """

    def __init__(self, base_path: str = None):
        """
        Initialize the JSON dependencies manager.
        
        :param base_path: Base path to data_dependencies directory.
                         Defaults to 'data_dependencies' in current working directory.
        """
        self.logger = Logger(None, log_to_console=True)
        self.base_path = Path(base_path) if base_path else Path("data_dependencies")
        
        # Cache for loaded dependencies
        self._dependencies_cache: Dict[str, Dict] = {}
        self._inverted_dependencies_cache: Dict[str, Dict] = {}
        self._static_reference_cache: Dict[str, Dict] = {}
        self._temporal_reference_cache: Dict[str, Dict] = {}
        self._loaded_sources: set = set()

    def load_dependencies(self, source: str) -> bool:
        """
        Load dependency configuration for a specific data source.
        """
        if source in self._loaded_sources:
            self.logger.info(f"Dependencies for '{source}' already loaded")
            return True

        source_path = self.base_path / source
        
        if not source_path.exists():
            self.logger.warning(f"Dependencies directory not found for source '{source}': {source_path}")
            return False

        try:
            # Load dependencies_temporal.json
            deps_file = source_path / "dependencies_temporal.json"
            if deps_file.exists():
                with open(deps_file, 'r', encoding='utf-8') as f:
                    self._dependencies_cache[source] = json.load(f)
                self.logger.info(f"Loaded dependencies_temporal.json for '{source}'")
            else:
                self._dependencies_cache[source] = {}
                self.logger.info(f"No dependencies_temporal.json found for '{source}'")

            # Load inverted_dependencies_temporal.json
            inv_deps_file = source_path / "inverted_dependencies_temporal.json"
            if inv_deps_file.exists():
                with open(inv_deps_file, 'r', encoding='utf-8') as f:
                    self._inverted_dependencies_cache[source] = json.load(f)
                self.logger.info(f"Loaded inverted_dependencies_temporal.json for '{source}'")
            else:
                self._inverted_dependencies_cache[source] = {}
                self.logger.info(f"No inverted_dependencies_temporal.json found for '{source}'")

            # Load no_dependencies_atemporal.json
            static_file = source_path / "no_dependencies_atemporal.json"
            if static_file.exists():
                with open(static_file, 'r', encoding='utf-8') as f:
                    self._static_reference_cache[source] = json.load(f)
                self.logger.info(f"Loaded no_dependencies_atemporal.json for '{source}'")
            else:
                self._static_reference_cache[source] = {}

            # Load no_dependencies_temporal.json
            temporal_file = source_path / "no_dependencies_temporal.json"
            if temporal_file.exists():
                with open(temporal_file, 'r', encoding='utf-8') as f:
                    self._temporal_reference_cache[source] = json.load(f)
                self.logger.info(f"Loaded no_dependencies_temporal.json for '{source}'")
            else:
                self._temporal_reference_cache[source] = {}

            self._loaded_sources.add(source)
            self.logger.info(f"Successfully loaded all dependencies for '{source}'")
            return True

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error loading dependencies for '{source}': {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error loading dependencies for '{source}': {e}")
            return False

    def get_entity_dependencies(self, source: str, entity_type: str) -> Dict[str, Dict[str, str]]:
        """
        Get all FK dependencies for a specific entity.
        """
        if not self.is_loaded(source):
            self.load_dependencies(source)

        dependencies = self._dependencies_cache.get(source, {})
        entity_deps = dependencies.get(entity_type, {})
        
        if entity_deps:
            self.logger.debug(f"Found {len(entity_deps)} dependencies for '{source}.{entity_type}'")
        
        return entity_deps

    def get_dependent_entities(self, source: str, entity_type: str) -> Dict[str, Dict[str, str]]:
        """
        Get all entities that depend on this entity (inverse dependencies).
        """
        if not self.is_loaded(source):
            self.load_dependencies(source)

        inverted_deps = self._inverted_dependencies_cache.get(source, {})
        dependent_entities = inverted_deps.get(entity_type, {})
        
        if dependent_entities:
            self.logger.debug(f"Found {len(dependent_entities)} dependent entities for '{source}.{entity_type}'")
        
        return dependent_entities

    def has_dependencies(self, source: str, entity_type: str) -> bool:
        """
        Check if an entity has any FK dependencies.
        """
        entity_deps = self.get_entity_dependencies(source, entity_type)
        return len(entity_deps) > 0

    def get_all_entities(self, source: str) -> List[str]:
        """
        Get list of all entities defined for a source.
        """
        if not self.is_loaded(source):
            self.load_dependencies(source)

        entities = set()
        
        # Add entities from dependencies
        dependencies = self._dependencies_cache.get(source, {})
        entities.update(dependencies.keys())
        
        # Add entities from inverted dependencies
        inverted_deps = self._inverted_dependencies_cache.get(source, {})
        entities.update(inverted_deps.keys())
        
        # Add static reference entities
        static_refs = self._static_reference_cache.get(source, {})
        entities.update(static_refs.keys())
        
        # Add temporal reference entities
        temporal_refs = self._temporal_reference_cache.get(source, {})
        entities.update(temporal_refs.keys())
        
        return sorted(list(entities))

    def get_static_reference_entities(self, source: str) -> Dict[str, Dict[str, Any]]:
        """
        Get entities that are static reference data (no temporal dependencies).
        """
        if not self.is_loaded(source):
            self.load_dependencies(source)

        return self._static_reference_cache.get(source, {})

    def get_temporal_reference_entities(self, source: str) -> Dict[str, Dict[str, Any]]:
        """
        Get entities that are temporal reference data.
        """
        if not self.is_loaded(source):
            self.load_dependencies(source)

        return self._temporal_reference_cache.get(source, {})

    def is_loaded(self, source: str) -> bool:
        """
        Check if dependencies are loaded for a source.
        """
        return source in self._loaded_sources

    def reload_dependencies(self, source: str) -> bool:
        """
        Reload dependencies for a source (useful for updates).
        """
        # Clear cache for this source
        if source in self._loaded_sources:
            self._loaded_sources.remove(source)
        
        self._dependencies_cache.pop(source, None)
        self._inverted_dependencies_cache.pop(source, None)
        self._static_reference_cache.pop(source, None)
        self._temporal_reference_cache.pop(source, None)
        
        # Reload
        return self.load_dependencies(source)

    def get_all_entity_types(self, source: str) -> List[str]:
        """
        Get all entity types for a data source (same as get_all_entities).
        """
        return self.get_all_entities(source)

    def get_loaded_sources(self) -> List[str]:
        """
        Get list of all loaded data sources.
        """
        return sorted(list(self._loaded_sources))

    def get_dependency_info(self, source: str) -> Dict[str, Any]:
        """
        Get summary information about loaded dependencies.
        
        :param source: Data source identifier
        :return: Dictionary with dependency statistics
        """
        if not self.is_loaded(source):
            self.load_dependencies(source)

        return {
            "source": source,
            "loaded": self.is_loaded(source),
            "total_entities": len(self.get_all_entities(source)),
            "entities_with_dependencies": len(self._dependencies_cache.get(source, {})),
            "entities_with_dependents": len(self._inverted_dependencies_cache.get(source, {})),
            "static_reference_entities": len(self._static_reference_cache.get(source, {})),
            "temporal_reference_entities": len(self._temporal_reference_cache.get(source, {}))
        }
