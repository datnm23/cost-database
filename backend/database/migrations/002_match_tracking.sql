-- Migration: 002_match_tracking
-- Description: Add match tracking fields to line_items table
-- Date: 2026-02-03

-- Add match tracking columns to line_items
ALTER TABLE line_items
    ADD COLUMN matched_master_id INT NULL COMMENT 'Reference to matched master work item',
    ADD COLUMN match_similarity DECIMAL(5, 2) NULL COMMENT 'Similarity score (0-100)',
    ADD COLUMN match_type ENUM('exact', 'fuzzy', 'none') DEFAULT 'none' COMMENT 'Type of match with master',
    ADD COLUMN original_sheet_name VARCHAR(100) NULL COMMENT 'Original Excel sheet name';

-- Add foreign key constraint
ALTER TABLE line_items
    ADD CONSTRAINT fk_line_item_master
    FOREIGN KEY (matched_master_id) REFERENCES master_work_items(master_id)
    ON DELETE SET NULL;

-- Add indexes for filtering
CREATE INDEX idx_line_items_match_type ON line_items(file_id, match_type);
CREATE INDEX idx_line_items_confidence ON line_items(file_id, confidence_score);
CREATE INDEX idx_line_items_matched_master ON line_items(matched_master_id);
