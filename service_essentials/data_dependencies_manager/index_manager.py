from typing import Dict, List, Any, Set
import os
import json


class IndexManager:
    """
    Manages MongoDB indexes for FK resolution performance optimization.
    
    This class automatically creates indexes based on:
    1. FK dependencies configuration (from dependencies JSON files)
    2. Pendency collections (for fast pendency lookups)
    """
    
    def __init__(self, dependencies_manager, document_storage_manager, logger):
        """
        Initialize index manager.
        
        :param dependencies_manager: DataDependenciesManager instance
        :param document_storage_manager: DocumentStorageManager instance
        :param logger: Logger instance
        """
        self.dependencies_manager = dependencies_manager
        self.document_storage_manager = document_storage_manager
        self.logger = logger
        self.indexed_collections = set()  # Track which collections already have indexes
    
    def ensure_fk_indexes(self, data_source: str) -> int:
        """
        Ensure all necessary indexes exist for FK resolution in a data source.
        
        This method:
        1. Loads dependencies for the data source
        2. Creates indexes on PK fields used as FKs
        3. Creates indexes on pendency collections
        
        :param data_source: Data source name (e.g., 'esfinge', 'pncp')
        :return: Number of indexes created/ensured
        """
        if not self.dependencies_manager.is_loaded(data_source):
            loaded = self.dependencies_manager.load_dependencies(data_source)
            if not loaded:
                self.logger.info(f"No dependencies for '{data_source}', skipping index creation")
                return 0
        
        total_indexes = 0
        
        # Get all entity types for this data source
        entity_types = self.dependencies_manager.get_all_entity_types(data_source)
        
        for entity_type in entity_types:
            # Create indexes for FK lookups
            total_indexes += self._ensure_entity_indexes(data_source, entity_type)
            
            # Create indexes for pendency collections
            total_indexes += self._ensure_pendency_indexes(data_source, entity_type)
        
        self.logger.info(f"Ensured {total_indexes} indexes for data source '{data_source}'")
        return total_indexes
    
    def _ensure_entity_indexes(self, data_source: str, entity_type: str) -> int:
        """
        Create indexes on entity collections for FK lookups.
        
        For each entity, creates indexes on PK fields that are referenced by other entities.
        
        :param data_source: Data source name
        :param entity_type: Entity type name
        :return: Number of indexes created
        """
        collection_name = f"{data_source}.{entity_type}"
        
        # Skip if already indexed
        if collection_name in self.indexed_collections:
            return 0
        
        # Get dependent entities (entities that reference this one)
        dependent_entities = self.dependencies_manager.get_dependent_entities(data_source, entity_type)
        
        if not dependent_entities:
            self.logger.debug(f"No dependent entities for '{entity_type}', skipping indexes")
            return 0
        
        indexes_to_create = []
        pk_fields = set()
        
        # Collect all PK fields that are used as FKs
        for dep_entity, fk_config in dependent_entities.items():
            pk_field = fk_config.get("pk")
            if pk_field and pk_field not in pk_fields:
                pk_fields.add(pk_field)
                indexes_to_create.append({
                    'keys': [(pk_field, 1)],  # 1 = ascending
                    'name': f"idx_{pk_field}"
                })
        
        if not indexes_to_create:
            return 0
        
        try:
            created = self.document_storage_manager.ensure_indexes(collection_name, indexes_to_create)
            self.indexed_collections.add(collection_name)
            self.logger.info(f"Created {len(created)} FK lookup indexes on '{collection_name}'")
            return len(created)
        except Exception as e:
            self.logger.error(f"Failed to create indexes on '{collection_name}': {e}")
            return 0
    
    def _ensure_pendency_indexes(self, data_source: str, entity_type: str) -> int:
        """
        Create indexes on pendency collections for fast pendency lookups.
        
        Creates compound indexes for the most common queries:
        1. Finding unresolved pendencies by FK value
        2. Finding all pendencies for a raw_data_id
        
        :param data_source: Data source name
        :param entity_type: Entity type name
        :return: Number of indexes created
        """
        pendency_collection = f"{data_source}.{entity_type}.pendency"
        
        # Skip if already indexed
        if pendency_collection in self.indexed_collections:
            return 0
        
        # Define indexes for pendency collections
        indexes_to_create = [
            {
                # Compound index for finding unresolved pendencies by FK
                # Used in: resolve_pendencies() method
                'keys': [
                    ("missing_entity", 1),
                    ("missing_pk_field", 1),
                    ("fk_value", 1),
                    ("resolved", 1)
                ],
                'name': "idx_pendency_lookup"
            },
            {
                # Index for checking if all pendencies are resolved for a message
                # Used in: check_all_pendencies_resolved() method
                'keys': [
                    ("raw_data_id", 1),
                    ("resolved", 1)
                ],
                'name': "idx_pendency_status"
            },
            {
                # Index for timestamp-based queries (optional, for cleanup/monitoring)
                'keys': [("timestamp", -1)],  # -1 = descending (newest first)
                'name': "idx_pendency_timestamp"
            }
        ]
        
        try:
            created = self.document_storage_manager.ensure_indexes(pendency_collection, indexes_to_create)
            self.indexed_collections.add(pendency_collection)
            self.logger.info(f"Created {len(created)} pendency indexes on '{pendency_collection}'")
            return len(created)
        except Exception as e:
            self.logger.error(f"Failed to create pendency indexes on '{pendency_collection}': {e}")
            return 0
    
    def ensure_all_indexes(self) -> int:
        """
        Ensure indexes for all loaded data sources.
        
        :return: Total number of indexes created/ensured
        """
        total = 0
        
        # Get all loaded data sources
        loaded_sources = self.dependencies_manager.get_loaded_sources()
        
        for source in loaded_sources:
            total += self.ensure_fk_indexes(source)
        
        return total