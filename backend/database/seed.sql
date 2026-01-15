-- Sample data for BOQ System
-- Run this after schema.sql for development/testing

-- Additional users
INSERT IGNORE INTO users (username, email, full_name, hashed_password, role) VALUES
('editor', 'editor@boqsystem.com', 'BOQ Editor', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeJhiPm.4VW6', 'editor'),
('viewer', 'viewer@boqsystem.com', 'BOQ Viewer', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeJhiPm.4VW6', 'viewer');

-- Sample projects
INSERT IGNORE INTO projects (project_code, project_name, project_type, location, client_name, contract_value, start_date, status) VALUES
('PRJ-2024-001', 'Vinhomes Grand Park Tower A', 'residential', 'Thu Duc City, HCMC', 'Vingroup', 1500000000, '2024-01-15', 'active'),
('PRJ-2024-002', 'Landmark 81 Office Tower', 'commercial', 'Binh Thanh District, HCMC', 'Vinhomes', 2000000000, '2024-02-01', 'active'),
('PRJ-2024-003', 'Long Thanh Airport Terminal', 'infrastructure', 'Dong Nai Province', 'ACV', 5000000000, '2024-03-01', 'active');

-- Additional SEC codes (Level 2 - SEC-02 children)
INSERT IGNORE INTO sec_codes (sec_code, sec_name_vi, sec_name_en, parent_code, level, keywords, is_active) VALUES
('SEC-02-01', 'Khung BTCT', 'Concrete Frame', 'SEC-02', 2, '["khung", "cột", "dầm", "frame", "column", "beam", "concrete"]', TRUE),
('SEC-02-02', 'Sàn', 'Floor', 'SEC-02', 2, '["sàn", "floor", "slab"]', TRUE),
('SEC-02-03', 'Mái', 'Roof', 'SEC-02', 2, '["mái", "roof"]', TRUE);

-- SEC codes Level 2 (SEC-03 children)
INSERT IGNORE INTO sec_codes (sec_code, sec_name_vi, sec_name_en, parent_code, level, keywords, is_active) VALUES
('SEC-03-01', 'Tường xây', 'Masonry', 'SEC-03', 2, '["tường", "xây", "masonry", "wall", "brick"]', TRUE),
('SEC-03-02', 'Trát tường', 'Plastering', 'SEC-03', 2, '["trát", "plastering", "render"]', TRUE),
('SEC-03-03', 'Sơn', 'Painting', 'SEC-03', 2, '["sơn", "paint", "painting"]', TRUE),
('SEC-03-04', 'Ốp lát', 'Tiling', 'SEC-03', 2, '["ốp", "lát", "gạch", "tile", "tiling"]', TRUE),
('SEC-03-05', 'Trần', 'Ceiling', 'SEC-03', 2, '["trần", "ceiling"]', TRUE);

-- SEC codes Level 2 (SEC-04 children)
INSERT IGNORE INTO sec_codes (sec_code, sec_name_vi, sec_name_en, parent_code, level, keywords, is_active) VALUES
('SEC-04-01', 'Điện', 'Electrical', 'SEC-04', 2, '["điện", "electrical", "power"]', TRUE),
('SEC-04-02', 'Nước', 'Plumbing', 'SEC-04', 2, '["nước", "plumbing", "water", "drainage"]', TRUE),
('SEC-04-03', 'Điều hòa', 'HVAC', 'SEC-04', 2, '["điều hòa", "HVAC", "air conditioning"]', TRUE),
('SEC-04-04', 'PCCC', 'Fire Protection', 'SEC-04', 2, '["PCCC", "chữa cháy", "fire protection"]', TRUE);

-- SEC codes Level 3 (detailed items)
INSERT IGNORE INTO sec_codes (sec_code, sec_name_vi, sec_name_en, parent_code, level, keywords, is_active) VALUES
('SEC-01-01-01', 'Đào đất thủ công', 'Manual Excavation', 'SEC-01-01', 3, '["đào", "thủ công", "manual", "excavation"]', TRUE),
('SEC-01-01-02', 'Đào đất máy', 'Machine Excavation', 'SEC-01-01', 3, '["đào", "máy", "machine", "excavator"]', TRUE),
('SEC-01-02-01', 'Cọc khoan nhồi D600', 'Bored Pile D600', 'SEC-01-02', 3, '["cọc khoan", "D600", "bored pile"]', TRUE),
('SEC-01-02-02', 'Cọc ép D300', 'Driven Pile D300', 'SEC-01-02', 3, '["cọc ép", "D300", "driven pile"]', TRUE);

-- Note: More SEC codes can be added as needed
