-- Fix rawData table structure to match expected schema
-- Run this SQL script on your database

USE balance_sheet;

-- First, check current structure
DESCRIBE rawData;

-- Option 1: Simple approach - Just add the columns (will error if they exist, that's okay)
-- Run these one at a time and ignore errors if columns already exist

-- Add Month column after EntityID
ALTER TABLE `rawData` ADD COLUMN `Month` VARCHAR(45) NULL AFTER `EntityID`;

-- Add Year column after Month  
ALTER TABLE `rawData` ADD COLUMN `Year` INT NULL AFTER `Month`;

-- Optional: Remove PeriodID if you don't need it anymore
-- ALTER TABLE `rawData` DROP COLUMN `PeriodID`;

-- Verify the final structure
DESCRIBE rawData;

-- Expected columns:
-- RecordID (bigint AI PK)
-- EntityID (int)
-- Month (varchar(45))
-- Year (int)
-- Particular (varchar(255))
-- OpeningBalance (decimal(18,2))
-- Transactions (decimal(18,2))
-- ClosingBalance (decimal(18,2))
-- created_at (datetime)

