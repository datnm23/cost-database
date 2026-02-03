-- Migration: 003_versions_flags
-- Description: Create boq_versions and line_item_flags tables
-- Date: 2026-02-03

-- BOQ Versions Table
-- Tracks different versions of BOQ for comparison
CREATE TABLE IF NOT EXISTS boq_versions (
    version_id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    version_number INT NOT NULL,
    version_name VARCHAR(100),
    file_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,

    -- Unique constraint: one version number per project
    UNIQUE KEY uk_project_version (project_id, version_number),

    -- Indexes
    INDEX idx_version_project (project_id),
    INDEX idx_version_file (file_id),

    -- Foreign Keys
    CONSTRAINT fk_version_project FOREIGN KEY (project_id)
        REFERENCES projects(project_id) ON DELETE CASCADE,
    CONSTRAINT fk_version_file FOREIGN KEY (file_id)
        REFERENCES boq_files(file_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Line Item Flags Table
-- Quick notes/flags for line items during review
CREATE TABLE IF NOT EXISTS line_item_flags (
    flag_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    line_item_id BIGINT NOT NULL,
    flag_type ENUM('price_warning', 'needs_verify', 'confirmed', 'important', 'question') NOT NULL,
    note TEXT,
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_flag_item (line_item_id),
    INDEX idx_flag_type (flag_type),
    INDEX idx_flag_created_by (created_by),

    -- Foreign Keys
    CONSTRAINT fk_flag_line_item FOREIGN KEY (line_item_id)
        REFERENCES line_items(line_item_id) ON DELETE CASCADE,
    CONSTRAINT fk_flag_user FOREIGN KEY (created_by)
        REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add comments
ALTER TABLE boq_versions COMMENT = 'Tracks BOQ file versions for comparison';
ALTER TABLE line_item_flags COMMENT = 'Quick notes and flags for line item review';
