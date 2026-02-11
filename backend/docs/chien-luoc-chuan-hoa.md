# Chiến lược chuẩn hóa dữ liệu - Cost Database

Tài liệu tổng hợp toàn bộ chiến lược chuẩn hóa đang áp dụng trong hệ thống cost-database, bao gồm chuẩn hóa tên công tác, sinh mã, phân loại, gom nhóm và kiểm soát chất lượng.

---

## 1. Chiến lược chuẩn hóa tên công tác (Description Normalization)

### 1.1. Cấu trúc 3 thành phần

Mọi tên công tác chuẩn hóa đều tuân theo format:

```
[TÊN ĐỐI TƯỢNG] - [CHẤT LIỆU/BIẾN THỂ] - [THÔNG SỐ KỸ THUẬT]
```

- Tối đa 2 dấu gạch ngang ` - ` (tạo đúng 3 phần)
- Nếu có nhiều hơn 3 phần, các phần giữa được gộp lại

**Ví dụ:**

| Đầu vào | Đầu ra |
|---------|--------|
| Đổ bê tông dầm sàn M350 thương phẩm | Bê tông dầm sàn - M350 - đá 1x2 |
| Ống HDPE D110 PN16 | Ống cấp nước - HDPE PN16 - D110 |
| Lắp đặt biển báo tam giác A70cm | Biển báo tam giác - A70 - 700x700 |

### 1.2. Quy tắc cắt bỏ động từ

**Động từ LOẠI BỎ** (phụ trợ/chung - không mang tính đặc trưng công việc):

- Cung cấp, Lắp đặt, Thi công, Sản xuất, Gia công, Bơm, Đổ (khi đi kèm từ khác)

**Động từ GIỮ LẠI** (đặc trưng công việc):

- Đào, Đắp, San, Lu, Đầm, Rải, Vận chuyển
- Xây, Trát, Lát, Ốp, Sơn, Quét

### 1.3. Template theo nhóm công tác

#### Đất & Cọc (Earthworks & Piling)

```
[Hành động] [Vật liệu] - [Thiết bị] - [Cấp đất/Grade]
```

- `Đào đất - máy đào 0.8 - đất cấp 3`
- `Đắp đất - K98 - đất mua mới`
- `Ép cọc - D500A - 200 tấn`
- Vị trí (hố móng, nền đường) KHÔNG đưa vào output

#### Bê tông & Cốt thép (Concrete & Rebar)

```
[Bê tông/Cốt thép] [vị trí kết cấu] - [Mác] - [Cốt liệu/Chi tiết]
```

- `Bê tông dầm sàn - M350 - đá 1x2`
- `Bê tông lót móng - M100 - đá 4x6`
- `Cốt thép - CB400V - D10-D18` (cốt thép KHÔNG có vị trí)
- Default: M250 cho bê tông, CB300 cho cốt thép, M100 cho lót móng

#### Hoàn thiện (Finishing)

```
[Động từ] [vị trí] - [Vật liệu chi tiết] - [Kích thước/Mác]
```

- `Lát sàn - gạch granite - 600x600`
- `Trát tường - dày 15mm - M75`
- `Xây tường - gạch đặc 6.5x10.5x22 - M75`
- `Sơn tường - 1 lót 2 phủ`

#### Kết cấu thép & MEP (Steel & MEP)

```
[Tên máy/Ống/Dây] - [Chất liệu] - [Quy cách/Size]
```

- `Cáp điện ngầm - Cu/XLPE/PVC - 4x50mm2`
- `Ống cấp nước - PPR PN10 - D50`
- `MCCB - 3P - 400A 50kA`

#### Hạ tầng đường (Road Infrastructure)

```
[Đối tượng] - [Chất liệu] - [Thông số]
```

- `Biển báo tam giác - A70 - 700x700`
- `Cột đèn - Thép mạ kẽm - H=8m`
- `Vạch sơn liền - Trắng - 150mm`

#### Cảnh quan (Landscaping)

```
[Trồng/Rải] [loại cây/vật liệu] - [kích thước] - [chi tiết]
```

- `Trồng cây Bàng Đài Loan - H3-4m - gốc Ø8-10cm`
- `Rải đất màu - dày 20cm`

### 1.4. Kiến trúc "Sandwich Hybrid"

Pipeline chuẩn hóa 4 bước:

```
1. Pre-processing       → Mở rộng viết tắt, strip động từ, extract location
2. Subtract-Back        → Trích xuất ngược: SPEC → MATERIAL → OBJECT
3. AI Semantic           → Chỉ khi confidence < 70% (threshold = 0.7)
4. Post-validation       → Enforce cấu trúc 3 thành phần, format output
```

**AI Enhancement** chỉ kích hoạt khi:
- Confidence < 80%
- Thiếu verb hoặc material
- Có PC grade cần mapping (PC30 → M100)
- Có gạch nhưng chưa xác định loại (đặc/ống)
- Item thuộc hạ tầng đường
- BTN không có grade
- Item phức tạp (bao gồm, kể cả)

### 1.5. Thứ tự ưu tiên normalizer

Pipeline ưu tiên phân luồng xử lý:

```
Priority 1: TrafficEquipmentNormalizer  → Biển báo, cọc tiêu, vạch sơn, cột đèn
Priority 2: MEPEquipmentNormalizer      → Ống, cáp, thiết bị điện, van, bơm
Priority 3: DescriptionNormalizer       → Mặc định (đất, bê tông, hoàn thiện, chung)
```

### 1.6. Phát hiện Hybrid

Hybrid = Kết hợp động từ xây dựng + specs chuyên ngành khác domain.

| Ví dụ | Loại | Giải thích |
|-------|------|------------|
| `Đào rãnh lắp ống HDPE D110` | HYBRID | Đào (earthwork) + HDPE D110 (MEP) |
| `Thi công cột đèn H=8m` | HYBRID | Thi công + cột đèn H=8m (traffic) |
| `Cáp Cu/XLPE/PVC 4x300mm2` | Pure MEP | Không có động từ xây dựng |
| `Lắp đặt biển báo` | Pure Traffic | Lắp đặt là verb mong đợi cho traffic |

**Động từ earthwork** (chỉ báo hybrid mạnh): đào, đắp, san, lu, đầm, rải

### 1.7. Chống hallucination (AI)

Quy tắc bắt buộc khi sử dụng AI:

1. CHỈ trích xuất thông tin CÓ TRONG bản gốc
2. KHÔNG tự thêm màu sắc, vật liệu, specs nếu không được nêu rõ
3. KHÔNG thêm "theo thiết kế" hoặc thông tin không có trong input
4. Nếu thiếu thông tin → giữ nguyên, KHÔNG bịa thêm

### 1.8. Mở rộng viết tắt

Hệ thống tự động mở rộng viết tắt phổ biến trước khi chuẩn hóa:

| Viết tắt | Mở rộng | Ghi chú |
|----------|---------|---------|
| BT | Bê tông | Concrete |
| BTXM | Bê tông xi măng | Cement concrete |
| BTCT | Bê tông cốt thép | Reinforced concrete |
| BTN | Bê tông nhựa | Asphalt concrete |
| CT | Cốt thép | Reinforcement |
| VK | Ván khuôn | Formwork |
| VKPP | Ván khuôn phủ phim | Film-coated formwork |
| CPĐD | Cấp phối đá dăm | Crushed stone aggregate |
| VĐKT | Vải địa kỹ thuật | Geotextile |
| PCCC | Phòng cháy chữa cháy | Fire protection |
| GCLD | Gia công lắp dựng | Fabrication & erection |
| LTB | Lớp thấm bám | Tack coat |
| BV | Bó vỉa | Curb |
| HG | Hố ga | Manhole |

### 1.9. Quy tắc format

- Viết hoa chữ cái đầu headline (động từ + vật liệu)
- Vị trí thi công viết thường (móng, cột, dầm, sàn)
- Không dùng `[]`, `()`
- Độ dài tối ưu: 40-80 ký tự
- Quy đổi đơn vị kích thước về mm khi phù hợp

---

## 2. Chiến lược sinh mã công tác (Work Code Generation)

### 2.1. Format mã

```
{SEC_PREFIX}-{CATEGORY}-{SUB_CATEGORY}-{SEQUENCE}
```

**Ví dụ:**
- `S01-EARTH-EXCAV-0001` — Đào đất (SEC-01, Earthworks, Excavation)
- `S02-CONC-M200-0001` — Bê tông M200 (SEC-02, Concrete, grade M200)
- `S03-WALL-BRICK-0008` — Tường gạch (SEC-03, Wall, Brick)
- `S04-PIPE-PLUMB-0003` — Ống nước (SEC-04, Pipe, Plumbing)

### 2.2. Bảng SEC Codes

| SEC Code | Prefix | Mô tả | Ví dụ |
|----------|--------|--------|-------|
| SEC-00 | S00 | Chung/Sơ bộ | Chi phí chung, biện pháp thi công |
| SEC-01 | S01 | Phần ngầm (Substructure) | Đào đất, cọc, móng |
| SEC-02 | S02 | Phần thân (Superstructure) | Bê tông, cốt thép, ván khuôn |
| SEC-03 | S03 | Kiến trúc (Architecture) | Xây, trát, sơn, lát, cửa |
| SEC-04 | S04 | MEP | Điện, nước, HVAC, PCCC |
| SEC-05 | S05 | Cảnh quan & Hạ tầng (Landscape) | Đường, vỉa hè, cây xanh |

**SEC Level 2:**

| SEC Code | Nhóm con |
|----------|----------|
| SEC-01-01 | Công tác đất (Earthworks) |
| SEC-01-02 | Cọc (Piling) |
| SEC-01-03 | Móng (Foundation) |
| SEC-02-01 → 06 | Bê tông, Sàn, Dầm, Cột, Tường, Cốt thép |
| SEC-03-01 → 06 | Xây, Trát, Sơn, Lát, Trần, Cửa |
| SEC-04-01 | Điện (Electrical) |
| SEC-04-02 | Nước (Plumbing) |
| SEC-04-03 | HVAC |
| SEC-04-04 | PCCC (Fire Protection) |
| SEC-05-01 → 03 | Đường, Vỉa hè, Cây xanh |

### 2.3. Bảng từ khóa → Category Code

**Earthworks (SEC-01):**

| Từ khóa | Code |
|---------|------|
| đào | EARTH |
| đắp | FILL |
| san | LEVEL |
| nền | GROUND |
| cọc | PILE |
| khoan | DRILL |
| móng | FOUND |

**Concrete & Structure (SEC-02):**

| Từ khóa | Code |
|---------|------|
| bê tông / betong | CONC |
| cốt thép | REBAR |
| sàn | SLAB |
| dầm | BEAM |
| cột | COL |
| tường | WALL |
| kết cấu | STRUC |

**Architecture (SEC-03):**

| Từ khóa | Code |
|---------|------|
| gạch | BRICK |
| vữa | MORT |
| trát | PLAST |
| sơn | PAINT |
| lát | TILE |
| trần | CEIL |
| mái | ROOF |
| cửa | DOOR |
| cửa sổ | WIND |

**MEP (SEC-04):**

| Từ khóa | Code |
|---------|------|
| điện | ELEC |
| nước | WATER |
| thang máy | ELEV |
| thông gió | VENT |
| điều hòa | HVAC |
| pccc / cháy | FIRE |
| ống / hdpe / pvc / ppr | PIPE |
| van | VALVE |
| côn / cút / tê / bích / khớp nối | FITTING |
| mccb / mcb / aptomat | BREAKER |
| tủ điện | PANEL |
| cáp | CABLE (cap) |
| đồng hồ | METER |
| bơm | PUMP |

**Landscape (SEC-05):**

| Từ khóa | Code |
|---------|------|
| cảnh quan | LAND |
| đường | ROAD |
| vỉa | PAVE |
| cây | TREE |
| hàng rào | FENCE |
| cổng | GATE |

### 2.4. Tích hợp grade vật liệu

Khi `include_grade=True`, mác vật liệu được đưa vào work code thay cho sub-category:

| Pattern | Ví dụ | Ghi chú |
|---------|-------|---------|
| M + số | M200, M250, M300 | Mác bê tông |
| B + số → M | B25 → M250 | Chuyển đổi B-grade sang M-grade |
| CB + số | CB300, CB400 | Mác thép cốt thép |
| PN + số | PN10, PN16 | Áp suất ống |
| K + số | K95, K98 | Độ đầm chặt |
| SS + số | SS400 | Thép kết cấu |
| SDR + số | SDR11, SDR17 | Tỷ số đường kính/bề dày ống |

### 2.5. Đánh số tự động

- Sequence 4 chữ số tự tăng theo category: `0001`, `0002`, ...
- Cache in-memory trong batch để tránh trùng lặp
- Query database để lấy max sequence hiện tại khi bắt đầu

---

## 3. Chiến lược phân loại nhóm công tác (Work Category Classification)

### 3.1. Bảy nhóm công tác

| Nhóm | Enum | Mô tả |
|------|------|-------|
| Đất & Cọc | EARTHWORKS_PILING | Đào, đắp, san, ép cọc, khoan cọc |
| Bê tông & Cốt thép | CONCRETE_REBAR | Đổ bê tông, cốt thép, ván khuôn |
| Hoàn thiện | FINISHING | Xây, trát, lát, sơn, ốp |
| Thép & MEP | STEEL_MEP | Kết cấu thép, điện, nước, HVAC |
| Hạ tầng đường | ROAD_INFRASTRUCTURE | BTN, biển báo, vạch sơn, lan can |
| Cảnh quan | LANDSCAPING | Cây xanh, cỏ, tiểu cảnh, đất màu |
| Chung | GENERAL | Không thuộc nhóm cụ thể |

### 3.2. Mapping nhóm → SEC Code

| WorkCategory | SEC Code |
|-------------|----------|
| EARTHWORKS_PILING | SEC-01 |
| CONCRETE_REBAR | SEC-02 |
| FINISHING | SEC-03 |
| STEEL_MEP | SEC-04 |
| ROAD_INFRASTRUCTURE | SEC-05 |
| LANDSCAPING | SEC-05 |
| GENERAL | SEC-00 |

### 3.3. Phân loại SEC đa cấp

Hệ thống phân loại SEC code theo 3 cơ chế, ưu tiên từ trên xuống:

#### a) ML-based (Sentence Transformers)

- Sử dụng Vietnamese sentence transformer model
- Encode SEC codes thành embeddings từ name + description + keywords
- So sánh cosine similarity giữa description input và SEC embeddings
- Kết quả trả về top-k SEC codes với confidence score (0-100%)
- Threshold mặc định từ `settings.CLASSIFICATION_THRESHOLD`

#### b) Rule-based fallback (Keyword matching)

- Nếu ML model chưa sẵn sàng hoặc confidence thấp
- Đối sánh keyword từ database SEC codes
- Score dựa trên: độ dài match / độ dài description * 100
- Bonus 20 điểm cho word boundary match
- Capped 95% (rule-based không bao giờ 100% confident)

#### c) Hardcoded MEP sub-categories

Regex patterns cho 4 nhóm MEP, chạy **sau ML** và **trước WorkCategory fallback**:

| SEC Code | Nhóm | Từ khóa chính |
|----------|------|---------------|
| SEC-04-01 | Điện | mccb, mcb, contactor, aptomat, cầu chì, đèn báo, tủ điện, thanh cái, cáp cu, xlpe, cáp điện, dây điện, cầu dao, rơ le, biến áp |
| SEC-04-02 | Nước | ống hdpe/pvc/ppr/thép/nhựa/gang/inox, van cổng/bướm/bi/một chiều, côn thu, cút, bích, khớp nối, đồng hồ nước, bơm nước/chìm |
| SEC-04-03 | HVAC | điều hòa, thông gió, ahu, fcu, ống gió, dàn lạnh/nóng, máy lạnh, chiller |
| SEC-04-04 | PCCC | pccc, báo cháy, sprinkler, bình chữa cháy, chữa cháy, đầu phun, tủ cứu hỏa |

### 3.4. Mô hình 3 lớp ưu tiên (Priority Objects)

Giải quyết vấn đề "Identity Theft" khi flat keyword matching nhận sai đối tượng:

| Lớp | Tên | Quy tắc | Ví dụ |
|-----|-----|---------|-------|
| Priority 1 | Biện pháp / Phương pháp | Match → DỪNG ngay, đây là Object chính | Ván khuôn, Vận chuyển, Đào phá dỡ, Tưới nhựa, Xây, Trát (~130 entries) |
| Priority 2 | Cấu kiện đặc thù | Match → Object = Cấu kiện, KHÔNG phải vật liệu | Bó vỉa, Tấm đan, Hố ga, MCCB, Camera, Van, Bơm, Cốt thép (~950+ entries) |
| Priority 3 | Vật liệu chung | Chỉ match khi KHÔNG có P1/P2 | Bê tông, Đá, Cát, Cáp điện, Ống nhựa (~90 entries) |

### 3.5. Từ khóa phân loại cho từng nhóm

**LANDSCAPING** (ưu tiên cao nhất):
cây bàng, cây phượng, cây sấu, cây xanh, trồng cây, trồng cỏ, thảm cỏ, bồn hoa, tiểu cảnh, chăm sóc cây

**ROAD_INFRASTRUCTURE:**
biển báo, cọc tiêu, cọc km, bản quan trắc, vạch sơn, lan can, hộ lan, tôn sóng, rải thảm, btn c, lớp thấm bám, nhựa pha dầu

**EARTHWORKS_PILING:**
đào, đắp, san, ép, khoan, đóng, cọc, đất, hố móng, nền, đầm chặt, k95, k98, cpđd, cấp phối, đá dăm

**CONCRETE_REBAR:**
bê tông, betong, đổ, đúc, cốt thép, thép, ván khuôn, gia công, lắp dựng

**FINISHING:**
xây, trát, láng, sơn, ốp, lát, gạch, vữa, tường, sàn, trần

**STEEL_MEP:**
lắp đặt, thi công, ống, dây, cáp, thiết bị, hệ thống, điện, nước, thông gió

---

## 4. Chiến lược gom nhóm và xây dựng Master Database

### 4.1. Pipeline 3 bước

```
Step 1 — AGGREGATION
    Scan line_items grouped by (description, unit)
    Đếm tần suất xuất hiện across files
    Output: List[AggregatedItem] sorted by frequency desc

Step 2 — STANDARDIZATION
    Normalize all descriptions (qua Orchestrator)
    Cluster similar items (fuzzy matching)
    Bầu canonical name per cluster
    Áp dụng Pareto 80/20
    Output: List[StandardizedItem] với canonical + synonyms

Step 3 — CODING & TAGGING
    Classify SEC codes (ML → Rule → WorkCategory fallback)
    Extract specs (SpecExtractor)
    Generate work codes (WorkCodeGenerator)
    Validate qua Gatekeeper
    Persist to: master / pending / quarantine
```

### 4.2. Clustering

- **Thuật toán**: Union-Find với pairwise fuzzy matching
- **Thư viện**: RapidFuzz (fallback: difflib SequenceMatcher)
- **Threshold**: `≥ 0.85` (85% similarity)
- **Điều kiện**: Chỉ cluster items có cùng đơn vị (unit)
- **Dataset lớn** (> 5000 items): Fallback sang exact-normalized grouping để tránh O(n²)

### 4.3. Bầu canonical

Chiến lược chọn tên chuẩn cho mỗi cluster:

1. **Sort** cluster theo: frequency (desc) → description length (desc)
2. **Chọn** normalized description đầu tiên KHÔNG bị degenerate
3. **Degenerate** = quá ngắn (< 5 ký tự) / từ lặp ("ống ống") / quá generic ("cái", "bộ")
4. **Fallback**: Nếu tất cả normalized đều degenerate → dùng raw description có frequency cao nhất
5. **Synonyms**: TẤT CẢ raw descriptions (kể cả canonical gốc) đều thành synonym

### 4.4. Pareto 80/20

- Items sorted theo frequency descending
- Đánh dấu `is_pareto_top = True` cho các item thuộc top 80% tần suất tích lũy
- Config `include_only_pareto = True` → chỉ xử lý Step 3 cho Pareto items

### 4.5. Matching thresholds

| Mức | Threshold | Hành động |
|-----|-----------|-----------|
| Exact Match | ≥ 95% | Tự động gán work code (auto-assign) |
| Fuzzy Match | 80% - 95% | Cần review thủ công |
| No Match | < 80% | Tạo item mới trong master |

---

## 5. Chiến lược kiểm soát chất lượng (Gatekeeper)

### 5.1. Scoring & Ngưỡng

| Điểm | Status | Hành động |
|------|--------|-----------|
| ≥ 75 | APPROVED | Tự động thêm vào Master DB |
| 50 - 74 | PENDING_REVIEW | Đưa vào staging area chờ review |
| < 50 | REJECTED | Quarantine / loại bỏ |

Mỗi quality indicator đáp ứng được cộng 25 điểm (tối đa 100).

### 5.2. Quality Indicators

| Indicator | Regex Pattern | Mô tả |
|-----------|---------------|-------|
| `has_verb` | Đào, Đắp, Đổ, Xây, Trát, Lắp, Lát, Sơn, Thi công, Gia công, Vận chuyển, Rải, Bê tông... | Có động từ hành động |
| `has_material` | bê tông, gạch, thép, đất, đá, ống, cáp, sơn, pvc, hdpe, CPĐD, BTN, biển báo, ván khuôn... | Có từ khóa vật liệu |
| `has_specs` | M\d+, D\d+, K\d+, \d+x\d+, \d+mm, PN\d+, CB\d+, loại I/II... | Có thông số kỹ thuật |
| `has_location` | móng, cột, dầm, sàn, tường, mái, nền, hố, mương, tầng, vỉa hè, mặt đường... | Có ngữ cảnh vị trí |

### 5.3. Category-specific rules & Defaults

| Category | Default Grade | Bonus | Material optional | Specs optional | Min indicators |
|----------|--------------|-------|-------------------|----------------|----------------|
| Earthworks | K95 | +25 | Yes | Yes | 1 |
| Concrete | M250 | 0 | No | No | 2 |
| Steel/MEP | - | +25 | No | Yes | 1 |
| Road | - | +25 | Yes | Yes | 1 |
| Finishing | - | +25 | No | Yes | 1 |
| Landscaping | - | +25 | Yes | Yes | 1 |
| General | - | +25 | Yes | Yes | 1 |

**Default specs bổ sung cho Concrete**: `đá 1x2`

### 5.4. Bộ lọc bổ sung

**Forbidden patterns** (reject ngay lập tức):
- Chỉ dấu câu, chỉ số, quá ngắn vô nghĩa (`?!`, `123`, `ab`)
- Garbage patterns: `test`, `xxx`, `abc`, `n/a`
- Chỉ dấu gạch, chỉ dấu chấm lửng

**Material-only items** (approve với score 75):
- Nhận dạng ~180+ pattern vật tư thuần (ống, cáp, van, gạch, thép, đèn, tủ điện, v.v.)
- Auto-approve khi match vì đây là vật tư hợp lệ, không cần verb/location

**Device code detection** (skip):
- Mã thiết bị dạng `TĐ-1-II-TBA`, `1.2.3`, `I.1` → bỏ qua, không phải mô tả công tác

---

## 6. Bảng tham chiếu

### 6.1. Mapping SEC Codes đầy đủ

| SEC Code | Prefix | Tên tiếng Việt | Sub-categories |
|----------|--------|----------------|----------------|
| SEC-00 | S00 | Phần chung | - |
| SEC-01 | S01 | Phần ngầm | 01: Đất, 02: Cọc, 03: Móng |
| SEC-02 | S02 | Phần thân | 01-06: BT, Sàn, Dầm, Cột, Tường, CT |
| SEC-03 | S03 | Kiến trúc | 01-06: Xây, Trát, Sơn, Lát, Trần, Cửa |
| SEC-04 | S04 | MEP | 01: Điện, 02: Nước, 03: HVAC, 04: PCCC |
| SEC-05 | S05 | Cảnh quan | 01: Đường, 02: Vỉa hè, 03: Cây xanh |

### 6.2. Bảng từ khóa MEP

| Nhóm | SEC Code | Từ khóa chính |
|------|----------|---------------|
| Điện | SEC-04-01 | mccb, mcb, contactor, aptomat, cầu chì, đèn báo, tủ điện, thanh cái, cáp điện, dây điện, cầu dao, rơ le, biến áp, xlpe |
| Nước | SEC-04-02 | ống hdpe/pvc/ppr/thép/nhựa/gang/inox, van cổng/bướm/bi/một chiều/cầu, côn thu, cút, tê, bích, khớp nối, đồng hồ nước, bơm nước/chìm |
| HVAC | SEC-04-03 | điều hòa, thông gió, ahu, fcu, ống gió, dàn lạnh/nóng, máy lạnh, chiller, cooling |
| PCCC | SEC-04-04 | pccc, báo cháy, sprinkler, bình chữa cháy, đầu phun, tủ cứu hỏa |

### 6.3. Bảng Grade Patterns

| Prefix | Pattern | Ví dụ | Áp dụng cho |
|--------|---------|-------|-------------|
| M | M + 2-3 số | M200, M300 | Mác bê tông |
| B | B + 2 số | B15, B25 | Mác BT (chuyển sang M) |
| CB | CB + 3 số | CB300, CB400V | Mác thép cốt thép |
| PN | PN + 1-2 số | PN10, PN16 | Áp suất ống |
| K | K9 + 1 số | K95, K98 | Độ đầm chặt |
| C | C + số/số | C16/20 | Mác BT Eurocode |
| SDR | SDR + 1-2 số | SDR11 | Tỷ số ống |
| CT | CT + 1 số | CT3, CT5 | Mác thép |
| SS | SS + 3 số | SS400 | Thép kết cấu |
| PC | PC + 2 số | PC30, PC40 | Mác xi măng |
| BTN C | BTN C + số | BTN C12.5 | Bê tông nhựa |
| D | D + 1-2 số | D10, D16 | Đường kính thép/ống |

### 6.4. Bảng file nguồn tương ứng từng chiến lược

| Chiến lược | File nguồn | Mô tả |
|------------|-----------|-------|
| Chuẩn hóa tên (Description) | `app/services/description_normalizer.py` | Normalizer chính, template theo nhóm |
| Pipeline Sandwich | `app/services/normalization_orchestrator.py` | Orchestrator 4 bước, hybrid detection |
| AI Normalizer | `app/services/ai_normalizer.py` | LLM enhancement, multi-pass analysis |
| Mở rộng viết tắt | `app/services/abbreviation_expander.py` | Bảng viết tắt → mở rộng |
| Subtract-Back | `app/services/subtract_back_extractor.py` | Trích xuất ngược SPEC→MAT→OBJ |
| Traffic Normalizer | `app/services/traffic_equipment_normalizer.py` | Biển báo, cọc tiêu, vạch sơn |
| MEP Normalizer | `app/services/mep_equipment_normalizer.py` | Ống, cáp, thiết bị điện |
| Sinh mã công tác | `app/services/work_code_generator.py` | Format SEC-CATEGORY-SEQ |
| ML Classifier | `app/services/classifier_service.py` | Sentence transformer + cosine similarity |
| Rule-based Classifier | `app/services/rule_based_classifier.py` | Keyword matching fallback |
| Trích xuất thông số | `app/services/spec_extractor.py` | Category, material, grade, dimension |
| Master Builder | `app/services/master_database_builder.py` | Pipeline 3 bước: Aggregate → Standardize → Code |
| Quality Gate | `app/services/master_data_gatekeeper.py` | Scoring, thresholds, defaults |
| Từ điển ưu tiên | `app/services/dictionaries/priority_objects.py` | Mô hình 3 lớp Priority |
| Từ điển tổng hợp | `app/services/dictionaries/master_resource.py` | 200+ object configs, extractors |
