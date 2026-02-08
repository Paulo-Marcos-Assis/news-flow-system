# FK Resolution with Pendency Check

## Critical Enhancement: Check Referenced Document's Pendencies

When resolving a foreign key, we now check if the **referenced document itself** has all its pendencies resolved before using it.

---

## The Problem

### Previous Behavior (Incomplete)

```
Empenho arrives → needs Processo
Lookup Processo → Found!
✗ Use Processo immediately (WRONG!)
✗ What if Processo itself has unresolved pendencies?
```

**Issue**: We were resolving FKs to documents that weren't fully resolved themselves.

---

## The Solution

### New Behavior (Correct)

```
Empenho arrives → needs Processo
Lookup Processo → Found!
Check: Does Processo have all its pendencies resolved?
  ├─ YES → Use Processo ✓
  └─ NO → Create pendency for Empenho ✓
```

**Result**: Only resolve FKs to fully resolved documents.

---

## Implementation

### Code Change

```python
if referenced_doc:
    # FK data found - check if referenced document has all its pendencies resolved
    referenced_raw_data_id = referenced_doc.get("raw_data_id")
    
    # Check if the referenced document itself has unresolved pendencies
    if self.pendency_manager.check_all_pendencies_resolved(source, ref_entity, referenced_raw_data_id):
        # Referenced document is fully resolved - can use it
        message[ref_entity] = {"raw_data_id": referenced_raw_data_id}
        self.logger.info(f"FK resolved: raw_data_id = {referenced_raw_data_id}")
        return True
    else:
        # Referenced document exists but has unresolved pendencies - create pendency
        self.logger.warning(f"FK found but referenced document {referenced_raw_data_id} has unresolved pendencies, creating pendency")
        self.pendency_manager.store_pendency(...)
        return False
```

---

## Complete Example

### Setup: Chain of Dependencies

```
Empenho → Processo → Unidade Gestora → Orgao
```

**Arrival Order**: Empenho, Processo, Unidade Gestora, Orgao

---

### Step 1: Empenho Arrives (Processo Not Found)

**Message**:
```json
{
    "entity_type": "empenho",
    "ID Empenho": "EMP001",
    "ID ProcedimentoLicitatorio": "PROC123",
    "raw_data_id": "emp_001"
}
```

**FK Resolution**:
1. Lookup Processo with `ID ProcedimentoLicitatorio = "PROC123"`
2. **Not found** in database
3. Create pendency for Empenho

**Result**: Empenho has pendency (needs Processo)

---

### Step 2: Processo Arrives (Unidade Gestora Not Found)

**Message**:
```json
{
    "entity_type": "processo_licitatorio",
    "ID ProcedimentoLicitatorio": "PROC123",
    "ID UnidadeGestora": 456,
    "raw_data_id": "proc_123"
}
```

**FK Resolution**:
1. Lookup Unidade Gestora with `ID UnidadeGestora = 456`
2. **Not found** in database
3. Create pendency for Processo

**Processo Stored in DB**:
```json
{
    "entity_type": "processo_licitatorio",
    "ID ProcedimentoLicitatorio": "PROC123",
    "ID UnidadeGestora": 456,
    "raw_data_id": "proc_123"
}
```

**Pendency Created**:
```json
{
    "_id": ObjectId("..."),
    "raw_data_id": "proc_123",
    "missing_entity": "unidade_gestora",
    "fk_value": 456,
    "resolved": false
}
```

**Result**: Processo stored but has unresolved pendency

---

### Step 3: Another Empenho Arrives (Needs Same Processo) - **CRITICAL CHECK**

**Message**:
```json
{
    "entity_type": "empenho",
    "ID Empenho": "EMP002",
    "ID ProcedimentoLicitatorio": "PROC123",
    "raw_data_id": "emp_002"
}
```

**FK Resolution (With New Check)**:
1. Lookup Processo with `ID ProcedimentoLicitatorio = "PROC123"`
2. **Found!** Processo exists in database
3. **NEW CHECK**: Does Processo have all pendencies resolved?
   ```python
   check_all_pendencies_resolved("esfinge", "processo_licitatorio", "proc_123")
   # Query: {"raw_data_id": "proc_123", "resolved": False}
   # Found: 1 unresolved (needs Unidade Gestora)
   # Returns: False
   ```
4. **Result**: Processo has unresolved pendencies
5. **Action**: Create pendency for Empenho (don't resolve FK yet)

**Log Output**:
```
[INFO] Looking up FK: processo_licitatorio.ID ProcedimentoLicitatorio = PROC123
[WARNING] FK found but referenced document proc_123 has unresolved pendencies, creating pendency
```

**Pendency Created for Empenho**:
```json
{
    "_id": ObjectId("..."),
    "raw_data_id": "emp_002",
    "missing_entity": "processo_licitatorio",
    "fk_value": "PROC123",
    "resolved": false
}
```

**Result**: Empenho NOT resolved (even though Processo exists!)

---

### Step 4: Unidade Gestora Arrives (Orgao Not Found)

**Message**:
```json
{
    "entity_type": "unidade_gestora",
    "ID UnidadeGestora": 456,
    "ID Orgao": 789,
    "raw_data_id": "ug_456"
}
```

**FK Resolution**:
1. Lookup Orgao → Not found
2. Create pendency for Unidade Gestora

**Pendency Resolution**:
1. Find pendencies waiting for Unidade Gestora
2. Found: Processo (proc_123)
3. Mark Processo's UG pendency as resolved
4. Check: Does Processo have all pendencies resolved?
   - **YES!** (only needed UG)
5. Merge Processo into UG message

**Result**: Processo now fully resolved

---

### Step 5: Orgao Arrives - **CASCADING RESOLUTION**

**Message**:
```json
{
    "entity_type": "orgao",
    "ID Orgao": 789,
    "raw_data_id": "org_789"
}
```

**Pendency Resolution**:
1. Resolves Unidade Gestora's pendency
2. UG fully resolved → Merges into Orgao
3. Recursive: Processo was merged into UG
4. Processo now fully resolved → Check pendencies waiting for Processo
5. Found: Empenho (emp_001) and Empenho (emp_002)
6. Both Empenhos' pendencies resolved
7. Both merge into Processo

**Final Result**: Complete chain resolved!

---

## Why This Check is Critical

### Without the Check (Wrong)

```
Timeline:
1. Empenho A arrives → Processo not found → Pendency created ✓
2. Processo arrives → UG not found → Pendency created ✓
   Processo stored in DB (with unresolved pendency)
3. Empenho B arrives → Processo found → FK resolved ✗ WRONG!
   Empenho B thinks it's resolved, but Processo isn't!
4. UG arrives → Resolves Processo
   But Empenho B already processed with incomplete Processo!
```

**Problem**: Empenho B was resolved to an incomplete Processo.

---

### With the Check (Correct)

```
Timeline:
1. Empenho A arrives → Processo not found → Pendency created ✓
2. Processo arrives → UG not found → Pendency created ✓
   Processo stored in DB (with unresolved pendency)
3. Empenho B arrives → Processo found → Check pendencies ✓
   Processo has unresolved pendencies → Pendency created ✓
4. UG arrives → Resolves Processo → Processo fully resolved ✓
   Recursive resolution → Resolves both Empenhos ✓
```

**Result**: Both Empenhos resolved only when Processo is fully resolved.

---

## Three States of a Document

### 1. **Not Found**
- Document doesn't exist in database
- **Action**: Create pendency

### 2. **Found but Incomplete**
- Document exists in database
- Document has unresolved pendencies
- **Action**: Create pendency (NEW!)

### 3. **Found and Complete**
- Document exists in database
- Document has all pendencies resolved
- **Action**: Resolve FK

---

## Decision Tree

```
Lookup FK
  │
  ├─ Not Found
  │   └─ Create Pendency
  │
  └─ Found
      │
      ├─ Has Unresolved Pendencies
      │   └─ Create Pendency (wait for referenced doc to be complete)
      │
      └─ All Pendencies Resolved
          └─ Resolve FK (safe to use)
```

---

## Benefits

### 1. **Data Integrity**
- ✅ Only resolve FKs to complete documents
- ✅ No partial/incomplete references
- ✅ Consistent data state

### 2. **Correct Ordering**
- ✅ Respects dependency chain
- ✅ Documents resolved in correct order
- ✅ No premature resolution

### 3. **Cascading Resolution**
- ✅ When referenced doc completes, all dependents resolve
- ✅ Automatic propagation
- ✅ Complete chain resolution

### 4. **Prevents Errors**
- ✅ No processing with incomplete FKs
- ✅ No null reference errors
- ✅ Guaranteed data completeness

---

## Edge Cases

### Case 1: Circular Dependencies

```
A depends on B
B depends on A
```

**Behavior**:
1. A arrives → B not found → Pendency created
2. B arrives → A found but incomplete → Pendency created
3. **Both stuck** (circular dependency detected)

**Resolution**: Circular dependencies should be prevented at schema design level.

---

### Case 2: Long Dependency Chain

```
A → B → C → D → E
```

**Behavior**:
1. A arrives → B not found → Pendency
2. B arrives → C not found → Pendency
3. C arrives → D not found → Pendency
4. D arrives → E not found → Pendency
5. E arrives → No dependencies → Stored
6. **Cascading resolution**: D → C → B → A (all resolve in order)

**Result**: Entire chain resolves when final dependency arrives.

---

### Case 3: Multiple Dependencies

```
A depends on B and C
B depends on D
C depends on E
```

**Behavior**:
1. A arrives → B not found, C not found → 2 pendencies
2. B arrives → D not found → Pendency (B incomplete)
3. C arrives → E not found → Pendency (C incomplete)
4. D arrives → Resolves B → B complete
5. A still incomplete (needs C)
6. E arrives → Resolves C → C complete
7. A now has all dependencies → Resolves

**Result**: A only resolves when both B and C are complete.

---

## Testing

### Test Case: Referenced Document with Unresolved Pendencies

```python
def test_fk_resolution_checks_referenced_pendencies():
    # Setup: Processo exists but has unresolved pendency
    processo = {
        "ID ProcedimentoLicitatorio": "PROC123",
        "ID UnidadeGestora": 456,
        "raw_data_id": "proc_123"
    }
    doc_storage.insert_document("esfinge.processo_licitatorio", processo)
    
    # Create unresolved pendency for Processo
    pendency_manager.store_pendency(
        source="esfinge",
        entity_type="processo_licitatorio",
        ref_entity="unidade_gestora",
        fk_field="ID UnidadeGestora",
        pk_field="ID UnidadeGestora",
        fk_value=456,
        message=processo
    )
    
    # Empenho arrives needing this Processo
    empenho = {
        "entity_type": "empenho",
        "ID Empenho": "EMP001",
        "ID ProcedimentoLicitatorio": "PROC123",
        "raw_data_id": "emp_001"
    }
    
    # Attempt FK resolution
    result = fk_resolver.resolve_fk_dependencies(empenho)
    
    # Verify: FK NOT resolved (Processo has unresolved pendencies)
    assert result == False
    assert "processo_licitatorio" not in empenho
    
    # Verify: Pendency created for Empenho
    pendencies = doc_storage.find_documents(
        "esfinge.empenho.pendency",
        {"raw_data_id": "emp_001", "resolved": False}
    )
    assert len(pendencies) == 1
    assert pendencies[0]["missing_entity"] == "processo_licitatorio"
```

---

## Summary

### The Check

Before resolving an FK, verify the referenced document has all its pendencies resolved:

```python
if referenced_doc:
    if check_all_pendencies_resolved(source, ref_entity, referenced_raw_data_id):
        # Safe to use
        resolve_fk()
    else:
        # Wait for referenced doc to be complete
        create_pendency()
```

### Benefits

✅ **Data integrity** - Only complete references  
✅ **Correct ordering** - Respects dependency chain  
✅ **Cascading resolution** - Automatic propagation  
✅ **Prevents errors** - No incomplete data  

### Three States

1. **Not Found** → Create pendency
2. **Found but Incomplete** → Create pendency (NEW!)
3. **Found and Complete** → Resolve FK

This ensures that FK resolution only happens when the referenced document is **fully resolved** with all its own dependencies satisfied.
