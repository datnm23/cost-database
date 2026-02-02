-- ====================================
-- SCHEMA EXTENSION: Legal Codes & ISO Classification
-- Mở rộng hệ thống để hỗ trợ Thông tư 12/2021 và ISO 12006-2
-- ====================================

-- TABLE 1: Legal Work Codes (Định mức Thông tư 12/2021)
-- ====================================
CREATE TABLE IF NOT EXISTS legal_work_codes (
    legal_code VARCHAR(30) PRIMARY KEY COMMENT 'Mã định mức: AA.1234a, BA.5678+, etc.',
    legal_code_prefix VARCHAR(5) NOT NULL COMMENT 'Tiền tố: AA, AB, BA, CA, etc.',
    legal_code_number VARCHAR(10) NOT NULL COMMENT 'Phần số: 1234, 5678',
    legal_code_suffix VARCHAR(5) COMMENT 'Hậu tố: a, b, +, -, NULL',
    
    -- Description
    name_official_vn TEXT NOT NULL COMMENT 'Tên chính thức theo định mức',
    name_natural_vn TEXT COMMENT 'Tên tự nhiên đề xuất theo chuẩn mới',
    name_en VARCHAR(500) COMMENT 'Tên tiếng Anh',
    
    -- Classification
    circular_number VARCHAR(50) DEFAULT '12/2021/TT-BXD' COMMENT 'Thông tư ban hành',
    appendix_code VARCHAR(20) COMMENT 'Phụ lục: I, II, III, IV, V',
    category_level_1 VARCHAR(100) COMMENT 'Nhóm cấp 1: Khảo sát, Thiết kế, Xây dựng',
    category_level_2 VARCHAR(100) COMMENT 'Nhóm cấp 2: Đất, Bê tông, Xây, Hoàn thiện',
    category_level_3 VARCHAR(100) COMMENT 'Nhóm cấp 3: Chi tiết hơn',
    
    -- Technical specs
    unit_standard VARCHAR(20) NOT NULL COMMENT 'Đơn vị: m, m2, m3, kg, etc.',
    material_spec JSON COMMENT 'Quy cách vật liệu: {"grade": "M200", "type": "commercial"}',
    technical_params JSON COMMENT 'Thông số kỹ thuật: {"thickness": "100mm", "depth": ">1.25m"}',
    
    -- Reference pricing (từ định mức)
    labor_cost DECIMAL(15,2) COMMENT 'Chi phí nhân công',
    machine_cost DECIMAL(15,2) COMMENT 'Chi phí máy',
    material_cost DECIMAL(15,2) COMMENT 'Chi phí vật liệu',
    total_unit_cost DECIMAL(15,2) COMMENT 'Đơn giá tổng',
    price_year INT COMMENT 'Năm giá',
    
    -- Metadata
    effective_from DATE COMMENT 'Ngày hiệu lực',
    effective_to DATE COMMENT 'Ngày hết hiệu lực',
    superseded_by VARCHAR(30) COMMENT 'Thay thế bởi mã',
    notes TEXT COMMENT 'Ghi chú đặc biệt',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_prefix (legal_code_prefix),
    INDEX idx_appendix (appendix_code),
    INDEX idx_cat1 (category_level_1),
    INDEX idx_cat2 (category_level_2),
    INDEX idx_unit (unit_standard),
    INDEX idx_active (is_active),
    FULLTEXT idx_name_vn (name_official_vn, name_natural_vn)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Mã định mức pháp lý theo Thông tư 12/2021/TT-BXD';


-- TABLE 2: ISO Classification Codes (ISO 12006-2)
-- ====================================
CREATE TABLE IF NOT EXISTS iso_classification_codes (
    iso_code VARCHAR(50) PRIMARY KEY COMMENT 'Mã ISO: Pr_21_31_13',
    iso_version VARCHAR(20) DEFAULT 'ISO 12006-2:2015',
    
    -- Hierarchy (Entity-System-Element-Product)
    entity_code VARCHAR(10) COMMENT 'Entity type: Ss, Pr, Ac, etc.',
    entity_name_vn VARCHAR(100) COMMENT 'Không gian, Công việc, Hoạt động',
    entity_name_en VARCHAR(100) COMMENT 'Space, Process, Activity',
    
    system_code VARCHAR(10) COMMENT 'System: 21 (tường), 22 (sàn), etc.',
    system_name_vn VARCHAR(100) COMMENT 'Tên hệ thống',
    system_name_en VARCHAR(100),
    
    element_code VARCHAR(10) COMMENT 'Element: 31 (bê tông)',
    element_name_vn VARCHAR(100),
    element_name_en VARCHAR(100),
    
    product_code VARCHAR(10) COMMENT 'Product: 13 (M200)',
    product_name_vn VARCHAR(100),
    product_name_en VARCHAR(100),
    
    -- Full description
    full_description_vn TEXT,
    full_description_en TEXT,
    
    -- Mapping reference
    tcvn_code VARCHAR(50) COMMENT 'Mã TCVN tương ứng',
    uniclass_code VARCHAR(50) COMMENT 'Mã Uniclass tương ứng',
    omniclass_code VARCHAR(50) COMMENT 'Mã OmniClass tương ứng',
    
    -- Metadata
    level TINYINT COMMENT 'Độ sâu phân cấp: 1-4',
    parent_code VARCHAR(50) COMMENT 'Mã cha',
    has_children BOOLEAN DEFAULT FALSE,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_entity (entity_code),
    INDEX idx_system (system_code),
    INDEX idx_level (level),
    INDEX idx_parent (parent_code),
    FULLTEXT idx_description (full_description_vn, full_description_en)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Mã phân loại ISO 12006-2 cho BIM';


-- TABLE 3: Work Code Mapping (Bảng ánh xạ 3 chiều)
-- ====================================
CREATE TABLE IF NOT EXISTS work_code_mapping (
    mapping_id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Three code systems
    work_code VARCHAR(50) NOT NULL COMMENT 'S01-EARTH-EXCAV-0001 (internal)',
    legal_code VARCHAR(30) COMMENT 'AA.1234a (Thông tư 12/2021)',
    iso_code VARCHAR(50) COMMENT 'Pr_21_31_13 (ISO 12006-2)',
    sec_code VARCHAR(20) COMMENT 'SEC-01-01 (internal)',
    
    -- Mapping metadata
    mapping_type ENUM('auto', 'manual', 'verified') DEFAULT 'auto',
    confidence_score DECIMAL(5,2) COMMENT 'Độ tin cậy ánh xạ 0-100',
    mapping_rules JSON COMMENT 'Quy tắc ánh xạ',
    
    -- Context
    description TEXT COMMENT 'Mô tả công tác',
    unit VARCHAR(20) COMMENT 'Đơn vị',
    material_grade VARCHAR(20) COMMENT 'Mác vật liệu',
    
    -- Validation
    is_primary BOOLEAN DEFAULT TRUE COMMENT 'Ánh xạ chính (1-to-1) hay phụ (1-to-many)',
    verified_by INT COMMENT 'User xác nhận',
    verified_at TIMESTAMP NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (work_code) REFERENCES master_work_items(work_code) ON DELETE CASCADE,
    FOREIGN KEY (legal_code) REFERENCES legal_work_codes(legal_code) ON DELETE SET NULL,
    FOREIGN KEY (iso_code) REFERENCES iso_classification_codes(iso_code) ON DELETE SET NULL,
    FOREIGN KEY (sec_code) REFERENCES sec_codes(sec_code) ON DELETE SET NULL,
    
    -- Indexes
    UNIQUE KEY uk_work_legal (work_code, legal_code),
    INDEX idx_work (work_code),
    INDEX idx_legal (legal_code),
    INDEX idx_iso (iso_code),
    INDEX idx_sec (sec_code),
    INDEX idx_type (mapping_type),
    INDEX idx_confidence (confidence_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Ánh xạ 3 lớp: Internal Work Code ↔ Legal Code ↔ ISO Code';


-- TABLE 4: BIM Object Mapping (Revit/BIM → Work Codes)
-- ====================================
CREATE TABLE IF NOT EXISTS bim_object_mapping (
    bim_mapping_id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- BIM Object identification
    revit_category VARCHAR(100) COMMENT 'Walls, Floors, Columns, etc.',
    revit_family VARCHAR(200) COMMENT 'Tên Family',
    revit_type VARCHAR(200) COMMENT 'Tên Type',
    
    -- BIM Parameters (JSON)
    bim_parameters JSON COMMENT 'Key parameters: {"Material": "Concrete", "Width": "200mm"}',
    
    -- Mapped codes
    work_code VARCHAR(50) COMMENT 'Internal work code',
    legal_code VARCHAR(30) COMMENT 'Legal code',
    iso_code VARCHAR(50) COMMENT 'ISO code',
    
    -- Auto-extraction rules
    extraction_rules JSON COMMENT 'Quy tắc trích xuất từ Revit',
    parameter_mapping JSON COMMENT 'Ánh xạ parameters',
    
    -- Usage statistics
    usage_count INT DEFAULT 0 COMMENT 'Số lần sử dụng',
    last_used_at TIMESTAMP NULL,
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (work_code) REFERENCES master_work_items(work_code) ON DELETE SET NULL,
    
    -- Indexes
    INDEX idx_category (revit_category),
    INDEX idx_family (revit_family),
    INDEX idx_work (work_code),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Ánh xạ BIM Objects (Revit) → Work Codes';


-- TABLE 5: Material Library (Thư viện vật liệu chuẩn)
-- ====================================
CREATE TABLE IF NOT EXISTS material_library (
    material_id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Identification
    material_code VARCHAR(50) UNIQUE NOT NULL COMMENT 'VL.BT.M200.01',
    material_name_vn VARCHAR(255) NOT NULL COMMENT 'Bê tông thương phẩm mác 200',
    material_name_en VARCHAR(255),
    
    -- Classification
    category VARCHAR(100) COMMENT 'Bê tông, Thép, Gạch, Sơn, etc.',
    sub_category VARCHAR(100),
    
    -- Specifications
    grade VARCHAR(50) COMMENT 'M200, M250, CB300, CT250, etc.',
    standard VARCHAR(100) COMMENT 'TCVN, ASTM, EN, etc.',
    specification TEXT COMMENT 'Đặc tính kỹ thuật chi tiết',
    
    -- Unit & Pricing
    unit_standard VARCHAR(20) NOT NULL,
    unit_variants JSON COMMENT '["m3", "mét khối", "cubic meter"]',
    ref_unit_price DECIMAL(15,2),
    price_source VARCHAR(200),
    price_updated_at DATE,
    
    -- Mapping
    legal_material_code VARCHAR(50) COMMENT 'Mã vật liệu trong định mức',
    iso_material_code VARCHAR(50),
    
    -- Metadata
    supplier_info JSON COMMENT 'Thông tin nhà cung cấp',
    technical_data JSON COMMENT 'Dữ liệu kỹ thuật',
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_code (material_code),
    INDEX idx_category (category),
    INDEX idx_grade (grade),
    INDEX idx_unit (unit_standard),
    FULLTEXT idx_name (material_name_vn, material_name_en)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Thư viện vật liệu chuẩn hóa';


-- TABLE 6: Naming Convention Templates
-- ====================================
CREATE TABLE IF NOT EXISTS naming_templates (
    template_id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Template info
    template_name VARCHAR(100) UNIQUE NOT NULL,
    template_type ENUM('work_item', 'material', 'file', 'parameter') NOT NULL,
    
    -- Pattern
    pattern VARCHAR(500) NOT NULL COMMENT '{ACTION} {OBJECT} {LOCATION} - {SPECS} - {GRADE}',
    example_vn TEXT COMMENT 'Đào đất móng - 1.25m3 - đất cấp 3',
    example_en TEXT,
    
    -- Rules (JSON)
    rules JSON COMMENT 'Quy tắc: lowercase vị trí, viết hoa động từ, etc.',
    
    -- Usage
    applicable_to JSON COMMENT 'Áp dụng cho: ["SEC-01-01", "SEC-02"]',
    priority INT DEFAULT 10,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_type (template_type),
    INDEX idx_name (template_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Templates đặt tên theo chuẩn';


-- ====================================
-- SAMPLE DATA: Legal Codes
-- ====================================
INSERT INTO legal_work_codes (
    legal_code, legal_code_prefix, legal_code_number, legal_code_suffix,
    name_official_vn, name_natural_vn, name_en,
    circular_number, appendix_code, category_level_1, category_level_2,
    unit_standard
) VALUES
-- Công tác đất (AA prefix)
('AA.1111', 'AA', '1111', NULL, 
 'Đào đất hố móng bằng máy, chiều sâu <= 1.25m, đất cấp 3',
 'Đào đất hố móng bằng máy - 1.25m - đất cấp 3',
 'Excavate foundation pit by machine - depth 1.25m - soil class 3',
 '12/2021/TT-BXD', 'Phụ lục I', 'Xây dựng', 'Công tác đất', 'm3'),

('AA.1112a', 'AA', '1112', 'a',
 'Đào đất rãnh móng bằng máy, chiều sâu > 1.25m đến 1.75m, đất cấp 2',
 'Đào đất rãnh móng bằng máy - 1.75m - đất cấp 2',
 'Excavate trench by machine - depth 1.75m - soil class 2',
 '12/2021/TT-BXD', 'Phụ lục I', 'Xây dựng', 'Công tác đất', 'm3'),

-- Công tác bê tông (AF prefix)
('AF.1201', 'AF', '1201', NULL,
 'Bê tông lót móng, chiều rộng <= 250cm, vữa bê tông PC30',
 'Đổ bê tông lót móng - M100 đá 4x6',
 'Cast concrete foundation bed - M100',
 '12/2021/TT-BXD', 'Phụ lục I', 'Xây dựng', 'Bê tông', 'm3'),

('AF.2101', 'AF', '2101', NULL,
 'Bê tông dầm, cột, vách, chiều cao đổ <= 3.5m, M200',
 'Đổ bê tông dầm cột - M200 - thương phẩm',
 'Cast concrete beam column - M200 commercial',
 '12/2021/TT-BXD', 'Phụ lục I', 'Xây dựng', 'Bê tông kết cấu', 'm3'),

-- Cốt thép (AG prefix)
('AG.1101', 'AG', '1101', NULL,
 'Gia công lắp dựng cốt thép móng, đường kính D<10, CB300',
 'Cốt thép móng - D<10 CB300',
 'Rebar foundation - D<10 CB300',
 '12/2021/TT-BXD', 'Phụ lục I', 'Xây dựng', 'Cốt thép', 'tấn'),

-- Xây (AE prefix)
('AE.1101', 'AE', '1101', NULL,
 'Xây tường thẳng, chiều dày <= 10cm, gạch ống 6x10.5x22',
 'Xây tường gạch ống - dày 100mm - vữa M75',
 'Build brick wall - 100mm - mortar M75',
 '12/2021/TT-BXD', 'Phụ lục I', 'Xây dựng', 'Xây', 'm2');


-- ====================================
-- SAMPLE DATA: ISO Codes
-- ====================================
INSERT INTO iso_classification_codes (
    iso_code, entity_code, entity_name_vn, entity_name_en,
    system_code, system_name_vn, system_name_en,
    element_code, element_name_vn, element_name_en,
    product_code, product_name_vn, product_name_en,
    full_description_vn, level
) VALUES
('Pr_21', 'Pr', 'Công việc', 'Process', 
 '21', 'Hệ thống tường', 'Wall system',
 NULL, NULL, NULL,
 NULL, NULL, NULL,
 'Công việc - Hệ thống tường', 2),

('Pr_21_31', 'Pr', 'Công việc', 'Process',
 '21', 'Hệ thống tường', 'Wall system',
 '31', 'Bê tông', 'Concrete',
 NULL, NULL, NULL,
 'Công việc - Tường - Bê tông', 3),

('Pr_21_31_13', 'Pr', 'Công việc', 'Process',
 '21', 'Hệ thống tường', 'Wall system',
 '31', 'Bê tông', 'Concrete',
 '13', 'Mác 200', 'Grade M200',
 'Công việc - Tường bê tông - Mác 200', 4);


-- ====================================
-- SAMPLE DATA: Mapping
-- ====================================
INSERT INTO work_code_mapping (
    work_code, legal_code, iso_code, sec_code,
    mapping_type, confidence_score,
    description, unit
) VALUES
('S01-EARTH-EXCAV-0001', 'AA.1111', 'Pr_01_10_01', 'SEC-01-01',
 'verified', 95.0,
 'Đào đất hố móng bằng máy', 'm3'),

('S02-CONC-M100-0001', 'AF.1201', 'Pr_21_31_10', 'SEC-02',
 'verified', 92.0,
 'Đổ bê tông lót móng M100', 'm3');


-- ====================================
-- SAMPLE DATA: Naming Templates
-- ====================================
INSERT INTO naming_templates (
    template_name, template_type, pattern, example_vn, rules, applicable_to
) VALUES
('Earthwork Standard', 'work_item',
 '{ACTION} {OBJECT} {LOCATION} - {DEPTH} - {SOIL_CLASS}',
 'Đào đất hố móng - 1.25m - đất cấp 3',
 '{"action_case": "capitalize", "location_case": "lowercase", "use_dash": true}',
 '["SEC-01-01"]'),

('Concrete Standard', 'work_item',
 '{ACTION} {ELEMENT} - {GRADE} - {TYPE}',
 'Đổ bê tông dầm sàn - M350 - thương phẩm',
 '{"grade_format": "M{number}", "use_dash": true}',
 '["SEC-02"]'),

('Masonry Standard', 'work_item',
 '{ACTION} {MATERIAL} {ELEMENT} - {THICKNESS} - {MORTAR}',
 'Xây tường gạch ống - dày 100mm - vữa M75',
 '{"thickness_unit": "mm", "use_dash": true}',
 '["SEC-03"]');
