-- Migration: 001_price_history
-- Description: Create price_history table for tracking historical prices per master item
-- Date: 2026-02-03

-- Price History Table
-- Tracks individual price records from different projects/files
CREATE TABLE IF NOT EXISTS price_history (
    price_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    master_item_id INT NOT NULL,
    file_id INT NOT NULL,
    project_id INT NOT NULL,
    unit_price DECIMAL(18, 2) NOT NULL,
    quantity DECIMAL(18, 4),
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    region VARCHAR(100),
    project_type ENUM('residential', 'commercial', 'industrial', 'infrastructure'),

    -- Indexes for efficient queries
    INDEX idx_price_master (master_item_id),
    INDEX idx_price_project (project_id),
    INDEX idx_price_file (file_id),
    INDEX idx_price_recorded_at (recorded_at),
    INDEX idx_price_history_composite (master_item_id, recorded_at DESC),

    -- Foreign Keys
    CONSTRAINT fk_price_master FOREIGN KEY (master_item_id)
        REFERENCES master_work_items(master_id) ON DELETE CASCADE,
    CONSTRAINT fk_price_file FOREIGN KEY (file_id)
        REFERENCES boq_files(file_id) ON DELETE CASCADE,
    CONSTRAINT fk_price_project FOREIGN KEY (project_id)
        REFERENCES projects(project_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add comment
ALTER TABLE price_history COMMENT = 'Stores historical price data for master work items from different projects';
