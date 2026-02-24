# Helpers

Generic helper classes for collectors in the data ingestion pipeline.

## Overview

This module provides two main classes:

### Splitter
Eliminates the need for intermediate JSON files by directly:
1. Saving records to MongoDB
2. Publishing them to the output queue

### CollectorCache
Provides a caching mechanism to avoid reprocessing identical messages by:
1. Checking if a message has been processed before
2. Retrieving cached records instead of reprocessing
3. Storing message configurations for future cache hits

This approach streamlines the data flow and reduces I/O operations.

## Usage

### Basic Example

```python
from service_essentials.helpers.splitter import Splitter

class YourCollector(BasicProducerConsumerService):
    def __init__(self):
        super().__init__()
        self.splitter = Splitter(
            data_source="YOUR_SOURCE",  # e.g., "DOM", "PNCP", "ESFINGE"
            queue_manager=self.queue_manager,
            output_queue=self.output_queue,
            logger=self.logger
        )
    
    def process_message(self, message):
        # ... your data collection logic ...
        records = self.collect_records()
        
        # Split and publish records directly
        processed_count = self.splitter.split_and_publish(records)
        
        self.logger.info(f"Processed {processed_count} records")
        return None
```

### With Additional Fields

You can add extra fields to each record:

```python
additional_fields = {
    "processing_date": datetime.now().isoformat(),
    "source_file": "example.json"
}

processed_count = self.splitter.split_and_publish(
    records, 
    additional_fields=additional_fields
)
```

## Features

- **Automatic MongoDB ingestion**: Each record is saved to MongoDB and assigned a `raw_data_id`
- **Direct queue publishing**: Records are published directly to the output queue without intermediate files
- **Error handling**: Continues processing even if individual records fail
- **Progress logging**: Logs progress every 100 records
- **Flexible metadata**: Support for adding custom fields to each record

## Benefits

1. **No intermediate files**: Eliminates the need to create, upload, and delete temporary JSON files
2. **Reduced I/O**: Fewer disk operations improve performance
3. **Simplified flow**: Direct path from collector to processor
4. **Reusable**: Can be used by any collector in the system
5. **Memory efficient**: Processes records one at a time

## Cache Mechanism

### How It Works

The cache mechanism uses MongoDB collections to store and retrieve processed data:

1. **Configuration Storage**: `{source}.collect_config` (e.g., `dom.collect_config`)
   - Stores the incoming message configuration
   - Used to check if identical messages have been processed before

2. **Records Storage**: `{source}` (e.g., `dom`)
   - Stores individual records with a `collect_id` field
   - The `collect_id` references the `_id` from the configuration collection

### Cache Flow

**Cache HIT** (message already processed):
```
Message arrives → Check cache → Found in collect_config → 
Retrieve records by collect_id → Publish cached records → Done
```

**Cache MISS** (new message):
```
Message arrives → Check cache → Not found → 
Process normally → Store config in collect_config (get collect_id) →
Process records with collect_id → Store in MongoDB → Publish → Done
```

### Using the Cache

```python
from service_essentials.helpers.splitter import Splitter
from service_essentials.helpers.collector_cache import CollectorCache

class YourCollector(BasicProducerConsumerService):
    def __init__(self):
        super().__init__()
        self.splitter = Splitter(
            data_source="your_source",
            queue_manager=self.queue_manager,
            output_queue=self.output_queue,
            logger=self.logger
        )
        self.cache = CollectorCache(
            data_source="your_source",
            document_storage_manager=self.document_storage_manager,
            logger=self.logger
        )
    
    def process_message(self, message):
        # Check cache first
        cache_result = self.cache.check_cache(message)
        
        if cache_result:
            # Cache HIT: Use cached records
            collect_id, cached_records = cache_result
            prepared_records = self.cache.get_cached_records_for_republish(cached_records)
            self.splitter.publish_cached_records(prepared_records)
            return None
        
        # Cache MISS: Process normally
        records = self.collect_your_data()
        
        # Store config and get collect_id
        collect_id = self.cache.store_config(message)
        
        # Process with collect_id
        self.splitter.split_and_publish(records, collect_id=collect_id)
        return None
```

### Disabling Cache

To disable caching for a specific message, add `"no_cache": true` to the message:

```json
{
    "api_url": "https://example.com",
    "date": "01/01/2024",
    "no_cache": true
}
```

## Migration from SplitterDom

The old flow:
```
Collector → JSON file → Object Storage → SplitterDom → MongoDB → Queue → Processor
```

The new flow:
```
Collector → Cache Check → Splitter → MongoDB → Queue → Processor
```

This eliminates the object storage step and the separate splitter service, while adding intelligent caching.
