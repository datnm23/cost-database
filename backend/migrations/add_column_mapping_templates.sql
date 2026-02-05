-- Migration: Add column_mapping_templates and template_usage_logs tables
-- Created: 2026-02-04
-- Description: Creates tables for storing and reusing column mapping configurations

CREATE TABLE IF NOT EXISTS column_mapping_templates (
    template_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    column_mapping JSON NOT NULL,           -- {"original_col": "standard_col"}
    header_row_hint INT DEFAULT 0,
    sheet_name_pattern VARCHAR(100),
    fingerprint VARCHAR(64) NOT NULL,       -- SHA256 hash
    fingerprint_components JSON,            -- Detailed parts for fuzzy matching
    use_count INT DEFAULT 0,
    last_used_at TIMESTAMP NULL,
    match_success_rate DECIMAL(5,2) DEFAULT 100.00,
    created_by INT,
    visibility ENUM('private', 'team', 'public') DEFAULT 'private',
    is_system BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_fingerprint (fingerprint),
    INDEX idx_visibility (visibility),
    INDEX idx_active (is_active),
    UNIQUE INDEX idx_name_owner (name, created_by)
);

CREATE TABLE IF NOT EXISTS template_usage_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    template_id INT NOT NULL,
    file_id INT,
    match_score DECIMAL(5,2),
    match_type ENUM('exact', 'fuzzy', 'manual') NOT NULL,
    was_successful BOOLEAN DEFAULT TRUE,
    columns_mapped INT,
    columns_total INT,
    user_id INT,
    action ENUM('auto_applied', 'user_selected', 'user_modified') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (template_id) REFERENCES column_mapping_templates(template_id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES boq_files(file_id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_template (template_id),
    INDEX idx_file (file_id),
    INDEX idx_user (user_id)
);
