-- Migration: Add pending_master_items and quarantine_logs tables
-- Created: 2026-02-03
-- Description: Creates tables for the approval workflow system

-- Pending Master Items - staging area for items needing human review
CREATE TABLE IF NOT EXISTS pending_master_items (
    pending_id INT AUTO_INCREMENT PRIMARY KEY,

    -- Item data
    description TEXT NOT NULL,
    description_normalized VARCHAR(500),
    sec_code VARCHAR(20),
    unit_standard VARCHAR(20),

    -- Source tracking
    source_file_id INT,
    original_description TEXT,

    -- Gatekeeper validation results
    quality_score FLOAT,
    quality_reasons TEXT,  -- JSON array of reasons
    quality_indicators TEXT,  -- JSON dict of indicator results

    -- Review status: PENDING, APPROVED, REJECTED
    status VARCHAR(20) DEFAULT 'PENDING',

    -- Review info
    reviewed_by INT,
    reviewed_at TIMESTAMP NULL,
    review_notes TEXT,

    -- If approved, link to created master item
    master_id INT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (source_file_id) REFERENCES boq_files(file_id) ON DELETE SET NULL,
    FOREIGN KEY (reviewed_by) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (master_id) REFERENCES master_work_items(master_id) ON DELETE SET NULL,

    INDEX idx_pending_status (status),
    INDEX idx_pending_score (quality_score),
    INDEX idx_pending_created (created_at)
);

-- Quarantine Logs - rejected items for analysis
CREATE TABLE IF NOT EXISTS quarantine_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,

    -- Original data
    description TEXT,
    description_normalized VARCHAR(500),
    source_file_id INT,

    -- Rejection info
    rejection_reason VARCHAR(500),
    quality_score FLOAT,
    matched_forbidden_pattern VARCHAR(100),
    quality_indicators TEXT,  -- JSON dict of indicator results

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (source_file_id) REFERENCES boq_files(file_id) ON DELETE SET NULL,

    INDEX idx_quarantine_file (source_file_id),
    INDEX idx_quarantine_created (created_at),
    INDEX idx_quarantine_reason (rejection_reason)
);
