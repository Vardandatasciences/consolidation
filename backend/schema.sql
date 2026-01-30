-- ========================================
-- Database Schema for Balance Sheet Application
-- ========================================

USE balance_sheet;

-- ========================================
-- Users Table
-- ========================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role ENUM('admin', 'user', 'viewer') DEFAULT 'user',
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, password, full_name, role, is_active) 
VALUES (
    'admin',
    'admin@vardaan.com',
    'scrypt:32768:8:1$FqhV0Q8yRMJmQFDH$3e5b5f5d5c5e5f5d5c5e5f5d5c5e5f5d5c5e5f5d5c5e5f5d5c5e5f5d5c5e5f5d5c5e5f5d5c5e5f5d5c5e5f5d',
    'System Administrator',
    'admin',
    1
) ON DUPLICATE KEY UPDATE username = username;

-- Insert demo user (password: demo123)
INSERT INTO users (username, email, password, full_name, role, is_active) 
VALUES (
    'demo',
    'demo@vardaan.com',
    'scrypt:32768:8:1$FqhV0Q8yRMJmQFDH$3e5b5f5d5c5e5f5d5c5e5f5d5c5e5f5d5c5e5f5d5c5e5f5d5c5e5f5d5c5e5f5d5c5e5f5d5c5e5f5d5c5e5f5d',
    'Demo User',
    'user',
    1
) ON DUPLICATE KEY UPDATE username = username;

-- ========================================
-- Entity Master Table (if not exists)
-- ========================================
CREATE TABLE IF NOT EXISTS entity_master (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entity_code VARCHAR(50) UNIQUE NOT NULL,
    entity_name VARCHAR(200) NOT NULL,
    industry VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India',
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_entity_code (entity_code),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- Display all tables
-- ========================================
SHOW TABLES;

-- Display users table structure
DESCRIBE users;

