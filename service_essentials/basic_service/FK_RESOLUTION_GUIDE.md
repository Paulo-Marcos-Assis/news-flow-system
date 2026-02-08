# Foreign Key Resolution Guide

## Overview

The FK (Foreign Key) resolution feature automatically enriches messages with references to related entities stored in the document database. This enables proper relationship tracking across the data ingestion pipeline.

## How It Works

### 1. **Configuration**

Enable FK resolution for specific services using environment variables:

```bash
# In .env
PROCESSOR_ESFINGE_RESOLVE_FOREIGN_KEYS=true
PROCESSOR_PNCP_RESOLVE_FOREIGN_KEYS=true
```

The pattern is: `{SERVICE_NAME}_RESOLVE_FOREIGN_KEYS=true`

### 2. **Dependency Files**

FK dependencies are defined in JSON files under `data_dependencies/{source}/`:

- **`dependencies_temporal.json`**: Defines which entities depend on others
- **`inverted_dependencies_temporal.json`**: Reverse lookup for resolving pendencies
- **`no_dependencies_atemporal.json`**: Static reference data (CSV-based)
- **`no_dependencies_temporal.json`**: Time-based reference data

#### Example: dependencies_temporal.json

```json
{
    "processo_licitatorio": {
        "unidade_gestora": {
            "fk": "ID UnidadeGestora",
            "pk": "ID UnidadeGestora"
        },
        "modalidade_licitacao": {
            "fk": "ID ModalidadeLicitacao",
            "pk": "ID ModalidadeLicitacao"
        }
    }
}
```

This means:
- `processo_licitatorio` has a FK to `unidade_gestora`
- The FK field in the message is `"ID UnidadeGestora"`
- The PK field in the referenced entity is also `"ID UnidadeGestora"`

### 3. **Message Flow**

#### Step 1: Message Arrives
```json
{
    "data_source": "esfinge",
    "entity_type": "processo_licitatorio",
    "ID UnidadeGestora": 123,
    "ID ModalidadeLicitacao": 5,
    "titulo": "Licitação XYZ",
    "raw_data_id": "abc123"
}
```

#### Step 2: FK Resolution
The system looks up each FK in the document storage:

```python
# Query: esfinge.unidade_gestora where "ID UnidadeGestora" = 123
# Query: esfinge.modalidade_licitacao where "ID ModalidadeLicitacao" = 5
```

#### Step 3a: FK Found - Enrichment
```json
{
    "data_source": "esfinge",
    "entity_type": "processo_licitatorio",
    "ID UnidadeGestora": 123,
    "unidade_gestora_raw_data_id": "xyz789",  // ← Added
    "ID ModalidadeLicitacao": 5,
    "modalidade_licitacao_raw_data_id": "def456",  // ← Added
    "titulo": "Licitação XYZ",
    "raw_data_id": "abc123"
}
```

#### Step 3b: FK Not Found - Pendency
If `unidade_gestora` with ID 123 doesn't exist yet, a pendency is stored:

```json
{
    "source": "esfinge",
    "entity": "processo_licitatorio",
    "missing_fk_entity": "unidade_gestora",
    "missing_fk_field": "ID UnidadeGestora",
    "missing_pk_field": "ID UnidadeGestora",
    "fk_value": 123,
    "original_message": { /* full message */ },
    "timestamp": "2025-10-18T11:56:00",
    "resolved": false
}
```

Collection: `esfinge.processo_licitatorio.pendency`

### 4. **Pendency Resolution**

When the missing entity arrives later:

```json
{
    "data_source": "esfinge",
    "entity_type": "unidade_gestora",
    "ID UnidadeGestora": 123,
    "nome": "Secretaria de Educação",
    "raw_data_id": "xyz789"
}
```

The system:
1. Stores this entity in `esfinge.unidade_gestora`
2. Checks `inverted_dependencies_temporal.json` for dependents
3. Finds pending `processo_licitatorio` records
4. Re-queues them with the FK resolved
5. Marks pendencies as `resolved: true`

## Implementation in Services

### Using in a Processor

```python
class ProcessorEsfinge(BasicProducerConsumerService):
    def process_message(self, message):
        # Add entity_type to message for FK resolution
        message["entity_type"] = "processo_licitatorio"
        
        # FK resolution happens automatically in the base class
        # if PROCESSOR_ESFINGE_RESOLVE_FOREIGN_KEYS=true
        
        # Your processing logic here
        result = self.extract_data(message)
        
        return result
```

### Message Requirements

For FK resolution to work, messages must include:
1. **`data_source`**: Source identifier (e.g., "esfinge", "pncp")
2. **`entity_type`**: Entity name matching the dependency files
3. **`raw_data_id`**: Unique identifier for this record
4. FK field values as defined in the dependency configuration

## Execution Flow

```
Message Received
    ↓
preprocess_message() [optional override]
    ↓
retrieve_fk_data() [if enabled]
    ├─→ Load dependency config
    ├─→ For each FK:
    │   ├─→ Query document storage
    │   ├─→ If found: Add {entity}_raw_data_id
    │   └─→ If not found: Store pendency
    └─→ Check for pendencies to resolve
    ↓
process_message() [your logic]
    ↓
postprocess_message() [optional override]
    ↓
Send to output queue
```

## Monitoring Pendencies

### Query Pending Records

```python
# Get all unresolved pendencies for processo_licitatorio
pendencies = document_storage_manager.find_documents(
    "esfinge.processo_licitatorio.pendency",
    {"resolved": False}
)

# Count pendencies by missing entity
from collections import Counter
missing_entities = Counter(p["missing_fk_entity"] for p in pendencies)
print(missing_entities)
# Output: {'unidade_gestora': 45, 'modalidade_licitacao': 12}
```

### Manually Resolve Pendencies

```python
# If you need to manually trigger resolution
service._resolve_pendencies(
    source="esfinge",
    entity_type="unidade_gestora",
    message=unidade_gestora_message,
    dependent_entities=inverted_deps["unidade_gestora"]
)
```

## Configuration Examples

### Enable for Specific Services

```bash
# Only resolve FKs in esfinge processor
PROCESSOR_ESFINGE_RESOLVE_FOREIGN_KEYS=true

# Disable for others (default)
PROCESSOR_PNCP_RESOLVE_FOREIGN_KEYS=false
PROCESSOR_DOM_RESOLVE_FOREIGN_KEYS=false
```

### Service Name Detection

The service name is automatically detected from the `SERVICE_NAME` environment variable, which is typically set in `docker-compose.yml`:

```yaml
processor-esfinge:
  build: processor/esfinge
  environment:
    SERVICE_NAME: "PROCESSOR_ESFINGE"
    INPUT_QUEUE: "esfinge_processor"
    OUTPUT_QUEUE: "esfinge_verifier"
```

## Best Practices

### 1. **Order of Processing**

Process entities in dependency order when possible:
- First: Reference data (no dependencies)
- Then: Parent entities (e.g., `unidade_gestora`)
- Finally: Child entities (e.g., `processo_licitatorio`)

### 2. **Pendency Cleanup**

Periodically clean up old resolved pendencies:

```python
from datetime import datetime, timedelta

# Delete pendencies resolved more than 30 days ago
cutoff = (datetime.now() - timedelta(days=30)).isoformat()
document_storage_manager.delete_many_documents(
    "esfinge.processo_licitatorio.pendency",
    {"resolved": True, "resolved_at": {"$lt": cutoff}}
)
```

### 3. **Error Handling**

The FK resolution is designed to be resilient:
- If dependency files are missing, processing continues without FK resolution
- If document storage is unavailable, errors are logged but don't stop processing
- Pendencies ensure no data is lost when FKs are temporarily unavailable

### 4. **Performance Considerations**

- FK lookups are single-document queries (fast with proper indexes)
- Pendency resolution happens asynchronously via re-queuing
- Consider batching if you have many pendencies to resolve

## Troubleshooting

### FK Resolution Not Working

1. Check environment variable is set correctly
2. Verify `data_source` and `entity_type` are in the message
3. Confirm dependency files exist in `data_dependencies/{source}/`
4. Check logs for "skipping FK resolution" messages

### Pendencies Not Resolving

1. Verify `inverted_dependencies_temporal.json` is correct
2. Check that PK values match exactly (type and value)
3. Ensure the referenced entity is being stored in document storage
4. Look for error logs in `_resolve_pendencies`

### Performance Issues

1. Add indexes to MongoDB collections:
   ```javascript
   db.getCollection("esfinge.unidade_gestora").createIndex({"ID UnidadeGestora": 1})
   ```
2. Monitor pendency collection sizes
3. Consider archiving old resolved pendencies

## Example Scenario

### Scenario: Processing e-Sfinge Data

1. **Unidade Gestora arrives first**:
   ```json
   {"entity_type": "unidade_gestora", "ID UnidadeGestora": 123, ...}
   ```
   - Stored in `esfinge.unidade_gestora`
   - No pendencies to resolve (no dependents yet)

2. **Processo Licitatorio arrives**:
   ```json
   {"entity_type": "processo_licitatorio", "ID UnidadeGestora": 123, ...}
   ```
   - FK lookup finds unidade_gestora
   - Message enriched with `unidade_gestora_raw_data_id`
   - Continues to next stage

3. **Another Processo arrives with missing FK**:
   ```json
   {"entity_type": "processo_licitatorio", "ID UnidadeGestora": 999, ...}
   ```
   - FK lookup fails (unidade_gestora 999 doesn't exist)
   - Pendency stored
   - Processing continues (without FK enrichment)

4. **Missing Unidade Gestora arrives later**:
   ```json
   {"entity_type": "unidade_gestora", "ID UnidadeGestora": 999, ...}
   ```
   - Stored in `esfinge.unidade_gestora`
   - Pendency found and resolved
   - Pending processo_licitatorio re-queued with FK

## Summary

The FK resolution system provides:
- ✅ Automatic relationship tracking
- ✅ Resilient handling of out-of-order data
- ✅ Transparent integration with existing services
- ✅ Comprehensive pendency management
- ✅ Configurable per-service activation

This ensures data integrity across the entire ingestion pipeline while handling the complexities of distributed, asynchronous processing.
