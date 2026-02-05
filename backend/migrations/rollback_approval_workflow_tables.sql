-- Rollback: Remove approval workflow tables
-- Created: 2026-02-03

-- Drop tables in reverse order of creation (to handle foreign keys)
DROP TABLE IF EXISTS quarantine_logs;
DROP TABLE IF EXISTS pending_master_items;

SELECT 'Rollback completed successfully' AS status;
