-- Migration: Add separated specs columns to master_work_items
-- Date: 2026-02-03
-- Description: Adds structured spec fields for fast filtering and matching key lookup

-- Add spec columns
ALTER TABLE master_work_items
    ADD COLUMN spec_category VARCHAR(100) NULL COMMENT 'Material category (Be tong, Thep, Ong)',
    ADD COLUMN spec_material VARCHAR(100) NULL COMMENT 'Material type (HDPE, PPR, Cu/XLPE)',
    ADD COLUMN spec_grade VARCHAR(50) NULL COMMENT 'Grade (M200, CB400, PN16)',
    ADD COLUMN spec_dimension VARCHAR(200) NULL COMMENT 'Dimensions (D110, 4x16mm2, 600x600)';

-- Add matching key for O(1) lookup
ALTER TABLE master_work_items
    ADD COLUMN matching_key VARCHAR(255) NULL COMMENT 'Normalized key for O(1) lookup';

-- Add embedding columns for pre-computed vectors
ALTER TABLE master_work_items
    ADD COLUMN embedding_vector LONGBLOB NULL COMMENT 'Pre-computed SBERT embedding (768 dims)',
    ADD COLUMN embedding_version VARCHAR(50) NULL COMMENT 'Embedding model version';

-- Create indexes for fast filtering
CREATE INDEX idx_master_matching_key ON master_work_items (matching_key);
CREATE INDEX idx_master_spec_category ON master_work_items (spec_category);
CREATE INDEX idx_master_spec_material ON master_work_items (spec_material);
CREATE INDEX idx_master_spec_grade ON master_work_items (spec_grade);

-- Show result
SELECT 'Migration completed successfully' AS status;
