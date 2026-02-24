from abc import abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService
from service_essentials.helpers.splitter import Splitter
from service_essentials.helpers.collector_cache import CollectorCache


class CachedCollectorService(BasicProducerConsumerService):
    """
    Abstract base class for collectors with built-in caching and splitting mechanisms.
    
    This class extends BasicProducerConsumerService and automatically provides:
    - Splitter: For processing and publishing records
    - CollectorCache: For caching message configurations and avoiding reprocessing
    - Complete process_message implementation with cache handling
    
    Developers only need to:
    1. Specify the data_source in __init__
    2. Implement collect_data(message) to return a list of records
    
    The caching, splitting, and publishing mechanisms are completely transparent.
    """
    
    def __init__(self, data_source: str, use_cache: bool = True):
        """
        Initialize the cached collector service.
        
        Args:
            data_source: The data source identifier (e.g., "dom", "pncp", "esfinge")
            use_cache: Whether to enable caching mechanism (default: True)
        """
        super().__init__()
        
        self.data_source = data_source.lower()
        self.use_cache = use_cache
        
        # Initialize splitter
        self.splitter = Splitter(
            data_source=self.data_source,
            queue_manager=self.queue_manager,
            output_queue=self.output_queue,
            document_storage_manager=self.document_storage_manager,
            logger=self.logger
        )
        
        # Initialize cache (only if enabled)
        if self.use_cache:
            self.cache = CollectorCache(
                data_source=self.data_source,
                document_storage_manager=self.document_storage_manager,
                logger=self.logger
            )
        else:
            self.cache = None
            self.logger.info(f"Cache mechanism disabled for {self.data_source}")
    
    def process_message(self, message: Dict[str, Any]) -> None:
        """
        Process an incoming message with automatic caching (if enabled).
        
        This method:
        1. Checks if the message has been processed before (cache check) - if cache enabled
        2. If cached, republishes the cached records
        3. If not cached, calls collect_data() and processes normally
        
        Args:
            message: The incoming message to process
        
        Returns:
            None (records are published to the output queue)
        """
        self.use_cache = message.get("use_cache", True)
        # Check cache and publish if found (only if cache is enabled)
        if self.use_cache:
            self.logger.info(f"DEBUG cache_result message: {message}")
            cache_result = self.check_cache_and_publish(message)
            
            if cache_result:
                return None
            
            # Cache miss - collect data
            self.logger.info("Cache MISS: Collecting data")
        else:
            self.logger.info("Cache disabled: Collecting data")
        
        records = self.collect_data(message)
        
        if not records:
            self.logger.warning("No records collected")
            return None
        
        # Store config and publish records (with or without cache)
        if self.use_cache:
            collect_id, processed_count = self.store_and_publish_records(message, records)
            self.logger.info(f"Processed {processed_count} records with collect_id={collect_id}")
        else:
            processed_count = self.publish_records_without_cache(records)
            self.logger.info(f"Processed {processed_count} records (cache disabled)")
        
        return None
    
    @abstractmethod
    def collect_data(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Collect and return records based on the incoming message.
        
        This is the only method that subclasses must implement.
        
        Args:
            message: The incoming message containing collection parameters
        
        Returns:
            List of records (as dictionaries) to be processed and published
        
        Example:
            def collect_data(self, message):
                api_url = message["api_url"]
                data = self.fetch_from_api(api_url)
                records = self.parse_data(data)
                return records
        """
        pass
    
    # Helper methods (can be used by subclasses if they override process_message)
    
    def check_cache_and_publish(self, message: Dict[str, Any]) -> Optional[Tuple[str, int]]:
        """
        Check cache and publish cached records if found.
        
        This is a helper method that:
        1. Checks if the message has been processed before
        2. If found, publishes the cached records
        3. Returns cache information or None
        
        Note: Returns None immediately if cache is disabled.
        
        Args:
            message: The incoming message to check
        
        Returns:
            Tuple of (collect_id, published_count) if cache hit, None if cache miss or disabled
        
        Example:
            cache_result = self.check_cache_and_publish(message)
            if cache_result:
                # Cache hit - records already published
                return None
            # Cache miss - continue with normal processing
        """
        # Return None if cache is disabled
        if not self.use_cache or self.cache is None:
            return None
        
        cache_result = self.cache.check_cache(message)
        
        if cache_result:
            # Cache HIT: Use cached records
            collect_id, cached_records = cache_result
            self.logger.info(f"Cache HIT: Using cached data with collect_id={collect_id}")
            
            # Prepare and publish cached records
            prepared_records = self.cache.get_cached_records_for_republish(cached_records)
            published_count = self.splitter.publish_cached_records(prepared_records)
            
            self.logger.info(f"Published {published_count} cached records from collect_id={collect_id}")
            return (collect_id, published_count)
        
        # Cache MISS
        self.logger.info("Cache MISS: Processing message normally")
        return None
    
    def store_and_publish_records(
        self, 
        message: Dict[str, Any], 
        records: List[Dict[str, Any]],
        additional_fields: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, int]:
        """
        Store message config in cache and publish records with collect_id.
        
        This is a helper method that:
        1. Stores the message configuration in cache
        2. Gets the collect_id
        3. Processes and publishes records with the collect_id
        
        Note: If cache is disabled, this method will raise an error.
        Use publish_records_without_cache() instead when cache is disabled.
        
        Args:
            message: The incoming message to store in cache
            records: List of records to process and publish
            additional_fields: Optional fields to add to each record
        
        Returns:
            Tuple of (collect_id, processed_count)
        
        Raises:
            RuntimeError: If cache is disabled
        
        Example:
            records = self.collect_your_data()
            collect_id, count = self.store_and_publish_records(message, records)
            self.logger.info(f"Processed {count} records with collect_id={collect_id}")
        """
        if not self.use_cache or self.cache is None:
            raise RuntimeError(
                "Cannot use store_and_publish_records() when cache is disabled. "
                "Use publish_records_without_cache() instead."
            )
        
        # Store configuration in cache and get collect_id
        collect_id = self.cache.store_config(message)
        
        # Use the Splitter to process records with collect_id
        processed_count = self.splitter.split_and_publish(
            records, 
            additional_fields=additional_fields,
            collect_id=collect_id
        )
        
        self.logger.info(f"Processed {processed_count} records with collect_id={collect_id}")
        return (collect_id, processed_count)
    
    def publish_records_without_cache(
        self,
        records: List[Dict[str, Any]],
        additional_fields: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Publish records without using cache (no collect_id).
        
        This is useful when you want to bypass the cache mechanism.
        
        Args:
            records: List of records to process and publish
            additional_fields: Optional fields to add to each record
        
        Returns:
            Number of records processed
        
        Example:
            records = self.collect_your_data()
            count = self.publish_records_without_cache(records)
        """
        processed_count = self.splitter.split_and_publish(
            records,
            additional_fields=additional_fields
        )
        
        self.logger.info(f"Processed {processed_count} records without cache")
        return processed_count