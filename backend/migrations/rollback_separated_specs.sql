-- Rollback Migration: Remove separated specs columns from master_work_items
-- Date: 2026-02-03
-- Description: Reverts the add_separated_specs migration

-- Drop indexes first
DROP INDEX idx_master_spec_grade ON master_work_items;
DROP INDEX idx_master_spec_material ON master_work_items;
DROP INDEX idx_master_spec_category ON master_work_items;
DROP INDEX idx_master_matching_key ON master_work_items;

-- Remove columns
ALTER TABLE master_work_items
    DROP COLUMN embedding_version,
    DROP COLUMN embedding_vector,
    DROP COLUMN matching_key,
    DROP COLUMN spec_dimension,
    DROP COLUMN spec_grade,
    DROP COLUMN spec_material,
    DROP COLUMN spec_category;

-- Show result
SELECT 'Rollback completed successfully' AS status;
