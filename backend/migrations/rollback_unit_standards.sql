-- Rollback: Remove unit standards tables (MySQL)
-- Description: Drop tables for unit standardization and SEC code default units

-- Drop tables
DROP TABLE IF EXISTS unit_standards;
DROP TABLE IF EXISTS sec_code_default_units;
