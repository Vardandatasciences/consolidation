-- Simple version: Create financial_year_master table without foreign key
-- Run this if you're getting foreign key errors

USE balance_sheet;

CREATE TABLE IF NOT EXISTS financial_year_master (
    id INT AUTO_INCREMENT PRIMARY KEY,
    financial_year VARCHAR(10) UNIQUE NOT NULL COMMENT 'Financial year in format "2024-25"',
    start_date DATE NOT NULL COMMENT 'Financial year start date',
    end_date DATE NOT NULL COMMENT 'Financial year end date',
    is_active TINYINT(1) DEFAULT 1 COMMENT '1=active, 0=inactive',
    description VARCHAR(255) NULL COMMENT 'Optional description',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT NULL COMMENT 'User ID (optional, no foreign key)',
    INDEX idx_financial_year (financial_year),
    INDEX idx_is_active (is_active),
    INDEX idx_dates (start_date, end_date),
    INDEX idx_active_dates (is_active, start_date, end_date),
    CONSTRAINT chk_dates CHECK (end_date > start_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Verify table was created
DESCRIBE financial_year_master;
