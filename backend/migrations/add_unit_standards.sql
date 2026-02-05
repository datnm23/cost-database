-- Migration: Add unit standards tables (MySQL)
-- Description: Create tables for unit standardization and SEC code default units

-- Table for unit standardization mappings
CREATE TABLE IF NOT EXISTS unit_standards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    raw_unit VARCHAR(50) NOT NULL UNIQUE,
    standard_unit VARCHAR(50) NOT NULL,
    unit_category VARCHAR(50),  -- volume, area, length, weight, count, other
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_unit_standards_raw_unit (raw_unit),
    INDEX ix_unit_standards_category (unit_category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table for SEC code to default unit mappings
CREATE TABLE IF NOT EXISTS sec_code_default_units (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sec_code VARCHAR(20) NOT NULL UNIQUE,
    default_unit VARCHAR(50) NOT NULL,
    category_name_vi VARCHAR(100),  -- Vietnamese name
    category_name_en VARCHAR(100),  -- English name
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_sec_code_default_units_sec_code (sec_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- SEED DATA: Unit Standardization Mappings
-- =====================================================

-- Volume units
INSERT IGNORE INTO unit_standards (raw_unit, standard_unit, unit_category, description) VALUES
('m3', 'm³', 'volume', 'Cubic meter'),
('m³', 'm³', 'volume', 'Cubic meter (already standard)'),
('mét khối', 'm³', 'volume', 'Vietnamese: Cubic meter'),
('m khối', 'm³', 'volume', 'Vietnamese: Cubic meter (short)'),
('khối', 'm³', 'volume', 'Vietnamese: Cubic'),
('cbm', 'm³', 'volume', 'Cubic meter (international)'),
('cubic meter', 'm³', 'volume', 'Cubic meter (English)'),
('cubic m', 'm³', 'volume', 'Cubic meter (abbreviated)');

-- Area units
INSERT IGNORE INTO unit_standards (raw_unit, standard_unit, unit_category, description) VALUES
('m2', 'm²', 'area', 'Square meter'),
('m²', 'm²', 'area', 'Square meter (already standard)'),
('mét vuông', 'm²', 'area', 'Vietnamese: Square meter'),
('m vuông', 'm²', 'area', 'Vietnamese: Square meter (short)'),
('sqm', 'm²', 'area', 'Square meter (international)'),
('sq.m', 'm²', 'area', 'Square meter (abbreviated)'),
('square meter', 'm²', 'area', 'Square meter (English)'),
('sq m', 'm²', 'area', 'Square meter (spaced)');

-- Length units
INSERT IGNORE INTO unit_standards (raw_unit, standard_unit, unit_category, description) VALUES
('m', 'm', 'length', 'Meter'),
('mét', 'm', 'length', 'Vietnamese: Meter'),
('met', 'm', 'length', 'Meter (no accent)'),
('meter', 'm', 'length', 'Meter (English)'),
('mm', 'mm', 'length', 'Millimeter'),
('milimet', 'mm', 'length', 'Vietnamese: Millimeter'),
('milimét', 'mm', 'length', 'Vietnamese: Millimeter (accent)'),
('cm', 'cm', 'length', 'Centimeter'),
('centimet', 'cm', 'length', 'Vietnamese: Centimeter'),
('centimét', 'cm', 'length', 'Vietnamese: Centimeter (accent)'),
('km', 'km', 'length', 'Kilometer');

-- Weight units
INSERT IGNORE INTO unit_standards (raw_unit, standard_unit, unit_category, description) VALUES
('kg', 'kg', 'weight', 'Kilogram'),
('kilo', 'kg', 'weight', 'Kilogram (short)'),
('kilogram', 'kg', 'weight', 'Kilogram (full)'),
('kilôgam', 'kg', 'weight', 'Vietnamese: Kilogram'),
('kí lô', 'kg', 'weight', 'Vietnamese: Kilo'),
('tấn', 'tấn', 'weight', 'Vietnamese: Tonne'),
('tan', 'tấn', 'weight', 'Tonne (no accent)'),
('ton', 'tấn', 'weight', 'Tonne (English)'),
('t', 'tấn', 'weight', 'Tonne (abbreviated)'),
('tonne', 'tấn', 'weight', 'Tonne (international)');

-- Count/Piece units
INSERT IGNORE INTO unit_standards (raw_unit, standard_unit, unit_category, description) VALUES
('cái', 'cái', 'count', 'Vietnamese: Piece'),
('chiếc', 'cái', 'count', 'Vietnamese: Piece (alternate)'),
('pc', 'cái', 'count', 'Piece (abbreviated)'),
('pcs', 'cái', 'count', 'Pieces'),
('ea', 'cái', 'count', 'Each'),
('each', 'cái', 'count', 'Each (full)'),
('piece', 'cái', 'count', 'Piece'),
('no', 'cái', 'count', 'Number'),
('nos', 'cái', 'count', 'Numbers'),
('bộ', 'bộ', 'count', 'Vietnamese: Set'),
('set', 'bộ', 'count', 'Set'),
('combo', 'bộ', 'count', 'Combo/Set'),
('điểm', 'điểm', 'count', 'Vietnamese: Point'),
('point', 'điểm', 'count', 'Point'),
('pt', 'điểm', 'count', 'Point (abbreviated)'),
('cây', 'cây', 'count', 'Vietnamese: Tree/Bar'),
('tree', 'cây', 'count', 'Tree');

-- Other units
INSERT IGNORE INTO unit_standards (raw_unit, standard_unit, unit_category, description) VALUES
('lô', 'lô', 'other', 'Vietnamese: Lot'),
('lot', 'lô', 'other', 'Lot'),
('ls', 'trọn gói', 'other', 'Lump sum'),
('lump sum', 'trọn gói', 'other', 'Lump sum (full)'),
('trọn gói', 'trọn gói', 'other', 'Vietnamese: Lump sum'),
('l.s', 'trọn gói', 'other', 'Lump sum (abbreviated)'),
('công', 'công', 'other', 'Vietnamese: Man-day'),
('man-day', 'công', 'other', 'Man-day'),
('ngày công', 'công', 'other', 'Vietnamese: Work day'),
('nc', 'công', 'other', 'Man-day (abbreviated)'),
('lít', 'lít', 'other', 'Vietnamese: Liter'),
('liter', 'lít', 'other', 'Liter'),
('l', 'lít', 'other', 'Liter (abbreviated)'),
('litre', 'lít', 'other', 'Litre (British)'),
('giờ', 'giờ', 'other', 'Vietnamese: Hour'),
('hour', 'giờ', 'other', 'Hour'),
('hr', 'giờ', 'other', 'Hour (abbreviated)'),
('h', 'giờ', 'other', 'Hour (short)'),
('ngày', 'ngày', 'other', 'Vietnamese: Day'),
('day', 'ngày', 'other', 'Day'),
('d', 'ngày', 'other', 'Day (abbreviated)'),
('tháng', 'tháng', 'other', 'Vietnamese: Month'),
('month', 'tháng', 'other', 'Month'),
('mo', 'tháng', 'other', 'Month (abbreviated)');

-- =====================================================
-- SEED DATA: SEC Code Default Units
-- =====================================================

-- Level 1 - Main categories
INSERT IGNORE INTO sec_code_default_units (sec_code, default_unit, category_name_vi, category_name_en, notes) VALUES
('SEC-00', 'trọn gói', 'Chi phí chung', 'Preliminaries', 'Lump sum for general costs'),
('SEC-01', 'm³', 'Phần ngầm', 'Substructure', 'Volume measurement default'),
('SEC-02', 'm³', 'Phần thân', 'Superstructure', 'Volume measurement default'),
('SEC-03', 'm²', 'Kiến trúc', 'Architecture', 'Area measurement default'),
('SEC-04', 'bộ', 'Cơ điện', 'MEP', 'Set/unit measurement default'),
('SEC-05', 'm²', 'Cảnh quan', 'Landscape', 'Area measurement default');

-- Level 2 - Substructure
INSERT IGNORE INTO sec_code_default_units (sec_code, default_unit, category_name_vi, category_name_en, notes) VALUES
('SEC-01-01', 'm³', 'Đào đất', 'Earthworks', 'Volume of excavation'),
('SEC-01-02', 'm', 'Cọc', 'Piling', 'Linear meter for piles'),
('SEC-01-03', 'm³', 'Móng', 'Foundation', 'Volume of concrete');

-- Level 2 - Superstructure
INSERT IGNORE INTO sec_code_default_units (sec_code, default_unit, category_name_vi, category_name_en, notes) VALUES
('SEC-02-01', 'm³', 'Bê tông', 'Concrete', 'Volume of concrete'),
('SEC-02-02', 'm³', 'Sàn', 'Floor Slab', 'Volume of concrete'),
('SEC-02-03', 'm³', 'Dầm', 'Beam', 'Volume of concrete'),
('SEC-02-04', 'm³', 'Cột', 'Column', 'Volume of concrete'),
('SEC-02-05', 'm³', 'Tường BTCT', 'RC Wall', 'Volume of concrete'),
('SEC-02-06', 'kg', 'Cốt thép', 'Rebar', 'Weight of reinforcement');

-- Level 2 - Architecture
INSERT IGNORE INTO sec_code_default_units (sec_code, default_unit, category_name_vi, category_name_en, notes) VALUES
('SEC-03-01', 'm³', 'Xây gạch', 'Masonry', 'Volume per TCVN'),
('SEC-03-02', 'm²', 'Trát', 'Plastering', 'Surface area'),
('SEC-03-03', 'm²', 'Sơn', 'Painting', 'Surface area'),
('SEC-03-04', 'm²', 'Lát gạch', 'Tiling', 'Surface area'),
('SEC-03-05', 'm²', 'Trần', 'Ceiling', 'Surface area'),
('SEC-03-06', 'bộ', 'Cửa', 'Door & Window', 'Per set/unit');

-- Level 2 - MEP
INSERT IGNORE INTO sec_code_default_units (sec_code, default_unit, category_name_vi, category_name_en, notes) VALUES
('SEC-04-01', 'điểm', 'Điện', 'Electrical', 'Points or linear'),
('SEC-04-02', 'điểm', 'Nước', 'Plumbing', 'Points or linear'),
('SEC-04-03', 'bộ', 'Điều hòa', 'HVAC', 'Per unit/set'),
('SEC-04-04', 'bộ', 'PCCC', 'Fire Protection', 'Per unit/set');

-- Level 2 - Landscape
INSERT IGNORE INTO sec_code_default_units (sec_code, default_unit, category_name_vi, category_name_en, notes) VALUES
('SEC-05-01', 'm²', 'Đường', 'Road', 'Surface area'),
('SEC-05-02', 'm²', 'Vỉa hè', 'Pavement', 'Surface area'),
('SEC-05-03', 'cây', 'Cây xanh', 'Greenery', 'Per tree count');
