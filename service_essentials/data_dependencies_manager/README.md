# Data Dependencies Manager

## Overview

The Data Dependencies Manager provides a unified interface for managing foreign key relationships and dependencies between entities in the CEOS data ingestion system. It follows the same factory pattern and dependency injection approach as other managers in the system.

## Architecture

```
DataDependenciesManagerFactory
    ↓
DataDependenciesManager (Abstract)
    ↓
JsonDependenciesManager (JSON Files Implementation)
```

### Helper Classes

- **FKResolver**: Handles FK lookup and message enrichment
- **PendencyManager**: Manages pendencies for missing FKs

## Features

- **Dependency Injection**: Automatically instantiated in `BasicProducerConsumerService`
- **Factory Pattern**: Easy to switch between different dependency sources
- **Caching**: Dependencies are loaded once and cached
- **Separation of Concerns**: FK resolution logic separated from base service
- **Extensible**: Easy to add new dependency sources (database, API, etc.)

## Configuration

Add to `.env`:

```bash
# Data Dependencies Manager Type
DATA_DEPENDENCIES_MANAGER=json

# Base path to dependencies directory
DATA_DEPENDENCIES_PATH=data_dependencies
```

## Directory Structure

```
data_dependencies/
├── esfinge/
│   ├── dependencies_temporal.json           # FK relationships
│   ├── inverted_dependencies_temporal.json  # Reverse FK relationships
│   ├── no_dependencies_atemporal.json       # Static reference data
│   └── no_dependencies_temporal.json        # Temporal reference data
└── pncp/
    └── ... (same structure)
```

## JSON File Formats

### dependencies_temporal.json

Defines which entities have FK dependencies:

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

**Meaning**: `processo_licitatorio` has FKs to `unidade_gestora` and `modalidade_licitacao`

### inverted_dependencies_temporal.json

Reverse lookup - which entities depend on this one:

```json
{
    "unidade_gestora": {
        "processo_licitatorio": {
            "fk": "ID UnidadeGestora",
            "pk": "ID UnidadeGestora"
        }
    }
}
```

**Meaning**: `processo_licitatorio` depends on `unidade_gestora`

### no_dependencies_atemporal.json

Static reference data (lookup tables):

```json
{
    "tipo_pessoa": {"csv_file": "tipo_pessoa.csv"},
    "modalidade_licitacao": {"csv_file": "modalidade_licitacao.csv"}
}
```

### no_dependencies_temporal.json

Temporal reference data (time-based):

```json
{
    "comissao_licitacao": {
        "csv_file": "comissao_licitacao_2021.csv",
        "year": "2021"
    }
}
```

## API Reference

### DataDependenciesManager

#### load_dependencies(source: str) -> bool
Load dependency configuration for a data source.

```python
loaded = manager.load_dependencies("esfinge")
```

#### get_entity_dependencies(source: str, entity_type: str) -> Dict
Get FK dependencies for an entity.

```python
deps = manager.get_entity_dependencies("esfinge", "processo_licitatorio")
# Returns: {"unidade_gestora": {"fk": "ID UnidadeGestora", "pk": "ID UnidadeGestora"}}
```

#### get_dependent_entities(source: str, entity_type: str) -> Dict
Get entities that depend on this entity.

```python
dependents = manager.get_dependent_entities("esfinge", "unidade_gestora")
# Returns: {"processo_licitatorio": {"fk": "ID UnidadeGestora", "pk": "ID UnidadeGestora"}}
```

#### has_dependencies(source: str, entity_type: str) -> bool
Check if entity has dependencies.

```python
if manager.has_dependencies("esfinge", "processo_licitatorio"):
    print("Has dependencies")
```

#### get_all_entities(source: str) -> List[str]
Get all entities for a source.

```python
entities = manager.get_all_entities("esfinge")
# Returns: ["processo_licitatorio", "unidade_gestora", "modalidade_licitacao", ...]
```

#### get_static_reference_entities(source: str) -> Dict
Get static reference data configuration.

```python
static_refs = manager.get_static_reference_entities("esfinge")
# Returns: {"tipo_pessoa": {"csv_file": "tipo_pessoa.csv"}, ...}
```

#### get_temporal_reference_entities(source: str) -> Dict
Get temporal reference data configuration.

```python
temporal_refs = manager.get_temporal_reference_entities("esfinge")
```

### FKResolver

#### resolve_fk_dependencies(message: Dict) -> Dict
Resolve all FK dependencies for a message.

```python
enriched_message = fk_resolver.resolve_fk_dependencies(message)
```

### PendencyManager

#### store_pendency(...) -> Optional[str]
Store a pendency when FK is missing.

```python
pendency_id = pendency_manager.store_pendency(
    source="esfinge",
    entity_type="processo_licitatorio",
    ref_entity="unidade_gestora",
    fk_field="ID UnidadeGestora",
    pk_field="ID UnidadeGestora",
    fk_value=123,
    message=original_message
)
```

#### resolve_pendencies(...) -> int
Resolve pendencies that depend on this record.

```python
resolved_count = pendency_manager.resolve_pendencies(
    source="esfinge",
    entity_type="unidade_gestora",
    message=current_message,
    output_queue="esfinge_processor"
)
```

## Usage in Services

The managers are automatically available in all services:

```python
class ProcessorEsfinge(BasicProducerConsumerService):
    def process_message(self, message):
        # Access data dependencies manager
        deps = self.data_dependencies_manager.get_entity_dependencies(
            "esfinge",
            "processo_licitatorio"
        )
        
        # FK resolution happens automatically if enabled
        # via self.fk_resolver and self.pendency_manager
        
        return result
```

## Integration with BasicProducerConsumerService

The managers are initialized in the constructor:

```python
# In BasicProducerConsumerService.__init__()
self.data_dependencies_manager = DataDependenciesManagerFactory.get_data_dependencies_manager()

if self.resolve_foreign_keys:
    self.fk_resolver = FKResolver(
        self.data_dependencies_manager,
        self.document_storage_manager,
        self.logger
    )
    self.pendency_manager = PendencyManager(
        self.data_dependencies_manager,
        self.document_storage_manager,
        self.queue_manager,
        self.logger
    )
```

## Advantages of This Design

### 1. **Separation of Concerns**
- Dependency management separated from FK resolution
- FK resolution separated from pendency management
- Each class has a single responsibility

### 2. **Dependency Injection**
- Managers are injected, not created internally
- Easy to mock for testing
- Follows SOLID principles

### 3. **Extensibility**
- Easy to add new dependency sources (database, API, etc.)
- Just implement `DataDependenciesManager` interface
- Update factory to support new type

### 4. **Testability**
- Each component can be tested independently
- Mock dependencies easily
- Clear interfaces

### 5. **Maintainability**
- Clean, focused code
- Easy to understand and modify
- Consistent with other managers

## Adding New Dependency Sources

To add support for another dependency source (e.g., database):

### 1. Create Implementation

```python
# database_dependencies_manager.py
class DatabaseDependenciesManager(DataDependenciesManager):
    def __init__(self, db_connection):
        self.db = db_connection
        
    def load_dependencies(self, source: str) -> bool:
        # Load from database
        pass
    
    # Implement other abstract methods
```

### 2. Update Factory

```python
# data_dependencies_manager_factory.py
if dependencies_manager_type == "database":
    from service_essentials.data_dependencies_manager.database_dependencies_manager import DatabaseDependenciesManager
    return DatabaseDependenciesManager(db_connection)
```

### 3. Configure

```bash
# .env
DATA_DEPENDENCIES_MANAGER=database
```

## Example: Complete Flow

### 1. Service Starts
```python
# BasicProducerConsumerService initializes
self.data_dependencies_manager = DataDependenciesManagerFactory.get_data_dependencies_manager()
# Returns JsonDependenciesManager instance
```

### 2. Message Arrives
```json
{
    "data_source": "esfinge",
    "entity_type": "processo_licitatorio",
    "ID UnidadeGestora": 123,
    "raw_data_id": "proc_001"
}
```

### 3. FK Resolution
```python
# In retrieve_fk_data()
message = self.fk_resolver.resolve_fk_dependencies(message)
```

### 4. FKResolver Workflow
```python
# 1. Load dependencies
deps = self.dependencies_manager.get_entity_dependencies("esfinge", "processo_licitatorio")

# 2. For each dependency
for ref_entity, fk_config in deps.items():
    # 3. Query document storage
    doc = self.document_storage_manager.find_document(
        "esfinge.unidade_gestora",
        {"ID UnidadeGestora": 123}
    )
    
    # 4. Enrich message
    if doc:
        message["unidade_gestora_raw_data_id"] = doc["raw_data_id"]
```

### 5. Pendency Resolution
```python
# Check for pendencies
self.pendency_manager.resolve_pendencies(
    "esfinge",
    "processo_licitatorio",
    message,
    output_queue
)
```

## Monitoring

### Get Dependency Info

```python
info = manager.get_dependency_info("esfinge")
print(info)
# {
#     "source": "esfinge",
#     "loaded": True,
#     "total_entities": 45,
#     "entities_with_dependencies": 20,
#     "entities_with_dependents": 15,
#     "static_reference_entities": 18,
#     "temporal_reference_entities": 1
# }
```

### Check if Loaded

```python
if manager.is_loaded("esfinge"):
    print("Dependencies loaded")
```

### Reload Dependencies

```python
# Useful after updating JSON files
manager.reload_dependencies("esfinge")
```

## Best Practices

### 1. **Keep JSON Files in Sync**
Ensure `dependencies_temporal.json` and `inverted_dependencies_temporal.json` are consistent.

### 2. **Use Descriptive Field Names**
FK and PK field names should match exactly what's in the data.

### 3. **Document Dependencies**
Add comments in JSON files explaining complex relationships.

### 4. **Version Control**
Keep dependency files in version control.

### 5. **Validate JSON**
Use JSON validators to catch syntax errors.

## Troubleshooting

### Dependencies Not Loading

**Check 1**: File path correct?
```python
# Verify path
import os
print(os.path.exists("data_dependencies/esfinge/dependencies_temporal.json"))
```

**Check 2**: JSON valid?
```bash
# Validate JSON
python -m json.tool data_dependencies/esfinge/dependencies_temporal.json
```

**Check 3**: Check logs
```
[INFO] Loaded dependencies_temporal.json for 'esfinge'
```

### FK Not Resolving

**Check 1**: Dependencies loaded?
```python
if manager.is_loaded("esfinge"):
    deps = manager.get_entity_dependencies("esfinge", "processo_licitatorio")
    print(deps)
```

**Check 2**: Field names match?
Verify FK and PK field names in JSON match actual data.

## Summary

The Data Dependencies Manager provides:
- ✅ Clean abstraction for dependency management
- ✅ Separation of concerns (dependencies, resolution, pendencies)
- ✅ Dependency injection and factory pattern
- ✅ Easy extensibility to new sources
- ✅ Consistent with existing architecture
- ✅ Well-tested and maintainable

This design makes the FK resolution system more modular, testable, and maintainable while following SOLID principles and existing patterns in the codebase.
