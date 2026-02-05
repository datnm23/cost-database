-- Migration: Add master_synonyms table
-- Created: 2026-02-03
-- Description: Creates the synonyms table for master work items

CREATE TABLE IF NOT EXISTS master_synonyms (
    synonym_id INT AUTO_INCREMENT PRIMARY KEY,
    master_id INT NOT NULL,
    synonym_text VARCHAR(500) NOT NULL,
    synonym_normalized VARCHAR(500),
    synonym_type ENUM('alias', 'abbreviation', 'regional', 'english') DEFAULT 'alias',
    is_active BOOLEAN DEFAULT TRUE,
    added_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (master_id) REFERENCES master_work_items(master_id) ON DELETE CASCADE,
    FOREIGN KEY (added_by) REFERENCES users(user_id) ON DELETE SET NULL,

    INDEX idx_synonym_normalized (synonym_normalized),
    INDEX idx_synonym_master (master_id),
    INDEX idx_synonym_active (is_active)
);

-- Add some sample synonyms for common Vietnamese construction terms
-- INSERT INTO master_synonyms (master_id, synonym_text, synonym_normalized, synonym_type)
-- SELECT master_id, 'BT lót', 'bt lót', 'abbreviation'
-- FROM master_work_items
-- WHERE description LIKE '%Bê tông lót%'
-- LIMIT 1;
