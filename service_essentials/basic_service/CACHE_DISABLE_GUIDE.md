# Disabling Cache in CachedCollectorService

The `CachedCollectorService` provides flexible options for disabling the cache mechanism when needed.

## Option 1: Disable Cache Globally for a Collector

You can disable caching for an entire collector by passing `use_cache=False` in the constructor:

```python
class CollectorDom(CachedCollectorService):
    def __init__(self):
        # Disable cache for all messages
        super().__init__(data_source="dom", use_cache=False)
    
    def collect_data(self, message):
        # Your data collection logic
        records = self.fetch_data(message)
        return records
```

### What Happens When Cache is Disabled:

- ✅ No cache checking occurs
- ✅ No configuration is stored in `{source}.collect_config`
- ✅ Records are published without `collect_id` field
- ✅ All messages are processed normally (no cache hits)
- ✅ Logging indicates cache is disabled

### Behavior:

```python
# With cache disabled:
self.logger.info("Cache disabled: Collecting data")
# ... collects data ...
self.logger.info(f"Processed {count} records (cache disabled)")
```

## Option 2: Skip Cache Lookup Per-Message (Force Refresh)

You can skip cache lookup for specific messages by adding `"no_cache": true` to the message:

```python
# Message that skips cache lookup but stores results
message = {
    "api_url": "https://example.com",
    "date": "01/01/2024",
    "package_name": "example",
    "no_cache": true  # Skip cache lookup, but store results
}
```

### What Happens:

- ✅ Cache **lookup is skipped** (always treated as cache miss)
- ✅ Data is collected fresh from source
- ✅ Configuration **is stored** in cache (without `no_cache` field)
- ✅ Records **are saved** with `collect_id`
- ✅ Future identical messages (without `no_cache`) **can use this cached data**

### Important:

**`no_cache: true` means "don't use cache for lookup, but store the results"**

This is different from `use_cache=False` which disables cache completely.

### Use Case:

This is useful when you want to:
- **Force refresh** of specific cached data
- **Update stale cache** with fresh data
- **Correct cached data** after source corrections
- **Rebuild cache** for specific configurations

The fresh data is stored in cache, so future requests can benefit from it.

## Comparison

### Cache Enabled (Default)

```python
class CollectorDom(CachedCollectorService):
    def __init__(self):
        super().__init__(data_source="dom")  # use_cache=True by default
```

**Flow:**
```
Message → Check cache → HIT: Publish cached records
                      → MISS: Collect data → Store config → Publish with collect_id
```

**MongoDB Collections:**
- `dom.collect_config`: Stores message configurations
- `dom`: Stores records with `collect_id` field

### Cache Disabled Globally

```python
class CollectorDom(CachedCollectorService):
    def __init__(self):
        super().__init__(data_source="dom", use_cache=False)
```

**Flow:**
```
Message → Collect data → Publish without collect_id
```

**MongoDB Collections:**
- `dom.collect_config`: Not used
- `dom`: Stores records without `collect_id` field

### Cache Lookup Skipped Per-Message (Force Refresh)

```python
# Collector has cache enabled
class CollectorDom(CachedCollectorService):
    def __init__(self):
        super().__init__(data_source="dom")

# But message skips cache lookup
message = {"api_url": "...", "no_cache": true}
```

**Flow:**
```
Message with no_cache → Skip cache lookup → Collect fresh data → Store config → Publish with collect_id
```

**Key Point:** Data is still stored in cache for future use!

**MongoDB Collections:**
- `dom.collect_config`: Stores config (without `no_cache` field) - **UPDATED/CREATED**
- `dom`: Stores records with `collect_id` field - **UPDATED/CREATED**

## Examples

### Example 1: Development/Testing Collector (No Cache)

```python
class CollectorDomDev(CachedCollectorService):
    def __init__(self):
        # Disable cache for development/testing
        super().__init__(data_source="dom_dev", use_cache=False)
    
    def collect_data(self, message):
        # Always processes fresh data
        return self.fetch_fresh_data(message)
```

### Example 2: Production Collector (Cache Enabled)

```python
class CollectorDom(CachedCollectorService):
    def __init__(self):
        # Cache enabled for production efficiency
        super().__init__(data_source="dom")
    
    def collect_data(self, message):
        # Cached when possible
        return self.fetch_data(message)
```

### Example 3: Conditional Cache

```python
class CollectorDom(CachedCollectorService):
    def __init__(self):
        # Enable/disable based on environment variable
        use_cache = os.getenv("ENABLE_CACHE", "true").lower() == "true"
        super().__init__(data_source="dom", use_cache=use_cache)
    
    def collect_data(self, message):
        return self.fetch_data(message)
```

### Example 4: Force Refresh via Message

```python
# Normal message (uses cache if available)
normal_message = {
    "api_url": "https://api.example.com",
    "date": "01/01/2024"
}
# If this was processed before, it will use cached data

# Force refresh message (skips cache lookup, but stores results)
refresh_message = {
    "api_url": "https://api.example.com",
    "date": "01/01/2024",
    "no_cache": true  # Forces fresh data collection and updates cache
}
# This will collect fresh data and update the cache
# Next time normal_message is sent, it will use this updated cache
```

## When to Disable Cache

### Disable Globally (`use_cache=False`) When:

- ✅ **Development/Testing**: You want fresh data every time
- ✅ **Real-time Data**: Source data changes frequently
- ✅ **No Duplication**: Messages are never identical
- ✅ **Debugging**: You want to test data collection logic

### Skip Cache Lookup Per-Message (`no_cache: true`) When:

- ✅ **Force Refresh**: Need to update specific cached data with fresh source data
- ✅ **Data Correction**: Source data was corrected and cache needs updating
- ✅ **Manual Trigger**: User explicitly requests fresh data (but keep it cached)
- ✅ **Scheduled Updates**: Periodic refresh of specific cached data
- ✅ **Cache Rebuild**: Rebuild cache for specific configurations

**Important:** The fresh data is stored in cache, so future requests benefit from it!

### Keep Cache Enabled When:

- ✅ **Production**: Efficiency and performance matter
- ✅ **Duplicate Messages**: Same messages may arrive multiple times
- ✅ **Expensive Operations**: Data collection is slow or costly
- ✅ **Static Data**: Source data doesn't change frequently

## Environment Variable Configuration

You can use environment variables to control caching:

```python
import os

class CollectorDom(CachedCollectorService):
    def __init__(self):
        # Read from environment variable
        use_cache = os.getenv("DOM_COLLECTOR_USE_CACHE", "true").lower() == "true"
        super().__init__(data_source="dom", use_cache=use_cache)
    
    def collect_data(self, message):
        return self.fetch_data(message)
```

**Docker Compose:**
```yaml
collector-dom:
  environment:
    DOM_COLLECTOR_USE_CACHE: "false"  # Disable cache
```

## Logging

The service logs cache status clearly:

**Cache Enabled:**
```
Cache HIT: Using cached data with collect_id=abc123
Published 150 cached records from collect_id=abc123
```

**Cache Miss:**
```
Cache MISS: Collecting data
Processed 150 records with collect_id=def456
```

**Cache Disabled:**
```
Cache mechanism disabled for dom
Cache disabled: Collecting data
Processed 150 records (cache disabled)
```

## Summary

| Method | Cache Lookup | Cache Storage | Use Case | MongoDB Impact |
|--------|--------------|---------------|----------|----------------|
| `use_cache=False` | ❌ Disabled | ❌ Disabled | Development, testing, real-time | No cache collections used |
| `no_cache: true` | ❌ Skipped | ✅ Enabled | Force refresh, update cache | Config stored, records have collect_id |
| Default (enabled) | ✅ Enabled | ✅ Enabled | Production, efficiency | Full cache functionality |

**Key Difference:**
- **`use_cache=False`**: Complete cache bypass (no lookup, no storage)
- **`no_cache: true`**: Skip lookup only, but **store results** for future use

Choose the method that best fits your use case!
