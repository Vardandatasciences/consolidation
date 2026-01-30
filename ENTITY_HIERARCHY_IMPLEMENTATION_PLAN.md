# Entity Hierarchy Implementation Plan
## Parent-Child-Grandchildren Relationships

### Current State Analysis

**Current `entity_master` Table Structure:**
Based on the code, the table currently has:
- `ent_id` (Primary Key)
- `ent_name`
- `ent_code`
- `lcl_curr`
- `city`
- `country`
- `financial_year_start_month`
- `financial_year_start_day`
- `created_at`
- `updated_at`
- `created_by`

**❌ MISSING:** No parent-child relationship fields

---

## Implementation Steps

### 1. Database Migration

**Create migration file:** `backend/migrations/004_entity_hierarchy.sql`

```sql
-- Migration: Add Parent-Child Relationship to Entities
-- ========================================

USE balance_sheet;

-- Add parent_entity_id column to entity_master
ALTER TABLE entity_master
ADD COLUMN parent_entity_id INT NULL COMMENT 'Reference to parent entity (ent_id)',
ADD INDEX idx_parent_entity (parent_entity_id),
ADD FOREIGN KEY (parent_entity_id) REFERENCES entity_master(ent_id) ON DELETE SET NULL;

-- Note: ON DELETE SET NULL means if parent is deleted, children become orphaned (no parent)
-- Alternative: ON DELETE CASCADE would delete children when parent is deleted (more destructive)
```

**Why `ON DELETE SET NULL`?**
- Prevents accidental cascade deletion of entire company hierarchies
- Allows orphaned entities to exist (can be reassigned later)
- More flexible for business scenarios

---

### 2. Backend API Updates

#### 2.1 Update Entity Routes (`backend/routes/entity.py`)

**A. Update `list_entities()` to include parent information:**
```python
# Add parent_entity_id to SELECT
SELECT 
    ent_id,
    ent_name,
    ent_code,
    lcl_curr,
    city,
    country,
    financial_year_start_month,
    financial_year_start_day,
    parent_entity_id  # NEW
FROM entity_master
ORDER BY ent_name ASC
```

**B. Update `create_entity()` to accept parent_entity_id:**
- Add validation to check if parent exists
- Add validation to prevent circular references (parent cannot be itself)
- Add `parent_entity_id` to INSERT statement

**C. Update `update_entity()` to allow changing parent:**
- Add validation to prevent circular references
- Add validation to prevent setting child as its own parent
- Update parent_entity_id in UPDATE statement

**D. Add new endpoints:**

1. **Get Entity Hierarchy:**
   ```
   GET /entities/<ent_id>/hierarchy
   ```
   Returns: parent, children, grandchildren (full tree)

2. **Get Children:**
   ```
   GET /entities/<ent_id>/children
   ```
   Returns: Direct children only

3. **Get Parent:**
   ```
   GET /entities/<ent_id>/parent
   ```
   Returns: Parent entity information

4. **Get All Descendants:**
   ```
   GET /entities/<ent_id>/descendants
   ```
   Returns: All children, grandchildren, etc. (recursive)

5. **Get Root Entities (entities with no parent):**
   ```
   GET /entities/roots
   ```
   Returns: All top-level entities (no parent)

---

### 3. Backend Helper Functions

**Add to `backend/routes/entity.py`:**

```python
def validate_parent_child_relationship(child_id, parent_id):
    """
    Validate that setting parent_id for child_id doesn't create circular references.
    Returns: (is_valid, error_message)
    """
    if child_id == parent_id:
        return False, "Entity cannot be its own parent"
    
    if not parent_id:
        return True, None  # No parent is valid
    
    # Check if parent_id is a descendant of child_id (would create cycle)
    # Get all descendants of child_id
    descendants = get_all_descendants(child_id)
    if parent_id in descendants:
        return False, "Cannot set parent: it would create a circular reference"
    
    return True, None

def get_all_descendants(entity_id):
    """
    Recursively get all descendant entity IDs (children, grandchildren, etc.)
    Returns: list of entity IDs
    """
    descendants = []
    children_query = "SELECT ent_id FROM entity_master WHERE parent_entity_id = %s"
    children = Database.execute_query(children_query, params=[entity_id], fetch_all=True) or []
    
    for child in children:
        child_id = child.get('ent_id')
        descendants.append(child_id)
        # Recursively get descendants of this child
        descendants.extend(get_all_descendants(child_id))
    
    return descendants
```

---

### 4. Frontend Updates

#### 4.1 Update Entity Type Definitions

**File:** `entity-insights-hub/src/lib/api.ts` or entity types file

```typescript
interface Entity {
  ent_id: number;
  ent_name: string;
  ent_code: string;
  lcl_curr?: string;
  city?: string;
  country?: string;
  financial_year_start_month?: number;
  financial_year_start_day?: number;
  parent_entity_id?: number | null;  // NEW
  parent_entity?: Entity | null;     // NEW (when fetched with hierarchy)
  children?: Entity[];                // NEW (when fetched with hierarchy)
}
```

#### 4.2 Update Entity API Functions

**File:** `entity-insights-hub/src/lib/api.ts`

Add new API functions:
```typescript
export const entityApi = {
  // ... existing functions ...
  
  getHierarchy: async (entId: number) => {
    return apiCall<{
      entity: Entity;
      parent: Entity | null;
      children: Entity[];
      grandchildren: Entity[];
    }>(`/entities/${entId}/hierarchy`, { method: 'GET' });
  },
  
  getChildren: async (entId: number) => {
    return apiCall<{ children: Entity[] }>(`/entities/${entId}/children`, { method: 'GET' });
  },
  
  getParent: async (entId: number) => {
    return apiCall<{ parent: Entity | null }>(`/entities/${entId}/parent`, { method: 'GET' });
  },
  
  getDescendants: async (entId: number) => {
    return apiCall<{ descendants: Entity[] }>(`/entities/${entId}/descendants`, { method: 'GET' });
  },
  
  getRootEntities: async () => {
    return apiCall<{ entities: Entity[] }>('/entities/roots', { method: 'GET' });
  },
};
```

#### 4.3 Update Entity Management UI

**File:** `entity-insights-hub/src/pages/Entities.tsx` (or similar)

**A. Add Parent Selector in Create/Edit Form:**
- Add dropdown to select parent entity
- Exclude current entity from parent options (if editing)
- Show hierarchy breadcrumb if parent exists

**B. Display Hierarchy in Entity List:**
- Show parent entity name (if exists)
- Add expandable tree view for children
- Add filter: "Show only root entities"

**C. Add Hierarchy View Page:**
- Tree visualization of entity relationships
- Click to expand/collapse children
- Show entity details on click

---

### 5. Data Validation Rules

1. **Circular Reference Prevention:**
   - Entity cannot be its own parent
   - Entity cannot have a descendant as its parent
   - Must validate on create and update

2. **Cascade Rules:**
   - When parent is deleted: children become orphaned (parent_entity_id = NULL)
   - When entity is deleted: children are not automatically deleted
   - Consider: Should we allow deletion if entity has children? (Add validation)

3. **Business Rules:**
   - Maximum depth? (e.g., 3 levels: parent, child, grandchild)
   - Can an entity have multiple parents? (No - single parent model)
   - Can an entity change its parent? (Yes, with validation)

---

### 6. Use Cases & Features

#### 6.1 Financial Consolidation
- **Use Case:** Roll up financial data from children to parent
- **Feature:** "Get Consolidated Financials" endpoint
- **Implementation:** Sum amounts from all descendants for parent entity

#### 6.2 Hierarchy Navigation
- **Use Case:** Navigate company structure
- **Feature:** Breadcrumb navigation, tree view
- **Implementation:** Frontend components for hierarchy display

#### 6.3 Filtering & Reporting
- **Use Case:** Show only entities under a parent
- **Feature:** Filter by hierarchy level
- **Implementation:** Add `include_children` parameter to queries

#### 6.4 Permissions & Access Control
- **Use Case:** Restrict access to entity hierarchy
- **Feature:** User permissions per entity branch
- **Implementation:** Future enhancement (not in initial scope)

---

### 7. Testing Checklist

- [ ] Create entity with parent
- [ ] Create entity without parent (root entity)
- [ ] Update entity to change parent
- [ ] Update entity to remove parent (set to NULL)
- [ ] Prevent circular references (entity as own parent)
- [ ] Prevent circular references (descendant as parent)
- [ ] Get entity hierarchy (parent, children, grandchildren)
- [ ] Get children only
- [ ] Get parent only
- [ ] Get all descendants
- [ ] Get root entities
- [ ] Delete parent entity (children become orphaned)
- [ ] Delete entity with children (children become orphaned)

---

### 8. Database Query Examples

#### Get Entity with Parent Info:
```sql
SELECT 
    e.ent_id,
    e.ent_name,
    e.ent_code,
    e.parent_entity_id,
    p.ent_name as parent_name,
    p.ent_code as parent_code
FROM entity_master e
LEFT JOIN entity_master p ON e.parent_entity_id = p.ent_id
WHERE e.ent_id = %s
```

#### Get Direct Children:
```sql
SELECT *
FROM entity_master
WHERE parent_entity_id = %s
ORDER BY ent_name ASC
```

#### Get All Descendants (Recursive CTE - MySQL 8.0+):
```sql
WITH RECURSIVE descendants AS (
    -- Base case: direct children
    SELECT ent_id, ent_name, ent_code, parent_entity_id, 1 as level
    FROM entity_master
    WHERE parent_entity_id = %s
    
    UNION ALL
    
    -- Recursive case: children of children
    SELECT e.ent_id, e.ent_name, e.ent_code, e.parent_entity_id, d.level + 1
    FROM entity_master e
    INNER JOIN descendants d ON e.parent_entity_id = d.ent_id
)
SELECT * FROM descendants ORDER BY level, ent_name;
```

#### Get Root Entities:
```sql
SELECT *
FROM entity_master
WHERE parent_entity_id IS NULL
ORDER BY ent_name ASC
```

---

### 9. Implementation Priority

**Phase 1 (Core Functionality):**
1. ✅ Database migration (add parent_entity_id column)
2. ✅ Update entity CRUD to handle parent_entity_id
3. ✅ Add validation (circular reference prevention)
4. ✅ Update frontend entity form (parent selector)

**Phase 2 (Hierarchy Features):**
5. ✅ Add hierarchy endpoints (children, parent, descendants)
6. ✅ Update entity list to show hierarchy
7. ✅ Add hierarchy view/tree visualization

**Phase 3 (Advanced Features):**
8. ⏳ Consolidated financial reporting
9. ⏳ Hierarchy-based filtering in reports
10. ⏳ Bulk operations (move subtree, etc.)

---

### 10. Example API Request/Response

**Create Entity with Parent:**
```json
POST /entities
{
  "ent_name": "Subsidiary Company",
  "ent_code": "SUB001",
  "lcl_curr": "USD",
  "city": "New York",
  "country": "USA",
  "parent_entity_id": 1
}
```

**Get Entity Hierarchy:**
```json
GET /entities/1/hierarchy

Response:
{
  "success": true,
  "data": {
    "entity": {
      "ent_id": 1,
      "ent_name": "Parent Company",
      "ent_code": "PAR001",
      "parent_entity_id": null
    },
    "parent": null,
    "children": [
      {
        "ent_id": 2,
        "ent_name": "Child Company 1",
        "ent_code": "CHI001",
        "parent_entity_id": 1
      },
      {
        "ent_id": 3,
        "ent_name": "Child Company 2",
        "ent_code": "CHI002",
        "parent_entity_id": 1
      }
    ],
    "grandchildren": [
      {
        "ent_id": 4,
        "ent_name": "Grandchild Company",
        "ent_code": "GRA001",
        "parent_entity_id": 2
      }
    ]
  }
}
```

---

## Summary

To implement parent-child-grandchildren relationships, you need to:

1. **Add `parent_entity_id` column** to `entity_master` table
2. **Update backend APIs** to handle parent relationships
3. **Add validation** to prevent circular references
4. **Add hierarchy endpoints** (children, parent, descendants)
5. **Update frontend** to show and manage hierarchy
6. **Test thoroughly** to ensure data integrity

The implementation is straightforward but requires careful validation to prevent data inconsistencies.


