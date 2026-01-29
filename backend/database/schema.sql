-- BOQ System Database Schema
-- MySQL 8.0+
-- Version: 2.0.0

-- Set character set and collation
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- ====================================
-- TABLE: users
-- ====================================
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    hashed_password VARCHAR(255) NOT NULL,
    role ENUM('viewer', 'editor', 'admin', 'super_admin') DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================
-- TABLE: projects
-- ====================================
CREATE TABLE IF NOT EXISTS projects (
    project_id INT AUTO_INCREMENT PRIMARY KEY,
    project_code VARCHAR(50) UNIQUE NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    project_type ENUM('residential', 'commercial', 'industrial', 'infrastructure') NOT NULL,
    location VARCHAR(255),
    client_name VARCHAR(255),
    contract_value DECIMAL(18,2),
    start_date DATE,
    status ENUM('active', 'completed', 'cancelled') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_project_code (project_code),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================
-- TABLE: sec_codes
-- ====================================
CREATE TABLE IF NOT EXISTS sec_codes (
    sec_code VARCHAR(20) PRIMARY KEY,
    sec_name_vi VARCHAR(255) NOT NULL,
    sec_name_en VARCHAR(255),
    parent_code VARCHAR(20),
    level TINYINT DEFAULT 1,
    keywords JSON,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (parent_code) REFERENCES sec_codes(sec_code) ON DELETE SET NULL,
    INDEX idx_parent (parent_code),
    INDEX idx_level (level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================
-- TABLE: boq_files
-- ====================================
CREATE TABLE IF NOT EXISTS boq_files (
    file_id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_hash CHAR(64) UNIQUE,
    file_path VARCHAR(500),
    total_rows INT DEFAULT 0,
    total_amount DECIMAL(18,2) DEFAULT 0,
    status ENUM('draft', 'approved') DEFAULT 'draft',
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by INT,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_project (project_id),
    INDEX idx_hash (file_hash),
    INDEX idx_uploaded_at (uploaded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================
-- TABLE: line_items
-- ====================================
CREATE TABLE IF NOT EXISTS line_items (
    line_item_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    file_id INT NOT NULL,
    project_id INT NOT NULL,
    `row_number` INT NOT NULL,
    description TEXT NOT NULL,
    unit VARCHAR(10),
    quantity DECIMAL(18,4),
    unit_price DECIMAL(18,2),
    amount DECIMAL(18,2),
    sec_code VARCHAR(20),
    confidence_score DECIMAL(5,2),
    classification_method ENUM('auto', 'manual') DEFAULT 'auto',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES boq_files(file_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (sec_code) REFERENCES sec_codes(sec_code) ON DELETE SET NULL,
    INDEX idx_file (file_id),
    INDEX idx_project (project_id),
    INDEX idx_sec_code (sec_code),
    INDEX idx_confidence (confidence_score),
    FULLTEXT idx_description (description)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================
-- TABLE: audit_logs
-- ====================================
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INT,
    old_value JSON,
    new_value JSON,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_user (user_id),
    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================
-- VIEWS
-- ====================================

-- Project summary view
CREATE OR REPLACE VIEW v_project_summary AS
SELECT 
    p.project_id,
    p.project_code,
    p.project_name,
    p.project_type,
    p.location,
    p.client_name,
    p.contract_value,
    p.status,
    p.created_at,
    COUNT(DISTINCT f.file_id) as total_files,
    COUNT(DISTINCT li.line_item_id) as total_items,
    COALESCE(SUM(li.amount), 0) as total_amount
FROM projects p
LEFT JOIN boq_files f ON p.project_id = f.project_id
LEFT JOIN line_items li ON p.project_id = li.project_id
GROUP BY p.project_id;

-- Line items with SEC hierarchy
CREATE OR REPLACE VIEW v_line_items_detailed AS
SELECT 
    li.line_item_id,
    li.file_id,
    li.project_id,
    p.project_code,
    p.project_name,
    li.`row_number`,
    li.description,
    li.unit,
    li.quantity,
    li.unit_price,
    li.amount,
    li.sec_code,
    s.sec_name_vi,
    s.sec_name_en,
    s.parent_code,
    li.confidence_score,
    li.classification_method,
    li.created_at,
    li.updated_at
FROM line_items li
LEFT JOIN projects p ON li.project_id = p.project_id
LEFT JOIN sec_codes s ON li.sec_code = s.sec_code;

-- ====================================
-- INITIAL DATA
-- ====================================

-- Insert default admin user (password: admin123)
-- Hash generated with bcrypt
INSERT IGNORE INTO users (username, email, full_name, hashed_password, role) VALUES
('admin', 'admin@boqsystem.com', 'System Administrator', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeJhiPm.4VW6', 'super_admin');

-- Sample SEC codes (Level 1)
INSERT IGNORE INTO sec_codes (sec_code, sec_name_vi, sec_name_en, level, keywords, is_active) VALUES
('SEC-00', 'Chi phí chung & Chuẩn bị', 'Preliminaries & General', 1, '["chuẩn bị", "chi phí chung", "preliminaries"]', TRUE),
('SEC-01', 'Phần Ngầm (Substructure)', 'Substructure', 1, '["ngầm", "substructure", "foundation"]', TRUE),
('SEC-02', 'Phần Thân (Superstructure)', 'Superstructure', 1, '["thân", "superstructure", "structure"]', TRUE),
('SEC-03', 'Kiến trúc & Hoàn thiện', 'Architecture & Finishes', 1, '["kiến trúc", "hoàn thiện", "architecture", "finishes"]', TRUE),
('SEC-04', 'Hệ thống MEP', 'MEP Systems', 1, '["MEP", "cơ điện", "mechanical", "electrical"]', TRUE),
('SEC-05', 'Cảnh quan & Ngoại thất', 'Landscape & External Works', 1, '["cảnh quan", "landscape", "external"]', TRUE);

-- SEC codes Level 2 (SEC-01 children)
INSERT IGNORE INTO sec_codes (sec_code, sec_name_vi, sec_name_en, parent_code, level, keywords, is_active) VALUES
('SEC-01-01', 'Công tác đất', 'Earthworks', 'SEC-01', 2, '["đào đất", "đắp đất", "earthwork", "excavation"]', TRUE),
('SEC-01-02', 'Cọc', 'Piling', 'SEC-01', 2, '["cọc", "pile", "piling"]', TRUE),
('SEC-01-03', 'Móng', 'Foundation', 'SEC-01', 2, '["móng", "foundation"]', TRUE);

-- More SEC codes can be added via seed.sql
