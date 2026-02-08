# Document Storage Manager

## Overview

The Document Storage Manager provides a unified interface for interacting with NoSQL document databases in the CEOS data ingestion system. It follows the same factory pattern used by the Object Storage Manager and Queue Manager.

## Architecture

```
DocumentStorageManager (Abstract Base Class)
    ├── MongoDBManager (MongoDB Implementation)
    └── [Future implementations: CouchDB, etc.]

DocumentStorageManagerFactory
    └── Creates appropriate manager based on environment variable
```

## Features

- **Dependency Injection**: Automatically instantiated in `BasicProducerConsumerService`
- **Factory Pattern**: Easy to switch between different document storage implementations
- **Environment-based Configuration**: All connection parameters from environment variables
- **Comprehensive CRUD Operations**: Insert, find, update, delete operations
- **Collection Management**: Check existence, count documents
- **Batch Operations**: Support for bulk inserts, updates, and deletes

## Configuration

Add to `.env`:

```bash
# Document Storage Manager Type
DOCUMENT_STORAGE_MANAGER=mongodb

# MongoDB Configuration
USERNAME_MONGODB=ceos
SENHA_MONGODB=ceosMongodb
DATABASE_AUTENTICACAO_MONGODB=admin
DATABASE_MONGODB=test_database
HOST_MONGODB=dbs.ceos.ufsc.br
PORT_MONGODB=2717
```

## Usage in Microservices

The document storage manager is automatically available in all services that extend `BasicProducerConsumerService`:

```python
class MyService(BasicProducerConsumerService):
    def process_message(self, message):
        # Access document storage manager
        doc_id = self.document_storage_manager.insert_document(
            "my_collection",
            {"key": "value"}
        )
        
        # Find documents
        docs = self.document_storage_manager.find_documents(
            "my_collection",
            {"key": "value"}
        )
        
        return result
```

## API Reference

### Insert Operations

```python
# Insert single document
doc_id = manager.insert_document("collection_name", {"field": "value"})

# Insert multiple documents
doc_ids = manager.insert_many_documents("collection_name", [
    {"field": "value1"},
    {"field": "value2"}
])
```

### Find Operations

```python
# Find single document
doc = manager.find_document("collection_name", {"field": "value"})

# Find multiple documents with limit
docs = manager.find_documents("collection_name", {"field": "value"}, limit=10)

# Find all documents (no limit)
docs = manager.find_documents("collection_name", {})
```

### Update Operations

```python
# Update single document
count = manager.update_document(
    "collection_name",
    {"field": "value"},  # query
    {"field": "new_value"}  # update
)

# Update multiple documents
count = manager.update_many_documents(
    "collection_name",
    {"status": "pending"},
    {"status": "processed"}
)

# Using MongoDB operators
count = manager.update_document(
    "collection_name",
    {"_id": "123"},
    {"$set": {"field": "value"}, "$inc": {"counter": 1}}
)
```

### Delete Operations

```python
# Delete single document
count = manager.delete_document("collection_name", {"field": "value"})

# Delete multiple documents
count = manager.delete_many_documents("collection_name", {"status": "old"})
```

### Utility Operations

```python
# Count documents
count = manager.count_documents("collection_name", {"status": "active"})

# Check if collection exists
exists = manager.collection_exists("collection_name")

# Close connection
manager.close_connection()
```

## Use Cases in CEOS

### 1. Foreign Key Resolution with Pendencies

Store records that are waiting for foreign key data:

```python
# Store pendency when FK data is not available
pendency = {
    "source": "PNCP",
    "entity": "processo_licitatorio",
    "missing_fk": "id_ente",
    "fk_identifier": {"cnpj": "12345678000190"},
    "original_message": message,
    "timestamp": datetime.now().isoformat()
}
self.document_storage_manager.insert_document(
    "pncp.processo_licitatorio.pendency",
    pendency
)

# Later, retrieve and resolve pendencies
pendencies = self.document_storage_manager.find_documents(
    "pncp.processo_licitatorio.pendency",
    {"missing_fk": "id_ente", "fk_identifier.cnpj": cnpj}
)
```

### 2. Caching Lookup Data

Cache frequently accessed reference data:

```python
# Cache tipo_pessoa lookup
cached = self.document_storage_manager.find_document(
    "cache.tipo_pessoa",
    {"codigo": "1"}
)

if not cached:
    # Load from CSV and cache
    data = load_from_csv()
    self.document_storage_manager.insert_document("cache.tipo_pessoa", data)
```

### 3. Audit Trail

Store processing history:

```python
audit = {
    "service": self.service_name,
    "message_id": message["raw_data_id"],
    "action": "processed",
    "timestamp": datetime.now().isoformat(),
    "details": {"status": "success"}
}
self.document_storage_manager.insert_document("audit_trail", audit)
```

## MongoDB-Specific Features

### Query Operators

The MongoDB implementation supports all MongoDB query operators:

```python
# Comparison operators
docs = manager.find_documents("collection", {"age": {"$gte": 18, "$lte": 65}})

# Logical operators
docs = manager.find_documents("collection", {
    "$or": [{"status": "active"}, {"status": "pending"}]
})

# Array operators
docs = manager.find_documents("collection", {"tags": {"$in": ["urgent", "important"]}})
```

### Automatic ObjectId Conversion

The MongoDB manager automatically converts ObjectId to string for JSON serialization:

```python
doc = manager.find_document("collection", {"field": "value"})
# doc['_id'] is already a string, not ObjectId
```

## Adding New Implementations

To add support for another document database:

1. Create a new manager class extending `DocumentStorageManager`
2. Implement all abstract methods
3. Update `DocumentStorageManagerFactory` to support the new type

Example:

```python
# couchdb_manager.py
class CouchDBManager(DocumentStorageManager):
    def connect(self, ...):
        # Implementation
        pass
    # ... implement other methods

# document_storage_manager_factory.py
if document_storage_type == "couchdb":
    from service_essentials.document_storage_manager.couchdb_manager import CouchDBManager
    return CouchDBManager()
```

## Testing

See `example_usage.py` for a complete example demonstrating all features.

## Integration with retrieve_fk_data

The document storage manager is designed to work with the `retrieve_fk_data` method in `BasicProducerConsumerService`:

```python
def retrieve_fk_data(self, message):
    # Use document_storage_manager to:
    # 1. Load FK dependencies from data_dependencies/
    # 2. Query for FK data
    # 3. Store pendencies if FK not found
    # 4. Retrieve and resolve existing pendencies
    # 5. Return enriched message
    return enriched_message
```

## Notes

- All connection parameters are read from environment variables
- Connections are established automatically on initialization
- The manager is thread-safe for read operations
- For write-heavy workloads, consider connection pooling (already handled by PyMongo)
