# CachedCollectorService

An abstract base class that extends `BasicProducerConsumerService` to provide transparent caching and splitting mechanisms for collectors.

## Overview

`CachedCollectorService` automatically handles:
- **Caching**: Avoids reprocessing identical messages
- **Splitting**: Processes and publishes records to MongoDB and queues
- **Configuration**: Automatically initializes splitter and cache components

Developers can focus on implementing the data collection logic while the caching and splitting mechanisms work transparently in the background.

## Key Features

- ✅ **Transparent Setup**: Splitter and cache are automatically initialized
- ✅ **Simple Helper Methods**: Easy-to-use methods for cache and publishing operations
- ✅ **Flexible**: Developers maintain full control over `process_message()`
- ✅ **Reusable**: Can be extended by any collector (DOM, PNCP, ESFINGE, etc.)

## Usage

### Basic Implementation

```python
from service_essentials.basic_service.cached_collector_service import CachedCollectorService

class YourCollector(CachedCollectorService):
    def __init__(self):
        # Just specify your data source
        super().__init__(data_source="your_source")
    
    def process_message(self, message):
        # Check cache and publish if found
        if self.check_cache_and_publish(message):
            return None
        
        # Cache miss - collect your data
        records = self.collect_your_data(message)
        
        # Store config and publish records with collect_id
        collect_id, count = self.store_and_publish_records(message, records)
        
        self.logger.info(f"Processed {count} records with collect_id={collect_id}")
        return None
    
    def collect_your_data(self, message):
        # Your custom data collection logic
        return [...]
```

### Real Example: CollectorDom

```python
from service_essentials.basic_service.cached_collector_service import CachedCollectorService

class CollectorDom(CachedCollectorService):
    def __init__(self):
        super().__init__(data_source="dom")

    def process_message(self, message):
        # Check cache and publish if found
        if self.check_cache_and_publish(message):
            return None
        
        # Cache miss - process normally
        api_url = message["api_url"]
        date = message["date"]
        package_name = message["package_name"]
        
        dados_base = self.realizar_requisicao_base(api_url + package_name)
        registros_data_especifica = self.filtrar_registros_para_data(dados_base, date)
        arquivos_baixados = self.realizar_download_arquivos_zip(registros_data_especifica)
        diretorio_temp = self.extrair_arquivos_zip(arquivos_baixados)
        registros = self.ler_jsons_e_listar_licitacoes(diretorio_temp)
        
        # Store config and publish records with collect_id
        collect_id, processed_count = self.store_and_publish_records(message, registros)
        
        self.logger.info(f"Processed {processed_count} records from {date} with collect_id={collect_id}")
        
        # Clean up temporary files
        self.apagar_arquivos_temp(arquivos_baixados)
        self.apagar_diretorio_temp(diretorio_temp)
        
        return None
```

## Helper Methods

### 1. `check_cache_and_publish(message)`

Checks if the message has been processed before and publishes cached records if found.

**Returns:**
- `Tuple[str, int]` (collect_id, published_count) if cache hit
- `None` if cache miss

**Example:**
```python
cache_result = self.check_cache_and_publish(message)
if cache_result:
    collect_id, count = cache_result
    self.logger.info(f"Used cache: {count} records")
    return None
# Continue with normal processing
```

### 2. `store_and_publish_records(message, records, additional_fields=None)`

Stores the message configuration in cache and publishes records with the collect_id.

**Parameters:**
- `message`: The incoming message to store in cache
- `records`: List of records to process and publish
- `additional_fields`: Optional fields to add to each record

**Returns:**
- `Tuple[str, int]` (collect_id, processed_count)

**Example:**
```python
records = self.collect_data()
collect_id, count = self.store_and_publish_records(message, records)
self.logger.info(f"Processed {count} records")
```

### 3. `publish_records_without_cache(records, additional_fields=None)`

Publishes records without using the cache mechanism (no collect_id).

**Parameters:**
- `records`: List of records to process and publish
- `additional_fields`: Optional fields to add to each record

**Returns:**
- `int` (processed_count)

**Example:**
```python
# For messages with no_cache=true or when you want to bypass cache
records = self.collect_data()
count = self.publish_records_without_cache(records)
```

## Automatic Components

When you extend `CachedCollectorService`, you automatically get:

### `self.splitter`
A `Splitter` instance configured for your data source that:
- Saves records to MongoDB
- Publishes records to the output queue
- Handles errors gracefully

### `self.cache`
A `CollectorCache` instance that:
- Checks for cached configurations in `{source}.collect_config`
- Retrieves cached records from `{source}` collection
- Stores new configurations with collect_id

### `self.data_source`
The data source identifier (lowercase) used for:
- MongoDB collection names
- Logging
- Cache keys

## Benefits Over Manual Implementation

**Before (Manual):**
```python
class CollectorDom(BasicProducerConsumerService):
    def __init__(self):
        super().__init__()
        # Manual initialization
        self.splitter = Splitter(...)
        self.cache = CollectorCache(...)
    
    def process_message(self, message):
        # Manual cache check
        cache_result = self.cache.check_cache(message)
        if cache_result:
            collect_id, cached_records = cache_result
            prepared = self.cache.get_cached_records_for_republish(cached_records)
            self.splitter.publish_cached_records(prepared)
            return None
        
        # Manual processing
        records = self.collect_data()
        collect_id = self.cache.store_config(message)
        self.splitter.split_and_publish(records, collect_id=collect_id)
        return None
```

**After (With CachedCollectorService):**
```python
class CollectorDom(CachedCollectorService):
    def __init__(self):
        super().__init__(data_source="dom")
    
    def process_message(self, message):
        # Simple one-liner for cache
        if self.check_cache_and_publish(message):
            return None
        
        # Collect data
        records = self.collect_data()
        
        # Simple one-liner for publishing
        self.store_and_publish_records(message, records)
        return None
```

## Migration Guide

To migrate an existing collector:

1. **Change parent class:**
   ```python
   # Before
   class YourCollector(BasicProducerConsumerService):
   
   # After
   class YourCollector(CachedCollectorService):
   ```

2. **Update `__init__`:**
   ```python
   # Before
   def __init__(self):
       super().__init__()
       self.splitter = Splitter(...)
       self.cache = CollectorCache(...)
   
   # After
   def __init__(self):
       super().__init__(data_source="your_source")
   ```

3. **Simplify `process_message`:**
   ```python
   # Replace manual cache checks with
   if self.check_cache_and_publish(message):
       return None
   
   # Replace manual store and publish with
   self.store_and_publish_records(message, records)
   ```

## Advanced Usage

### With Additional Fields

```python
additional_fields = {
    "processing_timestamp": datetime.now().isoformat(),
    "collector_version": "2.0"
}

collect_id, count = self.store_and_publish_records(
    message, 
    records,
    additional_fields=additional_fields
)
```

### Bypassing Cache for Specific Messages

The cache automatically respects the `no_cache` flag:

```json
{
    "api_url": "https://example.com",
    "date": "01/01/2024",
    "no_cache": true
}
```

When `no_cache: true` is present, `check_cache_and_publish()` will return `None` (cache miss).

## See Also

- [Splitter Documentation](../helpers/README.md)
- [CollectorCache Documentation](../helpers/collector_cache.py)
- [BasicProducerConsumerService](./basic_producer_consumer_service.py)
