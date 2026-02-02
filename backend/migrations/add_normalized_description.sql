-- Migration: Add normalized_description fields to line_items table
-- Date: 2024
-- Description: Add columns for naming normalization feature

-- Add new columns for normalized description
ALTER TABLE line_items ADD COLUMN normalized_description TEXT NULL;
ALTER TABLE line_items ADD COLUMN normalization_confidence DECIMAL(5,2) NULL;
ALTER TABLE line_items ADD COLUMN work_category VARCHAR(50) NULL;

-- Create indexes for better query performance
CREATE INDEX idx_line_items_normalized_desc ON line_items(normalized_description(255));
CREATE INDEX idx_line_items_work_category ON line_items(work_category);

-- Verify the changes
-- DESCRIBE line_items;
