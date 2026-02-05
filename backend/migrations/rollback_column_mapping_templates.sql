-- Rollback: Remove column_mapping_templates and template_usage_logs tables
-- Created: 2026-02-04

DROP TABLE IF EXISTS template_usage_logs;
DROP TABLE IF EXISTS column_mapping_templates;
