-- ========================================
-- Migration: Monthly Forex Rates Tracking
-- Adds monthly rate history to preserve historical accuracy
-- ========================================

USE balance_sheet;

-- ========================================
-- Create entity_forex_monthly_rates table
-- ========================================
CREATE TABLE IF NOT EXISTS entity_forex_monthly_rates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entity_id INT NOT NULL,
    currency VARCHAR(10) NOT NULL,
    financial_year INT NOT NULL,
    month_number INT NOT NULL COMMENT 'Month number in financial year (1-12)',
    month_name VARCHAR(20) NOT NULL COMMENT 'Month name (e.g., "April", "May")',
    rate DECIMAL(18,6) NOT NULL COMMENT 'Exchange rate for this month',
    effective_date DATE NULL COMMENT 'Date when rate was effective',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT NULL,
    FOREIGN KEY (entity_id) REFERENCES entity_master(ent_id) ON DELETE CASCADE,
    UNIQUE KEY uk_entity_currency_fy_month (entity_id, currency, financial_year, month_number),
    INDEX idx_entity_id (entity_id),
    INDEX idx_financial_year (financial_year),
    INDEX idx_currency (currency),
    INDEX idx_month (month_number),
    INDEX idx_fy_month (financial_year, month_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add foreign key constraint on created_by only if users table exists and has id column
-- Note: This is optional since created_by can be NULL
-- If you need this constraint, ensure users table exists with id column first
-- ALTER TABLE entity_forex_monthly_rates 
-- ADD CONSTRAINT fk_monthly_forex_created_by 
-- FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

-- ========================================
-- Migrate existing closing rates to monthly rates
-- This creates monthly rate records from existing entity_forex_rates
-- ========================================

-- Note: This migration assumes existing closing_rate values should be used for the final month
-- You may need to manually adjust monthly rates after migration

-- ========================================
-- Verification Queries
-- ========================================
-- Check table exists
SELECT COUNT(*) as table_exists
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'balance_sheet' 
  AND TABLE_NAME = 'entity_forex_monthly_rates';

-- Show table structure
DESCRIBE entity_forex_monthly_rates;

