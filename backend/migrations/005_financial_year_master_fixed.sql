-- ========================================
-- Migration: Create Financial Year Master Table (Fixed Version)
-- Description: Creates financial_year_master table
--              This version handles cases where users table might not exist
-- ========================================

USE balance_sheet;

-- ========================================
-- Step 1: Create financial_year_master table WITHOUT foreign key first
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
    INDEX idx_financial_year (financial_year),
    INDEX idx_is_active (is_active),
    INDEX idx_dates (start_date, end_date),
    INDEX idx_active_dates (is_active, start_date, end_date),
    CONSTRAINT chk_dates CHECK (end_date > start_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- Step 2: Add foreign key constraint (only if users table exists with id column)
-- ========================================
-- Check if users table exists and has id column, then add foreign key
SET @table_exists = (
    SELECT COUNT(*) 
    FROM information_schema.tables 
    WHERE table_schema = DATABASE() 
    AND table_name = 'users'
);

SET @column_exists = (
    SELECT COUNT(*) 
    FROM information_schema.columns 
    WHERE table_schema = DATABASE() 
    AND table_name = 'users' 
    AND column_name = 'id'
);

-- Only add foreign key if both table and column exist
SET @sql = IF(
    @table_exists > 0 AND @column_exists > 0,
    'ALTER TABLE financial_year_master ADD CONSTRAINT fk_fy_master_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL',
    'SELECT "Skipping foreign key: users table or id column does not exist" AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ========================================
-- Verification
-- ========================================
DESCRIBE financial_year_master;
