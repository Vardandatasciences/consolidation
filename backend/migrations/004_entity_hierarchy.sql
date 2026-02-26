-- ========================================
-- Migration: Add Parent-Child Relationship to Entities
-- Description: Adds parent_entity_id column to entity_master table
--              to support parent-child-grandchildren relationships
-- ========================================

USE balance_sheet;

-- ========================================
-- Step 1: Add parent_entity_id column
-- ========================================
ALTER TABLE entity_master
ADD COLUMN parent_entity_id INT NULL COMMENT 'Reference to parent entity (ent_id). NULL means this is a root entity.';

-- ========================================
-- Step 2: Add index for better query performance
-- ========================================
ALTER TABLE entity_master
ADD INDEX idx_parent_entity (parent_entity_id);

-- ========================================
-- Step 3: Add foreign key constraint
-- ========================================
ALTER TABLE entity_master
ADD CONSTRAINT fk_entity_parent 
FOREIGN KEY (parent_entity_id) 
REFERENCES entity_master(ent_id) 
ON DELETE SET NULL
ON UPDATE CASCADE;

-- ========================================
-- Verification Queries
-- ========================================

-- Check if column was added successfully
DESCRIBE entity_master;

-- Show all indexes on entity_master table
SHOW INDEX FROM entity_master WHERE Key_name = 'idx_parent_entity';

-- Show foreign key constraints
SELECT 
    CONSTRAINT_NAME,
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'entity_master'
  AND CONSTRAINT_NAME = 'fk_entity_parent';

-- ========================================
-- Example Queries for Common Operations
-- ========================================

-- Query 1: Get all entities with their parent information
-- Use this in your list_entities() API
SELECT 
    e.ent_id,
    e.ent_name,
    e.ent_code,
    e.lcl_curr,
    e.city,
    e.country,
    e.financial_year_start_month,
    e.financial_year_start_day,
    e.parent_entity_id,
    p.ent_name as parent_name,
    p.ent_code as parent_code
FROM entity_master e
LEFT JOIN entity_master p ON e.parent_entity_id = p.ent_id
ORDER BY e.ent_name ASC;

-- Query 2: Get direct children of an entity
-- Use this in get_children() API
-- Replace %s with the parent entity_id
SELECT 
    ent_id,
    ent_name,
    ent_code,
    lcl_curr,
    city,
    country,
    financial_year_start_month,
    financial_year_start_day,
    parent_entity_id
FROM entity_master
WHERE parent_entity_id = %s
ORDER BY ent_name ASC;

-- Query 3: Get parent entity
-- Use this in get_parent() API
-- Replace %s with the child entity_id
SELECT 
    p.ent_id,
    p.ent_name,
    p.ent_code,
    p.lcl_curr,
    p.city,
    p.country,
    p.financial_year_start_month,
    p.financial_year_start_day,
    p.parent_entity_id
FROM entity_master e
INNER JOIN entity_master p ON e.parent_entity_id = p.ent_id
WHERE e.ent_id = %s;

-- Query 4: Get all root entities (entities with no parent)
-- Use this in get_root_entities() API
SELECT 
    ent_id,
    ent_name,
    ent_code,
    lcl_curr,
    city,
    country,
    financial_year_start_month,
    financial_year_start_day,
    parent_entity_id
FROM entity_master
WHERE parent_entity_id IS NULL
ORDER BY ent_name ASC;

-- Query 5: Get entity with all direct children (hierarchy level 1)
-- Use this in get_hierarchy() API for immediate children
SELECT 
    e.ent_id,
    e.ent_name,
    e.ent_code,
    e.lcl_curr,
    e.city,
    e.country,
    e.financial_year_start_month,
    e.financial_year_start_day,
    e.parent_entity_id,
    c.ent_id as child_id,
    c.ent_name as child_name,
    c.ent_code as child_code
FROM entity_master e
LEFT JOIN entity_master p ON e.parent_entity_id = p.ent_id
LEFT JOIN entity_master c ON c.parent_entity_id = e.ent_id
WHERE e.ent_id = %s;

-- Query 6: Count children for each entity
SELECT 
    parent_entity_id,
    COUNT(*) as child_count
FROM entity_master
WHERE parent_entity_id IS NOT NULL
GROUP BY parent_entity_id;

-- Query 7: Find entities with no children (leaf nodes)
SELECT 
    e.ent_id,
    e.ent_name,
    e.ent_code
FROM entity_master e
LEFT JOIN entity_master c ON c.parent_entity_id = e.ent_id
WHERE c.ent_id IS NULL
ORDER BY e.ent_name ASC;

-- Query 8: Get all descendants using recursive CTE (MySQL 8.0+)
-- Use this in get_descendants() API
-- Note: This requires MySQL 8.0 or higher
WITH RECURSIVE descendants AS (
    -- Base case: direct children
    SELECT 
        ent_id, 
        ent_name, 
        ent_code, 
        lcl_curr,
        city,
        country,
        financial_year_start_month,
        financial_year_start_day,
        parent_entity_id, 
        1 as level
    FROM entity_master
    WHERE parent_entity_id = %s  -- Replace %s with root entity_id
    
    UNION ALL
    
    -- Recursive case: children of children
    SELECT 
        e.ent_id, 
        e.ent_name, 
        e.ent_code,
        e.lcl_curr,
        e.city,
        e.country,
        e.financial_year_start_month,
        e.financial_year_start_day,
        e.parent_entity_id, 
        d.level + 1 as level
    FROM entity_master e
    INNER JOIN descendants d ON e.parent_entity_id = d.ent_id
)
SELECT * FROM descendants ORDER BY level, ent_name;

-- Query 9: Get full hierarchy tree (entity + children + grandchildren)
-- Use this in get_hierarchy() API
-- This gets the entity, its parent, direct children, and grandchildren
SELECT 
    -- Entity itself
    e.ent_id,
    e.ent_name,
    e.ent_code,
    e.parent_entity_id as entity_parent_id,
    -- Parent info
    p.ent_id as parent_id,
    p.ent_name as parent_name,
    p.ent_code as parent_code,
    -- Children info
    c.ent_id as child_id,
    c.ent_name as child_name,
    c.ent_code as child_code,
    -- Grandchildren info
    gc.ent_id as grandchild_id,
    gc.ent_name as grandchild_name,
    gc.ent_code as grandchild_code
FROM entity_master e
LEFT JOIN entity_master p ON e.parent_entity_id = p.ent_id
LEFT JOIN entity_master c ON c.parent_entity_id = e.ent_id
LEFT JOIN entity_master gc ON gc.parent_entity_id = c.ent_id
WHERE e.ent_id = %s;  -- Replace %s with entity_id

-- Query 10: Validate no circular references (for validation function)
-- Check if an entity_id is in the descendants of another entity_id
-- Returns 1 if circular reference would occur, 0 otherwise
-- Usage: Check if setting entity B as parent of entity A would create a cycle
--        by checking if A is a descendant of B
WITH RECURSIVE descendants AS (
    SELECT ent_id, parent_entity_id
    FROM entity_master
    WHERE ent_id = %s  -- Replace %s with potential_child_id
    
    UNION ALL
    
    SELECT e.ent_id, e.parent_entity_id
    FROM entity_master e
    INNER JOIN descendants d ON e.ent_id = d.parent_entity_id
)
SELECT COUNT(*) as is_descendant
FROM descendants
WHERE ent_id = %s;  -- Replace %s with potential_parent_id
-- If result > 0, then potential_parent is a descendant of potential_child (CIRCULAR REFERENCE!)

-- Query 11: Get entity depth (how many levels deep)
-- Count how many ancestors an entity has
WITH RECURSIVE ancestors AS (
    -- Start with the entity
    SELECT ent_id, parent_entity_id, 0 as depth
    FROM entity_master
    WHERE ent_id = %s  -- Replace %s with entity_id
    
    UNION ALL
    
    -- Go up to parent
    SELECT e.ent_id, e.parent_entity_id, a.depth + 1
    FROM entity_master e
    INNER JOIN ancestors a ON e.ent_id = a.parent_entity_id
)
SELECT MAX(depth) as entity_depth FROM ancestors;

-- Query 12: Get complete hierarchy path (breadcrumb)
-- Returns all ancestors from root to entity
WITH RECURSIVE path AS (
    -- Start with the entity
    SELECT ent_id, ent_name, ent_code, parent_entity_id, 0 as level
    FROM entity_master
    WHERE ent_id = %s  -- Replace %s with entity_id
    
    UNION ALL
    
    -- Go up to parent
    SELECT e.ent_id, e.ent_name, e.ent_code, e.parent_entity_id, p.level + 1
    FROM entity_master e
    INNER JOIN path p ON e.ent_id = p.parent_entity_id
)
SELECT ent_id, ent_name, ent_code, level 
FROM path 
ORDER BY level DESC;  -- Root first, then parent, then entity

-- Query 13: Find entities that would create cycles if set as parent
-- Before updating entity A's parent to B, check if B is a descendant of A
-- Replace %child_id% with the entity being updated
-- Replace %parent_id% with the new parent_id
WITH RECURSIVE descendants AS (
    SELECT ent_id
    FROM entity_master
    WHERE ent_id = %child_id%  -- The entity being updated
    
    UNION ALL
    
    SELECT e.ent_id
    FROM entity_master e
    INNER JOIN descendants d ON e.parent_entity_id = d.ent_id
)
SELECT COUNT(*) as would_create_cycle
FROM descendants
WHERE ent_id = %parent_id%;  -- New parent ID
-- If result > 0, DO NOT ALLOW this parent assignment (circular reference)

-- Query 14: Get entity count by hierarchy level
SELECT 
    CASE 
        WHEN parent_entity_id IS NULL THEN 'Root (Level 0)'
        ELSE CONCAT('Level ', 
            (SELECT COUNT(*) 
             FROM entity_master e2 
             WHERE e2.ent_id = e1.parent_entity_id 
             AND e2.parent_entity_id IS NOT NULL) + 1)
    END as hierarchy_level,
    COUNT(*) as entity_count
FROM entity_master e1
GROUP BY 
    CASE 
        WHEN parent_entity_id IS NULL THEN 'Root (Level 0)'
        ELSE CONCAT('Level ', 
            (SELECT COUNT(*) 
             FROM entity_master e2 
             WHERE e2.ent_id = e1.parent_entity_id 
             AND e2.parent_entity_id IS NOT NULL) + 1)
    END;

-- Query 15: Update entity parent (example)
-- Use this in update_entity() API
-- Replace %new_parent_id% with new parent entity_id (can be NULL)
-- Replace %entity_id% with entity being updated
UPDATE entity_master
SET parent_entity_id = %new_parent_id%
WHERE ent_id = %entity_id%;

-- Query 16: Remove parent (set to NULL - make it a root entity)
UPDATE entity_master
SET parent_entity_id = NULL
WHERE ent_id = %entity_id%;

-- Query 17: Get all entities in a hierarchy branch (all descendants + the root)
-- Useful for filtering data by hierarchy
WITH RECURSIVE branch AS (
    -- Start with root entity
    SELECT ent_id, ent_name, ent_code, parent_entity_id
    FROM entity_master
    WHERE ent_id = %root_entity_id%  -- Replace with root entity_id
    
    UNION ALL
    
    -- Get all descendants
    SELECT e.ent_id, e.ent_name, e.ent_code, e.parent_entity_id
    FROM entity_master e
    INNER JOIN branch b ON e.parent_entity_id = b.ent_id
)
SELECT * FROM branch ORDER BY ent_name;

-- ========================================
-- Rollback Script (if needed)
-- ========================================
-- WARNING: Only run if you need to rollback the migration
-- This will remove the parent_entity_id column and all related constraints

-- Step 1: Drop foreign key constraint
-- ALTER TABLE entity_master DROP FOREIGN KEY fk_entity_parent;

-- Step 2: Drop index
-- ALTER TABLE entity_master DROP INDEX idx_parent_entity;

-- Step 3: Drop column
-- ALTER TABLE entity_master DROP COLUMN parent_entity_id;

-- ========================================
-- Notes:
-- ========================================
-- 1. The foreign key uses ON DELETE SET NULL, meaning:
--    - If a parent entity is deleted, children become orphaned (parent_entity_id = NULL)
--    - Children are NOT automatically deleted
--
-- 2. The foreign key uses ON UPDATE CASCADE, meaning:
--    - If a parent entity's ent_id changes, children's parent_entity_id updates automatically
--    - (Note: ent_id is AUTO_INCREMENT PRIMARY KEY, so this shouldn't normally happen)
--
-- 3. Queries using WITH RECURSIVE require MySQL 8.0 or higher
--    - For MySQL 5.7 or lower, use application-level recursion instead
--
-- 4. Always validate parent-child relationships in application code:
--    - Prevent entity from being its own parent
--    - Prevent circular references (descendant as parent)
--    - Consider maximum hierarchy depth
--
-- 5. Index on parent_entity_id improves query performance for:
--    - Finding children of an entity
--    - Finding parent of an entity
--    - Filtering by hierarchy level



