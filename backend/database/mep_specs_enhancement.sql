-- ====================================
-- MEP SPECS ENHANCEMENT: Material Spec JSON Schema
-- Mở rộng lưu trữ chi tiết MEP (PPR-D63-PN16)
-- ====================================

-- 1. Update master_work_items để hỗ trợ material_spec JSON
ALTER TABLE master_work_items 
MODIFY COLUMN material_spec JSON COMMENT 'Chi tiết specs MEP: {"material": "PPR", "diameter": "D63", "pressure": "PN16"}';

-- 2. Thêm index cho JSON search (MySQL 8.0+)
ALTER TABLE master_work_items 
ADD INDEX idx_material_spec_type ((JSON_EXTRACT(material_spec, '$.material')));

-- 3. Create MEP Material Specification Table (Reference data)
CREATE TABLE IF NOT EXISTS mep_material_specs (
    spec_id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Category
    category ENUM('water', 'electrical', 'hvac', 'fire', 'telecom') NOT NULL,
    sub_category VARCHAR(100) COMMENT 'pipe, cable, duct, conduit, etc.',
    
    -- Material identification
    material_code VARCHAR(50) UNIQUE NOT NULL COMMENT 'PPR, UPVC, Cu/XLPE/PVC',
    material_name_vn VARCHAR(255) NOT NULL,
    material_name_en VARCHAR(255),
    
    -- Specifications (JSON for flexibility)
    specs_template JSON COMMENT '{
        "diameter_range": ["D20", "D25", "D32", "D50", "D63"],
        "pressure_ratings": ["PN10", "PN16", "PN20"],
        "conductor_types": ["Cu", "Al"],
        "insulation": ["PVC", "XLPE"],
        "thickness_range": [0.5, 0.75, 1.0, 1.5]
    }',
    
    -- Standards
    standard_code VARCHAR(50) COMMENT 'TCVN 6151, EN 12201, IEC 60502',
    standard_name TEXT,
    
    -- Usage context
    typical_applications JSON COMMENT '["Cấp nước sinh hoạt", "Thoát nước", "Cáp điện lực"]',
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_category (category),
    INDEX idx_material_code (material_code),
    INDEX idx_sub_category (sub_category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Thư viện specifications vật liệu MEP';


-- ====================================
-- SAMPLE DATA: MEP Material Specs
-- ====================================

-- Water pipes
INSERT INTO mep_material_specs (
    category, sub_category, material_code, material_name_vn, material_name_en,
    specs_template, standard_code, typical_applications
) VALUES
('water', 'pipe', 'PPR', 
 'Ống nhựa Polypropylene nhiệt dẻo', 
 'Polypropylene Random Copolymer Pipe',
 JSON_OBJECT(
     'diameter_range', JSON_ARRAY('D20', 'D25', 'D32', 'D40', 'D50', 'D63', 'D75', 'D90', 'D110'),
     'pressure_ratings', JSON_ARRAY('PN10', 'PN16', 'PN20', 'PN25'),
     'thickness_series', JSON_ARRAY('S5', 'S4', 'S3.2', 'S2.5'),
     'temp_range', '-10°C to 95°C'
 ),
 'TCVN 6151:2009',
 JSON_ARRAY('Cấp nước nóng/lạnh', 'Hệ thống sưởi', 'Nước sinh hoạt')),

('water', 'pipe', 'UPVC', 
 'Ống nhựa PVC không hóa dẻo', 
 'Unplasticized Polyvinyl Chloride Pipe',
 JSON_OBJECT(
     'diameter_range', JSON_ARRAY('D50', 'D75', 'D90', 'D110', 'D140', 'D160', 'D200'),
     'pressure_ratings', JSON_ARRAY('Class 1', 'Class 2', 'Class 3'),
     'thickness_class', JSON_ARRAY('Light', 'Medium', 'Heavy'),
     'temp_range', '0°C to 60°C'
 ),
 'TCVN 6224:2003',
 JSON_ARRAY('Thoát nước', 'Nước thải', 'Cấp nước lạnh')),

('water', 'pipe', 'HDPE', 
 'Ống nhựa Polyethylene tỷ trọng cao', 
 'High Density Polyethylene Pipe',
 JSON_OBJECT(
     'diameter_range', JSON_ARRAY('D63', 'D90', 'D110', 'D160', 'D200', 'D250', 'D315'),
     'pressure_ratings', JSON_ARRAY('PN6', 'PN8', 'PN10', 'PN12.5', 'PN16'),
     'sdr_series', JSON_ARRAY('SDR11', 'SDR13.6', 'SDR17', 'SDR21', 'SDR26'),
     'burial_depth', 'up to 10m'
 ),
 'TCVN 7305:2016',
 JSON_ARRAY('Cấp nước ngầm', 'Hệ thống tưới', 'Công trình thủy lợi'));

-- Electrical cables
INSERT INTO mep_material_specs (
    category, sub_category, material_code, material_name_vn, material_name_en,
    specs_template, standard_code, typical_applications
) VALUES
('electrical', 'cable', 'Cu/XLPE/PVC', 
 'Cáp đồng cách điện XLPE vỏ PVC', 
 'Copper XLPE Insulated PVC Sheathed Cable',
 JSON_OBJECT(
     'conductor', 'Cu (Copper)',
     'insulation', 'XLPE (Cross-linked Polyethylene)',
     'sheath', 'PVC',
     'voltage_rating', JSON_ARRAY('0.6/1kV', '6/10kV', '12/20kV'),
     'core_config', JSON_ARRAY('1x', '2x', '3x', '4x', '3x+1x'),
     'size_range', JSON_ARRAY('1.5', '2.5', '4', '6', '10', '16', '25', '35', '50', '70', '95', '120', '150', '185', '240')
 ),
 'TCVN 5935:2009',
 JSON_ARRAY('Cáp điện lực', 'Đường dây chính', 'Cấp điện hạ thế')),

('electrical', 'cable', 'Cu/PVC', 
 'Dây đồng cách điện PVC', 
 'Copper PVC Insulated Wire',
 JSON_OBJECT(
     'conductor', 'Cu (Copper)',
     'insulation', 'PVC',
     'voltage_rating', '450/750V',
     'core_types', JSON_ARRAY('Single core', 'Multi core'),
     'size_range', JSON_ARRAY('0.5', '0.75', '1', '1.5', '2.5', '4', '6', '10', '16'),
     'color_code', JSON_ARRAY('Blue-N', 'Brown-L', 'Yellow/Green-PE')
 ),
 'TCVN 2682:2009',
 JSON_ARRAY('Dây điện chiếu sáng', 'Mạch điều khiển', 'Dây nối thiết bị'));

-- HVAC ducts
INSERT INTO mep_material_specs (
    category, sub_category, material_code, material_name_vn, material_name_en,
    specs_template, standard_code, typical_applications
) VALUES
('hvac', 'duct', 'GI_DUCT', 
 'Ống gió tôn tráng kẽm', 
 'Galvanized Iron Duct',
 JSON_OBJECT(
     'material', 'Galvanized Iron Sheet',
     'thickness_range', JSON_ARRAY('0.5mm', '0.6mm', '0.75mm', '0.8mm', '1.0mm', '1.2mm'),
     'dimension_types', JSON_ARRAY('Rectangular', 'Circular'),
     'pressure_class', JSON_ARRAY('Low', 'Medium', 'High'),
     'standard_sizes', JSON_ARRAY('200x100', '300x150', '400x200', '600x300', '800x400', '1000x500', '1200x600')
 ),
 'SMACNA Standard',
 JSON_ARRAY('Ống gió cấp', 'Ống gió hồi', 'Ống gió tươi')),

('hvac', 'pipe', 'CU_PIPE', 
 'Ống đồng điều hòa', 
 'Copper Refrigerant Pipe',
 JSON_OBJECT(
     'material', 'Copper (C12200)',
     'type', JSON_ARRAY('Type L', 'Type K', 'ACR'),
     'size_range', JSON_ARRAY('6.35', '9.52', '12.7', '15.88', '19.05', '22.22', '28.58', '34.92'),
     'insulation_types', JSON_ARRAY('Armaflex', 'Rubber foam', 'PE foam'),
     'thickness_insulation', JSON_ARRAY('9mm', '13mm', '19mm', '25mm')
 ),
 'ASTM B88',
 JSON_ARRAY('Đường ống gas', 'Đường ống lỏng', 'Hệ thống VRV/VRF'));

-- Fire protection
INSERT INTO mep_material_specs (
    category, sub_category, material_code, material_name_vn, material_name_en,
    specs_template, standard_code, typical_applications
) VALUES
('fire', 'pipe', 'SCH40', 
 'Ống thép đen hàn Schedule 40', 
 'Black Steel Welded Pipe Schedule 40',
 JSON_OBJECT(
     'material', 'Carbon Steel',
     'schedule', JSON_ARRAY('Sch10', 'Sch40', 'Sch80'),
     'diameter_range', JSON_ARRAY('DN20', 'DN25', 'DN32', 'DN50', 'DN65', 'DN80', 'DN100', 'DN150'),
     'pressure_rating', 'PN16',
     'coating', JSON_ARRAY('Galvanized', 'Painted', 'Bare')
 ),
 'TCVN 1651:2008',
 JSON_ARRAY('Hệ thống PCCC', 'Sprinkler', 'Hydrant'));


-- ====================================
-- HELPER FUNCTIONS: JSON Utilities
-- ====================================

-- Function to build material_spec JSON
DELIMITER $$

CREATE FUNCTION build_material_spec_json(
    p_material VARCHAR(50),
    p_diameter VARCHAR(20),
    p_pressure VARCHAR(20),
    p_conductor VARCHAR(50),
    p_size VARCHAR(20),
    p_dimension VARCHAR(50),
    p_thickness VARCHAR(20)
) RETURNS JSON
DETERMINISTIC
BEGIN
    DECLARE result JSON;
    
    SET result = JSON_OBJECT();
    
    IF p_material IS NOT NULL THEN
        SET result = JSON_SET(result, '$.material', p_material);
    END IF;
    
    IF p_diameter IS NOT NULL THEN
        SET result = JSON_SET(result, '$.diameter', p_diameter);
    END IF;
    
    IF p_pressure IS NOT NULL THEN
        SET result = JSON_SET(result, '$.pressure', p_pressure);
    END IF;
    
    IF p_conductor IS NOT NULL THEN
        SET result = JSON_SET(result, '$.conductor', p_conductor);
    END IF;
    
    IF p_size IS NOT NULL THEN
        SET result = JSON_SET(result, '$.size', p_size);
    END IF;
    
    IF p_dimension IS NOT NULL THEN
        SET result = JSON_SET(result, '$.dimension', p_dimension);
    END IF;
    
    IF p_thickness IS NOT NULL THEN
        SET result = JSON_SET(result, '$.thickness', p_thickness);
    END IF;
    
    RETURN result;
END$$

DELIMITER ;


-- ====================================
-- EXAMPLE USAGE: Update master_work_items
-- ====================================

-- Example 1: Water pipe
UPDATE master_work_items 
SET material_spec = build_material_spec_json(
    'PPR',      -- material
    'D63',      -- diameter
    'PN16',     -- pressure
    NULL,       -- conductor
    NULL,       -- size
    NULL,       -- dimension
    NULL        -- thickness
)
WHERE description LIKE '%ống PPR D63 PN16%';

-- Example 2: Electrical cable
UPDATE master_work_items 
SET material_spec = build_material_spec_json(
    NULL,               -- material
    NULL,               -- diameter
    NULL,               -- pressure
    'Cu/XLPE/PVC',     -- conductor
    '4x50',            -- size
    NULL,              -- dimension
    NULL               -- thickness
)
WHERE description LIKE '%cáp%Cu/XLPE/PVC%4x50%';

-- Example 3: HVAC duct
UPDATE master_work_items 
SET material_spec = build_material_spec_json(
    'Tôn tráng kẽm',  -- material
    NULL,              -- diameter
    NULL,              -- pressure
    NULL,              -- conductor
    NULL,              -- size
    '1200x400',        -- dimension
    '0.75mm'           -- thickness
)
WHERE description LIKE '%ống gió%1200x400%';


-- ====================================
-- VIEWS: Quick access to MEP specs
-- ====================================

-- View: Water pipes with full specs
CREATE OR REPLACE VIEW v_water_pipes_catalog AS
SELECT 
    m.material_code,
    m.material_name_vn,
    JSON_UNQUOTE(JSON_EXTRACT(m.specs_template, '$.diameter_range')) as diameters,
    JSON_UNQUOTE(JSON_EXTRACT(m.specs_template, '$.pressure_ratings')) as pressures,
    m.standard_code,
    m.typical_applications
FROM mep_material_specs m
WHERE m.category = 'water' AND m.sub_category = 'pipe';

-- View: Electrical cables catalog
CREATE OR REPLACE VIEW v_electrical_cables_catalog AS
SELECT 
    m.material_code,
    m.material_name_vn,
    JSON_UNQUOTE(JSON_EXTRACT(m.specs_template, '$.voltage_rating')) as voltage,
    JSON_UNQUOTE(JSON_EXTRACT(m.specs_template, '$.size_range')) as sizes,
    m.standard_code,
    m.typical_applications
FROM mep_material_specs m
WHERE m.category = 'electrical' AND m.sub_category = 'cable';

-- View: Work items with MEP specs
CREATE OR REPLACE VIEW v_work_items_with_mep_specs AS
SELECT 
    w.work_code,
    w.description,
    w.name_natural,
    w.sec_code,
    JSON_UNQUOTE(JSON_EXTRACT(w.material_spec, '$.material')) as material,
    JSON_UNQUOTE(JSON_EXTRACT(w.material_spec, '$.diameter')) as diameter,
    JSON_UNQUOTE(JSON_EXTRACT(w.material_spec, '$.pressure')) as pressure,
    JSON_UNQUOTE(JSON_EXTRACT(w.material_spec, '$.conductor')) as conductor,
    JSON_UNQUOTE(JSON_EXTRACT(w.material_spec, '$.size')) as cable_size,
    JSON_UNQUOTE(JSON_EXTRACT(w.material_spec, '$.dimension')) as dimension,
    JSON_UNQUOTE(JSON_EXTRACT(w.material_spec, '$.thickness')) as thickness
FROM master_work_items w
WHERE w.material_spec IS NOT NULL;


-- ====================================
-- VALIDATION QUERIES
-- ====================================

-- Check if material spec is valid for a given category
SELECT 
    w.work_code,
    w.description,
    w.material_spec,
    CASE 
        WHEN m.spec_id IS NOT NULL THEN 'Valid'
        ELSE 'Invalid - Material not in catalog'
    END as validation_status
FROM master_work_items w
LEFT JOIN mep_material_specs m 
    ON JSON_UNQUOTE(JSON_EXTRACT(w.material_spec, '$.material')) = m.material_code
WHERE w.material_spec IS NOT NULL;
