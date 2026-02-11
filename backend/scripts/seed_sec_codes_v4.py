"""
Seed SEC Code v4.0 reference data — 3-Level Format.

Populates sec_codes_v4 table with standard codes and activity_bom links.
Code format: [PREFIX].[GROUP].[TYPE]
  e.g.  A.CONC.STR  (Activity · Concrete · Structural)

Each GROUP.TYPE suffix can have up to 4 prefixes (A/M/L/E).
All Activity (A) codes are seeded.  M/L/E variants are added for the
most common work packages to enable same-suffix BOM linking:
  A.CONC.STR → M.CONC.STR, L.CONC.STR, E.CONC.STR

Usage:
    cd backend
    python scripts/seed_sec_codes_v4.py
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.sec_code_v4 import SECCodeV4
from app.models.activity_bom import ActivityBOM


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMPACT REFERENCE DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Each row: (GROUP, TYPE, name_vi, name_en, unit, keywords_vi, keywords_en, waste%)
# All rows get an A.* code.  Rows whose GROUP.TYPE also appears in
# RESOURCE_VARIANTS get M.*/L.*/E.* codes as well.

ALL_CODES = [
    # ── Nhóm Đất & Cọc ───────────────────────────
    ('SOIL', 'EXC', 'Đào đất', 'Excavation', 'm3',
     '["đào đất", "đào", "excavation"]',
     '["excavation", "earthwork"]', 2.0),
    ('SOIL', 'FIL', 'Đắp/Lấp đất', 'Fill / backfill', 'm3',
     '["đắp đất", "lấp đất", "san lấp"]',
     '["fill", "backfill"]', 5.0),
    ('SOIL', 'GRD', 'San nền', 'Grading', 'm3',
     '["san nền", "san lấp"]',
     '["grading", "leveling"]', 3.0),
    ('SOIL', 'TRN', 'Vận chuyển đất', 'Soil transport', 'm3',
     '["vận chuyển đất", "chở đất"]',
     '["transport", "hauling"]', 0.0),
    ('AGGT', 'CMP', 'Cấp phối đá dăm', 'Aggregate compaction', 'm3',
     '["cấp phối", "đá dăm", "aggregate"]',
     '["aggregate", "compaction", "gravel"]', 5.0),
    ('PILE', 'BOR', 'Cọc khoan nhồi', 'Bored pile', 'm',
     '["cọc khoan nhồi", "cọc nhồi", "khoan cọc"]',
     '["bored pile", "drilled shaft"]', 2.0),
    ('PILE', 'DRV', 'Cọc ép/đóng', 'Driven pile', 'm',
     '["cọc ép", "đóng cọc", "cọc đóng"]',
     '["driven pile", "pile driving"]', 2.0),
    ('PILE', 'TST', 'Thí nghiệm cọc', 'Pile test', 'lần',
     '["thí nghiệm cọc", "PDA", "PIT"]',
     '["pile test", "PDA", "PIT"]', 0.0),

    # ── Nhóm Bê tông & Cốt thép & Ván khuôn ─────
    ('CONC', 'STR', 'BT kết cấu', 'Structural concrete', 'm3',
     '["bê tông", "kết cấu", "đổ bê tông", "cột", "dầm", "sàn"]',
     '["concrete", "structural", "pour"]', 3.0),
    ('CONC', 'LEA', 'BT lót', 'Lean concrete', 'm3',
     '["bê tông lót", "lót"]',
     '["lean concrete", "blinding"]', 5.0),
    ('CONC', 'FND', 'BT móng', 'Foundation concrete', 'm3',
     '["bê tông móng", "móng"]',
     '["concrete", "foundation"]', 3.0),
    ('RBAR', 'STR', 'Cốt thép kết cấu', 'Structural rebar', 'kg',
     '["cốt thép", "thép", "sắt", "gia công thép"]',
     '["rebar", "reinforcement", "steel bar"]', 2.0),
    ('RBAR', 'STL', 'Thép hình', 'Structural steel', 'kg',
     '["thép hình", "H-beam", "I-beam"]',
     '["structural steel", "H-beam", "I-beam"]', 3.0),
    ('FWRK', 'WOD', 'Ván khuôn gỗ', 'Wood formwork', 'm2',
     '["ván khuôn", "coppha", "gỗ"]',
     '["formwork", "wood", "plywood"]', 10.0),
    ('FWRK', 'STL', 'Ván khuôn thép', 'Steel formwork', 'm2',
     '["ván khuôn thép", "coppha thép"]',
     '["steel formwork"]', 2.0),

    # ── Nhóm Hoàn thiện ──────────────────────────
    ('BRCK', 'SOL', 'Gạch đặc', 'Solid brick', 'viên',
     '["gạch đặc", "gạch ống", "xây tường"]',
     '["solid brick", "clay brick"]', 3.0),
    ('BRCK', 'AAC', 'Block AAC', 'AAC block', 'viên',
     '["AAC", "block nhẹ", "bê tông khí"]',
     '["AAC block", "autoclaved aerated concrete"]', 3.0),
    ('BRCK', 'CON', 'Block bê tông', 'Concrete block', 'viên',
     '["block bê tông", "gạch block"]',
     '["concrete block", "CMU"]', 3.0),
    ('PLST', 'CEM', 'Trát vữa xi măng', 'Cement plaster', 'm2',
     '["trát", "vữa", "xi măng", "trát tường"]',
     '["plaster", "cement render"]', 5.0),
    ('PLST', 'PUT', 'Bả matit', 'Putty / skim coat', 'm2',
     '["bả matit", "matit", "bả"]',
     '["putty", "skim coat"]', 5.0),
    ('PANT', 'INT', 'Sơn nội thất', 'Interior paint', 'm2',
     '["sơn", "sơn nước", "nội thất", "sơn trong"]',
     '["paint", "interior"]', 5.0),
    ('PANT', 'EXT', 'Sơn ngoại thất', 'Exterior paint', 'm2',
     '["sơn ngoài", "ngoại thất", "sơn ngoại"]',
     '["paint", "exterior"]', 5.0),
    ('PANT', 'WPF', 'Sơn chống thấm', 'Waterproof paint', 'm2',
     '["sơn chống thấm"]',
     '["waterproof paint"]', 5.0),
    ('TILE', 'CER', 'Lát ceramic', 'Ceramic tile', 'm2',
     '["gạch lát", "ceramic", "lát nền", "lát sàn"]',
     '["ceramic tile", "floor tile"]', 5.0),
    ('TILE', 'GRN', 'Lát granite', 'Granite tile', 'm2',
     '["granite", "đá granite", "lát đá"]',
     '["granite tile"]', 3.0),
    ('TILE', 'STN', 'Ốp đá tự nhiên', 'Natural stone cladding', 'm2',
     '["đá tự nhiên", "ốp đá", "marble"]',
     '["natural stone", "marble", "cladding"]', 3.0),
    ('TILE', 'VYL', 'Sàn vinyl/SPC', 'Vinyl / SPC flooring', 'm2',
     '["vinyl", "SPC", "sàn nhựa"]',
     '["vinyl", "SPC", "LVT"]', 3.0),
    ('TILE', 'LAM', 'Sàn gỗ công nghiệp', 'Laminate flooring', 'm2',
     '["sàn gỗ", "gỗ công nghiệp", "laminate"]',
     '["laminate", "engineered wood"]', 5.0),
    ('CLNG', 'GYP', 'Trần thạch cao', 'Gypsum ceiling', 'm2',
     '["trần", "thạch cao", "trần treo"]',
     '["ceiling", "gypsum", "suspended"]', 5.0),
    ('CLNG', 'ALU', 'Trần nhôm', 'Aluminium ceiling', 'm2',
     '["trần nhôm"]',
     '["aluminium ceiling"]', 3.0),
    ('DOOR', 'WOD', 'Cửa gỗ', 'Wooden door', 'bộ',
     '["cửa gỗ", "cửa phòng"]',
     '["wooden door"]', 2.0),
    ('DOOR', 'ALU', 'Cửa nhôm kính', 'Aluminium glass door', 'bộ',
     '["cửa nhôm", "cửa kính", "nhôm kính"]',
     '["aluminium door", "glass door"]', 2.0),
    ('DOOR', 'FIR', 'Cửa chống cháy', 'Fire-rated door', 'bộ',
     '["cửa chống cháy", "cửa PCCC"]',
     '["fire door", "fire-rated"]', 1.0),
    ('WPRF', 'MEM', 'Chống thấm màng', 'Membrane waterproofing', 'm2',
     '["chống thấm", "màng chống thấm", "bitumen"]',
     '["waterproofing", "membrane", "bitumen"]', 5.0),
    ('WPRF', 'COT', 'Chống thấm quét', 'Coating waterproofing', 'm2',
     '["chống thấm quét", "sika", "quét chống thấm"]',
     '["waterproof coating", "liquid membrane"]', 5.0),
    ('SANT', 'TLT', 'TBVS bồn cầu', 'Toilet bowl', 'bộ',
     '["bồn cầu", "toilet", "vệ sinh"]',
     '["toilet", "WC"]', 1.0),
    ('SANT', 'BSN', 'TBVS lavabo', 'Wash basin', 'bộ',
     '["lavabo", "chậu rửa"]',
     '["basin", "lavatory", "sink"]', 1.0),
    ('RLNG', 'GLS', 'Lan can kính', 'Glass railing', 'm',
     '["lan can kính", "rào kính"]',
     '["glass railing", "balustrade"]', 2.0),
    ('RLNG', 'INX', 'Lan can inox', 'Stainless steel railing', 'm',
     '["lan can inox", "tay vịn inox"]',
     '["stainless railing", "inox"]', 2.0),

    # ── Nhóm Mặt dựng ───────────────────────────
    ('CWLL', 'GLS', 'Vách kính mặt dựng', 'Glass curtain wall', 'm2',
     '["vách kính", "mặt dựng", "curtain wall"]',
     '["curtain wall", "glass facade"]', 3.0),
    ('CWLL', 'ALU', 'Cửa sổ nhôm kính', 'Aluminium window', 'bộ',
     '["cửa sổ", "nhôm kính"]',
     '["aluminium window"]', 2.0),
    ('CLAD', 'ALU', 'Ốp aluminium panel', 'Aluminium panel cladding', 'm2',
     '["ốp nhôm", "aluminium panel", "ACP"]',
     '["aluminium panel", "ACP", "cladding"]', 3.0),
    ('CLAD', 'GRN', 'Ốp đá granite ngoài', 'External granite cladding', 'm2',
     '["ốp đá ngoài", "granite ngoài"]',
     '["granite cladding", "external stone"]', 3.0),
    ('CLAD', 'LVR', 'Lam chắn nắng', 'Sun louver', 'm2',
     '["lam chắn nắng", "lam nhôm", "louver"]',
     '["louver", "sun shade"]', 2.0),

    # ── Nhóm Điện ────────────────────────────────
    ('CABL', 'PWR', 'Cáp động lực', 'Power cable', 'm',
     '["cáp động lực", "cáp điện", "dây điện"]',
     '["power cable", "electrical cable"]', 3.0),
    ('CABL', 'CTL', 'Cáp điều khiển', 'Control cable', 'm',
     '["cáp điều khiển", "cáp control"]',
     '["control cable"]', 3.0),
    ('CABL', 'COM', 'Cáp thông tin', 'Communication cable', 'm',
     '["cáp thông tin", "cáp mạng", "LAN", "cáp quang"]',
     '["communication cable", "LAN", "fiber"]', 3.0),
    ('LITE', 'LED', 'Đèn LED', 'LED light', 'bộ',
     '["đèn LED", "đèn", "chiếu sáng"]',
     '["LED light", "lighting"]', 1.0),
    ('LITE', 'EMG', 'Đèn sự cố', 'Emergency light', 'bộ',
     '["đèn sự cố", "đèn thoát hiểm", "exit"]',
     '["emergency light", "exit light"]', 1.0),
    ('PANL', 'MSB', 'Tủ điện chính', 'Main switchboard', 'bộ',
     '["tủ điện chính", "MSB", "tủ tổng"]',
     '["MSB", "main switchboard"]', 0.0),
    ('PANL', 'DSB', 'Tủ phân phối', 'Distribution board', 'bộ',
     '["tủ phân phối", "DB", "tủ điện"]',
     '["distribution board", "DB"]', 0.0),
    ('BRKR', 'MCB', 'MCB/MCCB', 'MCB / MCCB', 'cái',
     '["MCB", "MCCB", "aptomat"]',
     '["MCB", "MCCB", "circuit breaker"]', 1.0),
    ('BRKR', 'RCB', 'RCCB/RCBO', 'RCCB / RCBO', 'cái',
     '["RCCB", "RCBO", "chống rò"]',
     '["RCCB", "RCBO", "residual current"]', 1.0),
    ('COND', 'PVC', 'Ống luồn PVC', 'PVC conduit', 'm',
     '["ống luồn", "PVC", "ống nhựa"]',
     '["PVC conduit"]', 5.0),
    ('COND', 'MTL', 'Ống luồn kim loại', 'Metal conduit', 'm',
     '["ống luồn kim loại", "ống thép"]',
     '["metal conduit", "EMT", "IMC"]', 3.0),
    ('TRAY', 'GVN', 'Máng cáp mạ kẽm', 'Galvanised cable tray', 'm',
     '["máng cáp", "cable tray", "mạ kẽm"]',
     '["cable tray", "galvanised"]', 3.0),

    # ── Nhóm Nước ────────────────────────────────
    ('PIPE', 'SUP', 'Ống cấp nước', 'Water supply pipe', 'm',
     '["ống cấp", "cấp nước", "ống nước"]',
     '["water supply", "pipe"]', 3.0),
    ('PIPE', 'DRN', 'Ống thoát nước', 'Drainage pipe', 'm',
     '["ống thoát", "thoát nước"]',
     '["drainage", "pipe"]', 3.0),
    ('PIPE', 'FIR', 'Ống PCCC', 'Fire pipe', 'm',
     '["ống PCCC", "ống chữa cháy"]',
     '["fire pipe", "sprinkler pipe"]', 3.0),
    ('VALV', 'GAT', 'Van cổng', 'Gate valve', 'cái',
     '["van cổng"]',
     '["gate valve"]', 0.0),
    ('VALV', 'BFL', 'Van bướm', 'Butterfly valve', 'cái',
     '["van bướm"]',
     '["butterfly valve"]', 0.0),
    ('VALV', 'BAL', 'Van bi', 'Ball valve', 'cái',
     '["van bi"]',
     '["ball valve"]', 0.0),
    ('VALV', 'CHK', 'Van một chiều', 'Check valve', 'cái',
     '["van một chiều", "van 1 chiều"]',
     '["check valve"]', 0.0),
    ('FITG', 'ELB', 'Cút (elbow)', 'Elbow fitting', 'cái',
     '["cút", "elbow", "co"]',
     '["elbow", "fitting"]', 2.0),
    ('FITG', 'TEE', 'Tê', 'Tee fitting', 'cái',
     '["tê", "tee"]',
     '["tee", "fitting"]', 2.0),
    ('FITG', 'RED', 'Côn thu', 'Reducer fitting', 'cái',
     '["côn thu", "reducer"]',
     '["reducer", "fitting"]', 2.0),
    ('FITG', 'FLG', 'Bích', 'Flange', 'cái',
     '["bích", "mặt bích"]',
     '["flange"]', 1.0),
    ('PUMP', 'SUB', 'Bơm chìm', 'Submersible pump', 'bộ',
     '["bơm chìm"]',
     '["submersible pump"]', 0.0),
    ('PUMP', 'CEN', 'Bơm ly tâm', 'Centrifugal pump', 'bộ',
     '["bơm ly tâm"]',
     '["centrifugal pump"]', 0.0),
    ('PUMP', 'BOS', 'Bơm tăng áp', 'Booster pump', 'bộ',
     '["bơm tăng áp"]',
     '["booster pump"]', 0.0),
    ('TANK', 'WTR', 'Bể nước', 'Water tank', 'bộ',
     '["bể nước", "bồn nước"]',
     '["water tank"]', 0.0),

    # ── Nhóm HVAC ────────────────────────────────
    ('HVAC', 'AHU', 'AHU', 'Air handling unit', 'bộ',
     '["AHU", "air handling"]',
     '["AHU", "air handling unit"]', 0.0),
    ('HVAC', 'FCU', 'FCU', 'Fan coil unit', 'bộ',
     '["FCU", "fan coil"]',
     '["FCU", "fan coil unit"]', 0.0),
    ('HVAC', 'SPL', 'Điều hòa split', 'Split air conditioner', 'bộ',
     '["điều hòa", "split", "máy lạnh"]',
     '["split AC", "air conditioner"]', 0.0),
    ('HVAC', 'VRF', 'VRF', 'Variable refrigerant flow', 'bộ',
     '["VRF", "VRV"]',
     '["VRF", "VRV"]', 0.0),
    ('DUCT', 'GVN', 'Ống gió tôn mạ kẽm', 'GI duct', 'm2',
     '["ống gió", "tôn mạ kẽm", "duct"]',
     '["GI duct", "galvanised duct"]', 5.0),
    ('DUCT', 'FLX', 'Ống gió mềm', 'Flexible duct', 'm',
     '["ống gió mềm", "ống mềm"]',
     '["flexible duct"]', 3.0),
    ('INSU', 'RBR', 'Cách nhiệt cao su', 'Rubber insulation', 'm2',
     '["cách nhiệt", "cao su", "bảo ôn"]',
     '["rubber insulation", "Armaflex"]', 5.0),

    # ── Nhóm PCCC ────────────────────────────────
    ('SPRK', 'UPR', 'Sprinkler quay lên', 'Upright sprinkler', 'đầu',
     '["sprinkler", "quay lên", "upright"]',
     '["upright sprinkler"]', 1.0),
    ('SPRK', 'PND', 'Sprinkler quay xuống', 'Pendent sprinkler', 'đầu',
     '["sprinkler", "quay xuống", "pendent"]',
     '["pendent sprinkler"]', 1.0),
    ('FALM', 'SMK', 'Đầu báo khói', 'Smoke detector', 'cái',
     '["đầu báo khói", "báo khói"]',
     '["smoke detector"]', 1.0),
    ('FALM', 'HET', 'Đầu báo nhiệt', 'Heat detector', 'cái',
     '["đầu báo nhiệt", "báo nhiệt"]',
     '["heat detector"]', 1.0),
    ('FALM', 'PNL', 'Tủ trung tâm báo cháy', 'Fire alarm panel', 'bộ',
     '["tủ báo cháy", "trung tâm báo cháy"]',
     '["fire alarm panel", "FACP"]', 0.0),
    ('FFGT', 'EXT', 'Bình chữa cháy', 'Fire extinguisher', 'bình',
     '["bình chữa cháy", "bình cứu hoả"]',
     '["fire extinguisher"]', 0.0),
    ('FFGT', 'HOS', 'Vòi chữa cháy', 'Fire hose', 'bộ',
     '["vòi chữa cháy", "hộp cứu hoả"]',
     '["fire hose", "hose reel"]', 0.0),
    ('PUMP', 'FIR', 'Bơm chữa cháy', 'Fire pump', 'bộ',
     '["bơm chữa cháy", "bơm PCCC"]',
     '["fire pump"]', 0.0),

    # ── Nhóm Đường & Cảnh quan ───────────────────
    ('ROAD', 'ASP', 'Rải BTN (asphalt)', 'Asphalt paving', 'm2',
     '["BTN", "asphalt", "nhựa đường", "rải nhựa"]',
     '["asphalt", "paving"]', 3.0),
    ('ROAD', 'CRB', 'Bó vỉa', 'Curb', 'm',
     '["bó vỉa", "bordure"]',
     '["curb", "kerb"]', 2.0),
    ('ROAD', 'MRK', 'Sơn vạch', 'Road marking', 'm2',
     '["sơn vạch", "kẻ vạch"]',
     '["road marking"]', 5.0),
    ('LAND', 'TRE', 'Cây xanh', 'Tree planting', 'cây',
     '["cây xanh", "trồng cây"]',
     '["tree", "planting"]', 5.0),
    ('LAND', 'TRF', 'Cỏ thảm', 'Turf grass', 'm2',
     '["cỏ", "thảm cỏ", "cỏ nhung"]',
     '["turf", "grass"]', 5.0),
    ('LAND', 'IRG', 'Hệ thống tưới', 'Irrigation system', 'bộ',
     '["tưới", "hệ thống tưới", "tưới cây"]',
     '["irrigation"]', 3.0),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESOURCE VARIANTS — GROUP.TYPE that also get M / L / E codes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Only the most common work packages need full quad-table entries.
# Format: 'GROUP.TYPE': set of extra prefixes to create.

RESOURCE_VARIANTS = {
    # ── Đất & Cọc ─────────────────────────────────
    'SOIL.EXC': {'M', 'L', 'E'},
    'SOIL.FIL': {'M', 'L', 'E'},
    'AGGT.CMP': {'M', 'L', 'E'},
    'PILE.BOR': {'M', 'L', 'E'},
    'PILE.DRV': {'M', 'L', 'E'},

    # ── Bê tông & Cốt thép & Ván khuôn ───────────
    'CONC.STR': {'M', 'L', 'E'},
    'CONC.LEA': {'M', 'L', 'E'},
    'CONC.FND': {'M', 'L', 'E'},
    'RBAR.STR': {'M', 'L', 'E'},
    'RBAR.STL': {'M', 'L', 'E'},
    'FWRK.WOD': {'M', 'L'},
    'FWRK.STL': {'M', 'L', 'E'},

    # ── Hoàn thiện ────────────────────────────────
    'BRCK.SOL': {'M', 'L'},
    'BRCK.AAC': {'M', 'L'},
    'BRCK.CON': {'M', 'L'},
    'PLST.CEM': {'M', 'L'},
    'PLST.PUT': {'M', 'L'},
    'PANT.INT': {'M', 'L'},
    'PANT.EXT': {'M', 'L'},
    'TILE.CER': {'M', 'L'},
    'TILE.GRN': {'M', 'L'},
    'CLNG.GYP': {'M', 'L'},
    'DOOR.WOD': {'M', 'L'},
    'DOOR.ALU': {'M', 'L'},
    'WPRF.MEM': {'M', 'L'},
    'WPRF.COT': {'M', 'L'},
    'SANT.TLT': {'M', 'L'},
    'SANT.BSN': {'M', 'L'},
    'RLNG.GLS': {'M', 'L'},

    # ── Mặt dựng ─────────────────────────────────
    'CWLL.GLS': {'M', 'L', 'E'},
    'CLAD.ALU': {'M', 'L'},

    # ── Điện ──────────────────────────────────────
    'CABL.PWR': {'M', 'L'},
    'CABL.CTL': {'M', 'L'},
    'LITE.LED': {'M', 'L'},
    'PANL.MSB': {'M', 'L'},
    'PANL.DSB': {'M', 'L'},
    'BRKR.MCB': {'M', 'L'},
    'COND.PVC': {'M', 'L'},
    'TRAY.GVN': {'M', 'L'},

    # ── Nước ──────────────────────────────────────
    'PIPE.SUP': {'M', 'L'},
    'PIPE.DRN': {'M', 'L'},
    'PIPE.FIR': {'M', 'L'},
    'VALV.GAT': {'M', 'L'},
    'FITG.ELB': {'M'},
    'FITG.TEE': {'M'},
    'FITG.RED': {'M'},
    'PUMP.SUB': {'M', 'L', 'E'},
    'PUMP.CEN': {'M', 'L', 'E'},
    'PUMP.BOS': {'M', 'L', 'E'},
    'TANK.WTR': {'M', 'L'},

    # ── HVAC ──────────────────────────────────────
    'HVAC.AHU': {'M', 'L', 'E'},
    'HVAC.FCU': {'M', 'L'},
    'HVAC.SPL': {'M', 'L'},
    'HVAC.VRF': {'M', 'L', 'E'},
    'DUCT.GVN': {'M', 'L'},
    'INSU.RBR': {'M', 'L'},

    # ── PCCC ──────────────────────────────────────
    'SPRK.UPR': {'M', 'L'},
    'SPRK.PND': {'M', 'L'},
    'FALM.SMK': {'M', 'L'},
    'FALM.PNL': {'M', 'L'},
    'FFGT.EXT': {'M'},
    'FFGT.HOS': {'M', 'L'},
    'PUMP.FIR': {'M', 'L', 'E'},

    # ── Đường & Cảnh quan ─────────────────────────
    'ROAD.ASP': {'M', 'L', 'E'},
    'ROAD.CRB': {'M', 'L'},
    'LAND.TRE': {'M', 'L'},
    'LAND.TRF': {'M', 'L'},
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BOM LINKS: Activity → Resources
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# (activity_code, resource_code, resource_type, quantity_factor)
BOM_LINKS = [
    # ── Đất & Cọc ─────────────────────────────────
    ('A.SOIL.EXC', 'M.SOIL.EXC', 'M', 1.00),
    ('A.SOIL.EXC', 'L.SOIL.EXC', 'L', 0.05),
    ('A.SOIL.EXC', 'E.SOIL.EXC', 'E', 0.03),

    ('A.SOIL.FIL', 'M.SOIL.FIL', 'M', 1.05),
    ('A.SOIL.FIL', 'L.SOIL.FIL', 'L', 0.08),
    ('A.SOIL.FIL', 'E.SOIL.FIL', 'E', 0.03),

    ('A.AGGT.CMP', 'M.AGGT.CMP', 'M', 1.05),
    ('A.AGGT.CMP', 'L.AGGT.CMP', 'L', 0.06),
    ('A.AGGT.CMP', 'E.AGGT.CMP', 'E', 0.03),

    ('A.PILE.BOR', 'M.PILE.BOR', 'M', 1.05),
    ('A.PILE.BOR', 'L.PILE.BOR', 'L', 0.10),
    ('A.PILE.BOR', 'E.PILE.BOR', 'E', 0.08),

    ('A.PILE.DRV', 'M.PILE.DRV', 'M', 1.02),
    ('A.PILE.DRV', 'L.PILE.DRV', 'L', 0.08),
    ('A.PILE.DRV', 'E.PILE.DRV', 'E', 0.06),

    # ── Bê tông kết cấu ──────────────────────────
    ('A.CONC.STR', 'M.CONC.STR', 'M', 1.05),
    ('A.CONC.STR', 'L.CONC.STR', 'L', 0.15),
    ('A.CONC.STR', 'E.CONC.STR', 'E', 0.02),

    ('A.CONC.LEA', 'M.CONC.LEA', 'M', 1.05),
    ('A.CONC.LEA', 'L.CONC.LEA', 'L', 0.08),
    ('A.CONC.LEA', 'E.CONC.LEA', 'E', 0.01),

    ('A.CONC.FND', 'M.CONC.FND', 'M', 1.05),
    ('A.CONC.FND', 'L.CONC.FND', 'L', 0.12),
    ('A.CONC.FND', 'E.CONC.FND', 'E', 0.02),

    # ── Cốt thép ─────────────────────────────────
    ('A.RBAR.STR', 'M.RBAR.STR', 'M', 1.02),
    ('A.RBAR.STR', 'L.RBAR.STR', 'L', 0.012),
    ('A.RBAR.STR', 'E.RBAR.STR', 'E', 0.005),

    ('A.RBAR.STL', 'M.RBAR.STL', 'M', 1.03),
    ('A.RBAR.STL', 'L.RBAR.STL', 'L', 0.015),
    ('A.RBAR.STL', 'E.RBAR.STL', 'E', 0.01),

    # ── Ván khuôn ─────────────────────────────────
    ('A.FWRK.WOD', 'M.FWRK.WOD', 'M', 1.10),
    ('A.FWRK.WOD', 'L.FWRK.WOD', 'L', 0.25),

    ('A.FWRK.STL', 'M.FWRK.STL', 'M', 1.05),
    ('A.FWRK.STL', 'L.FWRK.STL', 'L', 0.15),
    ('A.FWRK.STL', 'E.FWRK.STL', 'E', 0.02),

    # ── Gạch xây (cross-group: brickwork → mortar) ─
    ('A.BRCK.SOL', 'M.BRCK.SOL', 'M', 1.03),
    ('A.BRCK.SOL', 'M.PLST.CEM', 'M', 0.30),
    ('A.BRCK.SOL', 'L.BRCK.SOL', 'L', 0.60),

    ('A.BRCK.AAC', 'M.BRCK.AAC', 'M', 1.03),
    ('A.BRCK.AAC', 'M.PLST.CEM', 'M', 0.20),
    ('A.BRCK.AAC', 'L.BRCK.AAC', 'L', 0.45),

    ('A.BRCK.CON', 'M.BRCK.CON', 'M', 1.03),
    ('A.BRCK.CON', 'M.PLST.CEM', 'M', 0.25),
    ('A.BRCK.CON', 'L.BRCK.CON', 'L', 0.50),

    # ── Trát / Bả / Sơn ──────────────────────────
    ('A.PLST.CEM', 'M.PLST.CEM', 'M', 1.05),
    ('A.PLST.CEM', 'L.PLST.CEM', 'L', 0.15),

    ('A.PLST.PUT', 'M.PLST.PUT', 'M', 1.05),
    ('A.PLST.PUT', 'L.PLST.PUT', 'L', 0.10),

    ('A.PANT.INT', 'M.PANT.INT', 'M', 1.05),
    ('A.PANT.INT', 'L.PANT.INT', 'L', 0.05),

    ('A.PANT.EXT', 'M.PANT.EXT', 'M', 1.05),
    ('A.PANT.EXT', 'L.PANT.EXT', 'L', 0.06),

    # ── Lát / Ốp ─────────────────────────────────
    ('A.TILE.CER', 'M.TILE.CER', 'M', 1.05),
    ('A.TILE.CER', 'L.TILE.CER', 'L', 0.20),

    ('A.TILE.GRN', 'M.TILE.GRN', 'M', 1.03),
    ('A.TILE.GRN', 'L.TILE.GRN', 'L', 0.25),

    # ── Trần ──────────────────────────────────────
    ('A.CLNG.GYP', 'M.CLNG.GYP', 'M', 1.05),
    ('A.CLNG.GYP', 'L.CLNG.GYP', 'L', 0.15),

    # ── Cửa ───────────────────────────────────────
    ('A.DOOR.WOD', 'M.DOOR.WOD', 'M', 1.00),
    ('A.DOOR.WOD', 'L.DOOR.WOD', 'L', 0.50),

    ('A.DOOR.ALU', 'M.DOOR.ALU', 'M', 1.00),
    ('A.DOOR.ALU', 'L.DOOR.ALU', 'L', 0.40),

    # ── Chống thấm ────────────────────────────────
    ('A.WPRF.MEM', 'M.WPRF.MEM', 'M', 1.05),
    ('A.WPRF.MEM', 'L.WPRF.MEM', 'L', 0.10),

    ('A.WPRF.COT', 'M.WPRF.COT', 'M', 1.05),
    ('A.WPRF.COT', 'L.WPRF.COT', 'L', 0.08),

    # ── Thiết bị vệ sinh ─────────────────────────
    ('A.SANT.TLT', 'M.SANT.TLT', 'M', 1.00),
    ('A.SANT.TLT', 'L.SANT.TLT', 'L', 0.50),

    ('A.SANT.BSN', 'M.SANT.BSN', 'M', 1.00),
    ('A.SANT.BSN', 'L.SANT.BSN', 'L', 0.40),

    # ── Lan can ───────────────────────────────────
    ('A.RLNG.GLS', 'M.RLNG.GLS', 'M', 1.03),
    ('A.RLNG.GLS', 'L.RLNG.GLS', 'L', 0.30),

    # ── Mặt dựng ─────────────────────────────────
    ('A.CWLL.GLS', 'M.CWLL.GLS', 'M', 1.03),
    ('A.CWLL.GLS', 'L.CWLL.GLS', 'L', 0.25),
    ('A.CWLL.GLS', 'E.CWLL.GLS', 'E', 0.05),

    ('A.CLAD.ALU', 'M.CLAD.ALU', 'M', 1.03),
    ('A.CLAD.ALU', 'L.CLAD.ALU', 'L', 0.20),

    # ── Điện ──────────────────────────────────────
    ('A.CABL.PWR', 'M.CABL.PWR', 'M', 1.03),
    ('A.CABL.PWR', 'L.CABL.PWR', 'L', 0.02),

    ('A.CABL.CTL', 'M.CABL.CTL', 'M', 1.03),
    ('A.CABL.CTL', 'L.CABL.CTL', 'L', 0.02),

    ('A.LITE.LED', 'M.LITE.LED', 'M', 1.00),
    ('A.LITE.LED', 'L.LITE.LED', 'L', 0.30),

    ('A.PANL.MSB', 'M.PANL.MSB', 'M', 1.00),
    ('A.PANL.MSB', 'L.PANL.MSB', 'L', 2.00),

    ('A.PANL.DSB', 'M.PANL.DSB', 'M', 1.00),
    ('A.PANL.DSB', 'L.PANL.DSB', 'L', 1.00),

    ('A.BRKR.MCB', 'M.BRKR.MCB', 'M', 1.00),
    ('A.BRKR.MCB', 'L.BRKR.MCB', 'L', 0.10),

    ('A.COND.PVC', 'M.COND.PVC', 'M', 1.05),
    ('A.COND.PVC', 'L.COND.PVC', 'L', 0.03),

    ('A.TRAY.GVN', 'M.TRAY.GVN', 'M', 1.05),
    ('A.TRAY.GVN', 'L.TRAY.GVN', 'L', 0.05),

    # ── Nước ──────────────────────────────────────
    ('A.PIPE.SUP', 'M.PIPE.SUP', 'M', 1.03),
    ('A.PIPE.SUP', 'L.PIPE.SUP', 'L', 0.05),

    ('A.PIPE.DRN', 'M.PIPE.DRN', 'M', 1.03),
    ('A.PIPE.DRN', 'L.PIPE.DRN', 'L', 0.05),

    ('A.PIPE.FIR', 'M.PIPE.FIR', 'M', 1.03),
    ('A.PIPE.FIR', 'L.PIPE.FIR', 'L', 0.05),

    ('A.VALV.GAT', 'M.VALV.GAT', 'M', 1.00),
    ('A.VALV.GAT', 'L.VALV.GAT', 'L', 0.20),

    ('A.PUMP.SUB', 'M.PUMP.SUB', 'M', 1.00),
    ('A.PUMP.SUB', 'L.PUMP.SUB', 'L', 1.00),
    ('A.PUMP.SUB', 'E.PUMP.SUB', 'E', 0.10),

    ('A.PUMP.CEN', 'M.PUMP.CEN', 'M', 1.00),
    ('A.PUMP.CEN', 'L.PUMP.CEN', 'L', 1.00),
    ('A.PUMP.CEN', 'E.PUMP.CEN', 'E', 0.10),

    ('A.TANK.WTR', 'M.TANK.WTR', 'M', 1.00),
    ('A.TANK.WTR', 'L.TANK.WTR', 'L', 2.00),

    # ── HVAC ──────────────────────────────────────
    ('A.HVAC.AHU', 'M.HVAC.AHU', 'M', 1.00),
    ('A.HVAC.AHU', 'L.HVAC.AHU', 'L', 2.00),
    ('A.HVAC.AHU', 'E.HVAC.AHU', 'E', 0.10),

    ('A.HVAC.FCU', 'M.HVAC.FCU', 'M', 1.00),
    ('A.HVAC.FCU', 'L.HVAC.FCU', 'L', 0.50),

    ('A.HVAC.SPL', 'M.HVAC.SPL', 'M', 1.00),
    ('A.HVAC.SPL', 'L.HVAC.SPL', 'L', 0.50),

    ('A.HVAC.VRF', 'M.HVAC.VRF', 'M', 1.00),
    ('A.HVAC.VRF', 'L.HVAC.VRF', 'L', 2.00),
    ('A.HVAC.VRF', 'E.HVAC.VRF', 'E', 0.15),

    ('A.DUCT.GVN', 'M.DUCT.GVN', 'M', 1.05),
    ('A.DUCT.GVN', 'L.DUCT.GVN', 'L', 0.10),

    ('A.INSU.RBR', 'M.INSU.RBR', 'M', 1.05),
    ('A.INSU.RBR', 'L.INSU.RBR', 'L', 0.08),

    # ── PCCC ──────────────────────────────────────
    ('A.SPRK.UPR', 'M.SPRK.UPR', 'M', 1.01),
    ('A.SPRK.UPR', 'L.SPRK.UPR', 'L', 0.10),

    ('A.SPRK.PND', 'M.SPRK.PND', 'M', 1.01),
    ('A.SPRK.PND', 'L.SPRK.PND', 'L', 0.10),

    ('A.FALM.SMK', 'M.FALM.SMK', 'M', 1.00),
    ('A.FALM.SMK', 'L.FALM.SMK', 'L', 0.15),

    ('A.FALM.PNL', 'M.FALM.PNL', 'M', 1.00),
    ('A.FALM.PNL', 'L.FALM.PNL', 'L', 2.00),

    ('A.FFGT.EXT', 'M.FFGT.EXT', 'M', 1.00),

    ('A.FFGT.HOS', 'M.FFGT.HOS', 'M', 1.00),
    ('A.FFGT.HOS', 'L.FFGT.HOS', 'L', 0.50),

    ('A.PUMP.FIR', 'M.PUMP.FIR', 'M', 1.00),
    ('A.PUMP.FIR', 'L.PUMP.FIR', 'L', 2.00),
    ('A.PUMP.FIR', 'E.PUMP.FIR', 'E', 0.10),

    # ── Đường & Cảnh quan ─────────────────────────
    ('A.ROAD.ASP', 'M.ROAD.ASP', 'M', 1.05),
    ('A.ROAD.ASP', 'L.ROAD.ASP', 'L', 0.03),
    ('A.ROAD.ASP', 'E.ROAD.ASP', 'E', 0.04),

    ('A.ROAD.CRB', 'M.ROAD.CRB', 'M', 1.03),
    ('A.ROAD.CRB', 'L.ROAD.CRB', 'L', 0.10),

    ('A.LAND.TRE', 'M.LAND.TRE', 'M', 1.00),
    ('A.LAND.TRE', 'L.LAND.TRE', 'L', 0.30),

    ('A.LAND.TRF', 'M.LAND.TRF', 'M', 1.05),
    ('A.LAND.TRF', 'L.LAND.TRF', 'L', 0.05),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEEDING LOGIC
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Name prefix labels for non-Activity codes
_PREFIX_LABEL_VI = {'M': 'VT: ', 'L': 'NC: ', 'E': 'MTC: '}
_PREFIX_LABEL_EN = {'M': 'Mat: ', 'L': 'Lab: ', 'E': 'Eqp: '}


def _build_code(prefix: str, group: str, type_code: str) -> str:
    """Build a 3-level code string: PREFIX.GROUP.TYPE"""
    return f"{prefix}.{group}.{type_code}"


def seed_all():
    """Seed all v4.0 reference data."""
    db = SessionLocal()

    try:
        # Clear existing data (BOM first due to FK constraints)
        db.query(ActivityBOM).delete()
        db.query(SECCodeV4).delete()
        db.flush()

        counts = {'A': 0, 'M': 0, 'L': 0, 'E': 0}

        # ── 1. Build all SECCodeV4 records ────────
        for row in ALL_CODES:
            group, type_code, name_vi, name_en, unit, kw_vi, kw_en, waste = row
            suffix = f"{group}.{type_code}"

            # Always create the Activity (A) code
            a_code = _build_code('A', group, type_code)
            db.add(SECCodeV4(
                code=a_code,
                table_type='A',
                group_code=group,
                type_code=type_code,
                name_vi=name_vi,
                name_en=name_en,
                unit=unit,
                keywords_vi=kw_vi,
                keywords_en=kw_en,
                waste_percent=waste,
                is_active=True,
            ))
            counts['A'] += 1

            # Create M/L/E variants if this suffix is listed
            extra = RESOURCE_VARIANTS.get(suffix, set())
            for prefix in sorted(extra):
                r_code = _build_code(prefix, group, type_code)
                lbl_vi = _PREFIX_LABEL_VI.get(prefix, '')
                lbl_en = _PREFIX_LABEL_EN.get(prefix, '')
                db.add(SECCodeV4(
                    code=r_code,
                    table_type=prefix,
                    group_code=group,
                    type_code=type_code,
                    name_vi=f"{lbl_vi}{name_vi}",
                    name_en=f"{lbl_en}{name_en}",
                    unit=unit,
                    keywords_vi=kw_vi,
                    keywords_en=kw_en,
                    waste_percent=waste,
                    is_active=True,
                ))
                counts[prefix] += 1

        db.flush()

        # ── 2. Insert BOM links ───────────────────
        bom_inserted = 0
        for activity, resource, rtype, qty in BOM_LINKS:
            db.add(ActivityBOM(
                activity_code=activity,
                resource_code=resource,
                resource_type=rtype,
                quantity_factor=qty,
            ))
            bom_inserted += 1

        db.commit()

        total = sum(counts.values())
        print(f"\nSeeded {total} SEC v4.0 codes (3-level format):")
        print(f"  Activity  (A): {counts['A']}")
        print(f"  Material  (M): {counts['M']}")
        print(f"  Labour    (L): {counts['L']}")
        print(f"  Equipment (E): {counts['E']}")
        print(f"  BOM links:     {bom_inserted}")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    print("=" * 55)
    print("  SEED SEC CODE v4.0 — 3-Level Format")
    print("  Format: [A|M|L|E].[GROUP].[TYPE]")
    print("=" * 55)
    seed_all()
    print("\nDone.")
