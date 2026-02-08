from typing import Dict, Any, Optional, List
import copy


class CollectorCache:
    """
    Cache mechanism for collectors to avoid reprocessing identical messages.
    
    This class:
    1. Checks if a message has been processed before by querying MongoDB
    2. If found, retrieves cached records instead of reprocessing
    3. If not found, stores the message configuration for future cache hits
    
    Uses document_storage_manager to interact with:
    - {source}.collect_config: Stores message configurations
    - {source}: Stores individual records with collect_id reference
    """
    
    def __init__(self, data_source: str, document_storage_manager, logger):
        """
        Initialize the CollectorCache.
        
        Args:
            data_source: The data source identifier (e.g., "dom", "pncp", etc.)
            document_storage_manager: Document storage manager instance
            logger: Logger instance for logging operations
        """
        self.data_source = data_source.lower()
        self.document_storage_manager = document_storage_manager
        self.logger = logger
        self.config_collection = f"{self.data_source}.collect_config"
        self.records_collection = self.data_source
    
    def check_cache(self, message: Dict[str, Any]) -> Optional[tuple[str, List[Dict[str, Any]]]]:
        """
        Check if the message has been processed before.
        
        Args:
            message: The incoming message to check
        
        Returns:
            Tuple of (collect_id, cached_records) if found, None otherwise
        """
        # Skip cache lookup if no_cache=true (but data will still be stored later)
        if message.get("no_cache", False):
            self.logger.info("Cache lookup skipped for this message (no_cache=true)")
            return None
        
        # Create a query by copying the message and removing no_cache field if present
        query = copy.deepcopy(message)
        query.pop("no_cache", None)
        
        try:
            # Search for matching configuration in collect_config
            cached_config = self.document_storage_manager.find_document(
                self.config_collection,
                query
            )
            
            if cached_config:
                collect_id = cached_config.get("_id")
                self.logger.info(f"Cache HIT: Found cached configuration with collect_id={collect_id}")
                
                # Retrieve all records associated with this collect_id
                # For sources that use entity_type-based collections, we need to search across all collections
                cached_records = self._retrieve_cached_records_by_collect_id(collect_id)
                
                self.logger.info(f"Retrieved {len(cached_records)} cached records")
                return (collect_id, cached_records)
            else:
                self.logger.info("Cache MISS: No matching configuration found")
                return None
                
        except Exception as e:
            self.logger.error(f"Error checking cache: {e}")
            # On error, proceed without cache
            return None
    
    def _retrieve_cached_records_by_collect_id(self, collect_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all cached records with the given collect_id.
        
        This method searches across all collections that match the pattern:
        - {data_source} (main collection)
        - {data_source}.{entity_type} (entity-specific collections)
        
        Args:
            collect_id: The collect_id to search for
        
        Returns:
            List of all cached records with this collect_id
        """
        all_cached_records = []
        
        try:
            # Get all collections that start with data_source
            all_collections = self.document_storage_manager.list_collections()
            relevant_collections = [
                col for col in all_collections 
                if col == self.data_source or col.startswith(f"{self.data_source}.")
            ]
            
            self.logger.info(f"Searching for cached records in collections: {relevant_collections}")
            
            # Search each relevant collection for records with this collect_id
            for collection in relevant_collections:
                try:
                    records = self.document_storage_manager.find_documents(
                        collection,
                        {"collect_id": collect_id}
                    )
                    if records:
                        self.logger.info(f"Found {len(records)} cached records in collection '{collection}'")
                        all_cached_records.extend(records)
                except Exception as e:
                    self.logger.warning(f"Error searching collection '{collection}': {e}")
                    continue
            
            return all_cached_records
            
        except Exception as e:
            self.logger.error(f"Error retrieving cached records: {e}")
            return []
    
    def store_config(self, message: Dict[str, Any]) -> str:
        """
        Store the message configuration in the cache.
        
        Args:
            message: The message configuration to store
        
        Returns:
            The collect_id (MongoDB _id) of the stored configuration
        """
        # Remove no_cache field before storing
        config_to_store = copy.deepcopy(message)
        config_to_store.pop("no_cache", None)
        
        try:
            collect_id = self.document_storage_manager.insert_document(
                self.config_collection,
                config_to_store
            )
            self.logger.info(f"Stored new configuration with collect_id={collect_id}")
            return collect_id
            
        except Exception as e:
            self.logger.error(f"Error storing configuration: {e}")
            raise
    
    def get_cached_records_for_republish(
        self, 
        cached_records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Prepare cached records for republishing to the queue.
        
        This method ensures cached records have the necessary fields
        (raw_data_id, data_source, collect_id) for downstream processing.
        
        Args:
            cached_records: List of cached records from MongoDB
        
        Returns:
            List of records ready to be published
        """
        prepared_records = []
        
        for record in cached_records:
            # Ensure the record has the required fields
            if "_id" in record:
                # Use the MongoDB _id as raw_data_id if not already present
                if "raw_data_id" not in record:
                    record["raw_data_id"] = record["_id"]
            
            # Ensure data_source is present
            if "data_source" not in record:
                record["data_source"] = self.data_source
            
            prepared_records.append(record)
        
        return prepared_records
