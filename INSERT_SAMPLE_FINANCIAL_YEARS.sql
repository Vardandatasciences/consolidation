-- ========================================
-- Insert Sample Financial Years for Testing
-- ========================================
-- This script adds multiple financial years to test the validation feature

USE balance_sheet;

-- Insert multiple financial years (2023-24, 2024-25, 2025-26, 2026-27)
-- Adjust the dates based on your actual financial year convention (typically April to March)

INSERT INTO financial_year_master (financial_year, start_date, end_date, is_active, description, created_by)
VALUES
    -- FY 2023-24 (April 2023 to March 2024)
    ('2023-24', '2023-04-01', '2024-03-31', 1, 'Financial Year 2023-24', 1),
    
    -- FY 2024-25 (April 2024 to March 2025)
    ('2024-25', '2024-04-01', '2025-03-31', 1, 'Financial Year 2024-25', 1),
    
    -- FY 2025-26 (April 2025 to March 2026)
    ('2025-26', '2025-04-01', '2026-03-31', 1, 'Financial Year 2025-26', 1),
    
    -- FY 2026-27 (April 2026 to March 2027)
    ('2026-27', '2026-04-01', '2027-03-31', 1, 'Financial Year 2026-27', 1),
    
    -- FY 2027-28 (April 2027 to March 2028)
    ('2027-28', '2027-04-01', '2028-03-31', 1, 'Financial Year 2027-28', 1)
ON DUPLICATE KEY UPDATE 
    start_date = VALUES(start_date),
    end_date = VALUES(end_date),
    is_active = VALUES(is_active),
    description = VALUES(description);

-- Verify the inserted data
SELECT 
    id,
    financial_year,
    start_date,
    end_date,
    is_active,
    description
FROM financial_year_master
WHERE is_active = 1
ORDER BY start_date DESC;

-- ========================================
-- Test Scenarios After Inserting:
-- ========================================
-- 1. Try uploading data for FY 2024-25 → Should work (exists in master data)
-- 2. Try uploading data for FY 2025-26 → Should work (exists in master data)
-- 3. Try uploading data for FY 2022-23 → Should FAIL (before earliest configured FY 2023-24)
-- 4. Try uploading data for FY 2028-29 → Should FAIL (after latest configured FY, but not in master data)
-- 5. Try uploading data for April 2026 → Should FAIL (FY 2026-27 exists, but April 2026 is before it starts)
