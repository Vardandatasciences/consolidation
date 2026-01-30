-- Migration: Update financial_year format to "2024-25" style
-- This migration:
-- 1. Adds financial_year column to final_structured (if not exists)
-- 2. Adds financial_year column to rawData (if not exists)
-- 3. Updates entity_forex_rates.financial_year to VARCHAR to support "2024-25" format

-- Add financial_year column to final_structured
ALTER TABLE final_structured 
ADD COLUMN IF NOT EXISTS financial_year VARCHAR(10) NULL COMMENT 'Financial year in format "2024-25" (ending year format)';

-- Add financial_year column to rawData
ALTER TABLE `rawData` 
ADD COLUMN IF NOT EXISTS `financial_year` VARCHAR(10) NULL COMMENT 'Financial year in format "2024-25" (ending year format)';

-- Update entity_forex_rates.financial_year to VARCHAR if it's currently INT
-- Note: This will preserve existing data, but you may need to convert existing values
ALTER TABLE entity_forex_rates 
MODIFY COLUMN financial_year VARCHAR(10) NOT NULL COMMENT 'Financial year in format "2024-25" (ending year format)';

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_final_structured_financial_year ON final_structured(financial_year);
CREATE INDEX IF NOT EXISTS idx_rawData_financial_year ON `rawData`(`financial_year`);




