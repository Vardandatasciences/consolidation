-- ========================================
-- Migration: Create Financial Year Master Table
-- Description: Creates financial_year_master table to store valid financial year ranges
--              This enables validation that data can only be uploaded within configured FY ranges
-- ========================================

USE balance_sheet;

-- ========================================
-- Step 1: Create financial_year_master table
-- ========================================
CREATE TABLE IF NOT EXISTS financial_year_master (
    id INT AUTO_INCREMENT PRIMARY KEY,
    financial_year VARCHAR(10) UNIQUE NOT NULL COMMENT 'Financial year in format "2024-25" (ending year format)',
    start_date DATE NOT NULL COMMENT 'Financial year start date (e.g., 2024-04-01)',
    end_date DATE NOT NULL COMMENT 'Financial year end date (e.g., 2025-03-31)',
    is_active TINYINT(1) DEFAULT 1 COMMENT 'Whether this FY is active for data uploads (1=active, 0=inactive)',
    description VARCHAR(255) NULL COMMENT 'Optional description for this financial year',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT NULL COMMENT 'User ID who created this record',
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_financial_year (financial_year),
    INDEX idx_is_active (is_active),
    INDEX idx_dates (start_date, end_date),
    INDEX idx_active_dates (is_active, start_date, end_date),
    CONSTRAINT chk_dates CHECK (end_date > start_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- Step 2: Insert sample data (optional - for testing)
-- ========================================
-- Uncomment below to insert sample financial years
-- Note: Adjust dates based on your actual financial year conventions

/*
INSERT INTO financial_year_master (financial_year, start_date, end_date, is_active, description, created_by)
VALUES
    ('2023-24', '2023-04-01', '2024-03-31', 1, 'Financial Year 2023-24', 1),
    ('2024-25', '2024-04-01', '2025-03-31', 1, 'Financial Year 2024-25', 1),
    ('2025-26', '2025-04-01', '2026-03-31', 1, 'Financial Year 2025-26', 1)
ON DUPLICATE KEY UPDATE 
    start_date = VALUES(start_date),
    end_date = VALUES(end_date),
    is_active = VALUES(is_active),
    description = VALUES(description);
*/

-- ========================================
-- Verification Queries
-- ========================================

-- Check if table was created successfully
DESCRIBE financial_year_master;

-- Show all indexes
SHOW INDEX FROM financial_year_master;

-- ========================================
-- Example Queries for Common Operations
-- ========================================

-- Query 1: Get all active financial years
-- Use this in list_financial_years() API
SELECT 
    id,
    financial_year,
    start_date,
    end_date,
    is_active,
    description,
    created_at,
    updated_at
FROM financial_year_master
WHERE is_active = 1
ORDER BY start_date DESC;

-- Query 2: Validate if a date falls within any active financial year
-- Use this in validate_date_against_fy_master() function
-- Replace %date% with the date to validate (e.g., '2024-04-15')
SELECT 
    id,
    financial_year,
    start_date,
    end_date,
    is_active
FROM financial_year_master
WHERE is_active = 1
  AND %date% >= start_date
  AND %date% <= end_date
LIMIT 1;

-- Query 3: Get financial year for a specific date
-- Returns the financial year that contains the given date
SELECT 
    financial_year,
    start_date,
    end_date
FROM financial_year_master
WHERE is_active = 1
  AND %date% >= start_date
  AND %date% <= end_date
LIMIT 1;

-- Query 4: Check for overlapping date ranges (for validation before insert/update)
-- Use this to prevent creating financial years with overlapping dates
-- Replace %start_date% and %end_date% with new FY dates
-- Replace %id% with current record ID (NULL for new records)
SELECT COUNT(*) as overlap_count
FROM financial_year_master
WHERE is_active = 1
  AND id != COALESCE(%id%, 0)
  AND (
    (%start_date% BETWEEN start_date AND end_date)
    OR (%end_date% BETWEEN start_date AND end_date)
    OR (start_date BETWEEN %start_date% AND %end_date%)
    OR (end_date BETWEEN %start_date% AND %end_date%)
  );

-- Query 5: Get financial year by ID
-- Use this in get_financial_year() API
SELECT 
    id,
    financial_year,
    start_date,
    end_date,
    is_active,
    description,
    created_at,
    updated_at,
    created_by
FROM financial_year_master
WHERE id = %id%;

-- Query 6: Check if financial year has any data (before deletion)
-- Check if any records exist in final_structured or rawData for this FY
SELECT 
    (SELECT COUNT(*) FROM final_structured WHERE financial_year = %financial_year%) as structured_count,
    (SELECT COUNT(*) FROM `rawData` WHERE financial_year = %financial_year%) as raw_count;

-- Query 7: Get all financial years (active and inactive)
-- Use this in admin view
SELECT 
    id,
    financial_year,
    start_date,
    end_date,
    is_active,
    description,
    created_at,
    updated_at
FROM financial_year_master
ORDER BY start_date DESC;

-- Query 8: Activate/Deactivate financial year
-- Use this in update_financial_year() API
UPDATE financial_year_master
SET is_active = %is_active%,
    updated_at = CURRENT_TIMESTAMP
WHERE id = %id%;

-- Query 9: Get financial years that contain a specific month
-- Replace %year% and %month_name% (e.g., 2024, 'April')
SELECT 
    id,
    financial_year,
    start_date,
    end_date,
    is_active
FROM financial_year_master
WHERE is_active = 1
  AND YEAR(start_date) <= %year%
  AND YEAR(end_date) >= %year%
  AND (
    (MONTH(start_date) <= MONTH(STR_TO_DATE(CONCAT(%year%, '-', %month_name%, '-01'), '%Y-%M-%d')))
    AND (MONTH(end_date) >= MONTH(STR_TO_DATE(CONCAT(%year%, '-', %month_name%, '-01'), '%Y-%M-%d')))
  );

-- ========================================
-- Rollback Script (if needed)
-- ========================================
-- WARNING: Only run if you need to rollback the migration
-- This will remove the financial_year_master table and all data

-- DROP TABLE IF EXISTS financial_year_master;

-- ========================================
-- Notes:
-- ========================================
-- 1. The financial_year field uses format "2024-25" (ending year format)
--    - This matches the format used in entity_forex_rates and final_structured tables
--
-- 2. Date validation:
--    - end_date must be after start_date (enforced by CHECK constraint)
--    - Overlapping date ranges should be prevented in application code
--
-- 3. is_active flag:
--    - Only active financial years allow data uploads
--    - Inactive financial years are kept for historical reference
--
-- 4. Indexes:
--    - idx_financial_year: Fast lookup by financial year string
--    - idx_is_active: Fast filtering of active/inactive FYs
--    - idx_dates: Fast date range queries
--    - idx_active_dates: Optimized for active FY date range queries
--
-- 5. Foreign key:
--    - created_by references users(id)
--    - ON DELETE SET NULL means if user is deleted, created_by becomes NULL
--
-- 6. Before deleting a financial year:
--    - Check if any data exists for that FY
--    - Consider soft delete (set is_active = 0) instead of hard delete

