import json
from typing import List, Dict, Any, Optional
from service_essentials.mongodb_ingestor.mongo_ingestor import MongoDBIngestor


class Splitter:
    """
    Generic helper class for splitting records and publishing them to a queue.
    
    This class eliminates the need for intermediate JSON files by directly:
    1. Saving records to MongoDB
    2. Publishing them to the output queue
    
    Can be used by any collector that needs to split and process multiple records.
    """
    
    def __init__(self, data_source: str, queue_manager, output_queue: str, document_storage_manager, logger):
        """
        Initialize the Splitter.
        
        Args:
            data_source: The data source identifier (e.g., "DOM", "PNCP", etc.)
            queue_manager: The queue manager instance for publishing messages
            output_queue: The name of the output queue to publish to
            logger: Logger instance for logging operations
        """
        self.data_source = data_source
        self.queue_manager = queue_manager
        self.output_queue = output_queue
        self.logger = logger
        #self.mongo = MongoDBIngestor(data_source)
        self.document_storage_manager = document_storage_manager
    
    def split_and_publish(
        self, 
        records: List[Dict[str, Any]], 
        additional_fields: Optional[Dict[str, Any]] = None,
        collect_id: Optional[str] = None
    ) -> int:
        """
        Split records, save them to MongoDB, and publish to the output queue.
        
        Args:
            records: List of records to process
            additional_fields: Optional dictionary of fields to add to each record
            collect_id: Optional collect_id to associate with all records (for cache mechanism)
        
        Returns:
            Number of records successfully processed
        """
        processed_count = 0
        
        for i, record in enumerate(records):
            try:
                # Ingest the record into MongoDB and get the universal ID
                #print(f"Ingest do JSON")
                if collect_id:
                    record["collect_id"] = str(collect_id)

                self.logger.debug(f"Ingesting record: {record}")

                if record.get("entity_type") is not None:
                    entity_type = record["entity_type"]
                    collection = f"{self.data_source}.{entity_type}"
                else:
                    collection = self.data_source

                record["raw_data_collection"] = collection
                universal_id = self.document_storage_manager.insert_document(collection = collection, document = record)
                #print(f"JSON Ingested, universal_id: {universal_id}")
                
                # Add the raw_data_id to the record
                record["raw_data_id"] = str(universal_id)
                
                # Add the data_source to the record
                record["data_source"] = self.data_source.lower()
                #print(f"data_source: {record['data_source']}")
                
                
                
                # Add any additional fields if provided
                if additional_fields:
                    record.update(additional_fields)

                if "_id" in record:
                    record["_id"] = str(record["_id"])
                
                self.logger.info(f"Publishing record: {record}")
                # Publish the record to the output queue
                self.queue_manager.publish_message(
                    self.output_queue, 
                    json.dumps(record, ensure_ascii=False)
                )
                
                processed_count += 1
                
                # Process heartbeats every 10 records to keep connection alive
                if (i + 1) % 10 == 0:
                    if hasattr(self.queue_manager, '_process_data_events'):
                        self.queue_manager._process_data_events()
                
                if (i + 1) % 100 == 0:
                    self.logger.info(f"Processed {i + 1}/{len(records)} records")
                    
            except Exception as e:
                self.logger.error(f"Error processing record {i}: {e}")
                # Continue processing other records even if one fails
                continue
        
        self.logger.info(f"Successfully processed {processed_count}/{len(records)} records")
        return processed_count
    
    def publish_cached_records(self, cached_records: List[Dict[str, Any]]) -> int:
        """
        Publish cached records directly to the output queue without MongoDB insertion.
        
        Args:
            cached_records: List of cached records to publish
        
        Returns:
            Number of records successfully published
        """
        published_count = 0
        
        for i, record in enumerate(cached_records):
            try:
                # Publish the cached record to the output queue
                self.queue_manager.publish_message(
                    self.output_queue, 
                    json.dumps(record, ensure_ascii=False)
                )
                
                published_count += 1
                
                # Process heartbeats every 10 records to keep connection alive
                if (i + 1) % 10 == 0:
                    if hasattr(self.queue_manager, '_process_data_events'):
                        self.queue_manager._process_data_events()
                
                if (i + 1) % 100 == 0:
                    self.logger.info(f"Published {i + 1}/{len(cached_records)} cached records")
                    
            except Exception as e:
                self.logger.error(f"Error publishing cached record {i}: {e}")
                # Continue publishing other records even if one fails
                continue
        
        self.logger.info(f"Successfully published {published_count}/{len(cached_records)} cached records")
        return published_count
