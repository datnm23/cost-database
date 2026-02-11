# CHIẾN LƯỢC CHUẨN HÓA DỮ LIỆU COST DATABASE

**Phiên bản:** 4.0
**Cập nhật:** 11/02/2026
**Mục đích:** Tài liệu hóa toàn bộ các chiến lược chuẩn hóa tên công tác, mã công tác, và nhóm công tác đang áp dụng trong hệ thống.

---

## MỤC LỤC

1. [Chuẩn hóa tên công tác (Description Normalizer)](#1-chuẩn-hóa-tên-công-tác)
2. [Chuẩn hóa thiết bị MEP (MEP Equipment Normalizer)](#2-chuẩn-hóa-thiết-bị-mep)
3. [Sinh mã công tác Legacy (Work Code Generator)](#3-sinh-mã-công-tác-legacy)
4. [Sinh mã công tác V4 (V4 Code Generator — 3-Level)](#4-sinh-mã-công-tác-v4)
   - 4.8 [Reference Code vs Instance Code](#48-reference-code-vs-instance-code)
   - 4.9 [Phát hiện loại item (Item Type Detection)](#49-phát-hiện-loại-item-item-type-detection)
5. [Ánh xạ SEC Code V4 (SEC Code V4 Mapper)](#5-ánh-xạ-sec-code-v4)
6. [Kiểm soát chất lượng Master Data (Master Data Gatekeeper)](#6-kiểm-soát-chất-lượng-master-data)
7. [Pipeline xây dựng Master Database (Master Database Builder)](#7-pipeline-xây-dựng-master-database)
8. [Vòng đời Specification (Spec Lifecycle Service)](#8-vòng-đời-specification)
9. [Mô hình dữ liệu (Models)](#9-mô-hình-dữ-liệu)
10. [Hệ thống mã SEC v4.1 (3-Level Code + Attribute Model)](#10-hệ-thống-mã-sec-v41)

---

## 1. Chuẩn hóa tên công tác

**Nguồn:** `backend/app/services/description_normalizer.py`

### 1.1 Phương pháp: Natural Syntax (Phương án 5)

Chuẩn hóa description theo cú pháp tự nhiên tiếng Việt với 6 quy tắc cốt lõi:

| # | Quy tắc | Ví dụ |
|:---:|:---|:---|
| 1 | Cụm Động từ & Vật liệu: Viết hoa chữ cái đầu | `Đào đất`, `Bê tông` |
| 2 | Vị trí Thi công: Viết thường toàn bộ | `hố móng`, `dầm sàn` |
| 3 | Thông số Kỹ thuật Chính: Sau dấu `-` đầu tiên | `M350`, `D16` |
| 4 | Chi tiết Bổ sung: Sau dấu `-` thứ hai | `thương phẩm`, `đá 1x2` |
| 5 | Hạn chế ký tự đặc biệt: Không dùng `[]`, `()` | |
| 6 | Độ dài tối ưu: 40–80 ký tự | |

### 1.2 Cấu trúc đầu ra: 3 thành phần

```
[TÊN ĐỐI TƯỢNG] - [CHẤT LIỆU/BIẾN THỂ] - [THÔNG SỐ KỸ THUẬT]
```

Tối đa 2 dấu gạch ngang, tối đa 3 thành phần. Nếu đầu vào có nhiều hơn 3 phần, các phần giữa được ghép lại.

### 1.3 Phân loại nhóm công tác (7 nhóm)

| Nhóm | Hằng số | Template |
|:---|:---|:---|
| Đất & Cọc | `earthworks_piling` | `[Hành động] [Vật liệu] - [Thiết bị] - [Cấp đất]` |
| Bê tông & Cốt thép | `concrete_rebar` | `[Bê tông/Cốt thép] [vị trí] - [Mác] - [đá 1x2]` |
| Hoàn thiện | `finishing` | `[Động từ] [vị trí] - [Vật liệu chi tiết] - [Kích thước/Mác]` |
| Kết cấu thép & MEP | `steel_mep` | `[Tên thiết bị/Ống/Dây] - [Chất liệu] - [Quy cách]` |
| Hạ tầng đường | `road_infrastructure` | `[Đối tượng] - [Chất liệu] - [Thông số]` |
| Cây xanh, cảnh quan | `landscaping` | `[Trồng/Rải] [loại cây/vật liệu] - [kích thước] - [chi tiết]` |
| Chung | `general` | Fallback noun-first format |

### 1.4 Xử lý động từ

**Động từ LOẠI BỎ** (phụ trợ/chung): `Cung cấp`, `Lắp đặt`, `Thi công`, `Sản xuất`, `Gia công`, `Bơm`, `Đổ`

**Động từ GIỮ LẠI** (đặc trưng công việc): `Đào`, `Đắp`, `San`, `Lu`, `Đầm`, `Rải`, `Vận chuyển`, `Xây`, `Trát`, `Lát`, `Ốp`, `Sơn`, `Quét`

### 1.5 Trích xuất mác vật liệu

| Pattern | Ví dụ | Kết quả |
|:---|:---|:---|
| `M` + số | `M200`, `M350` | `M200`, `M350` |
| `mác` + số | `mác 250` | `M250` |
| `B` + số (chuyển đổi) | `B25` → `M250` | Bảng chuyển đổi B→M |
| `CB` + số | `CB400V` | `CB400V` |
| `D` + số (đường kính thép) | `D16` | `D16` |
| `PC` + số (xi măng) | `PC30` + `lót móng` | `M100` |
| `SS` + số (thép kết cấu) | `SS400` | `SS400` |
| `PN` + số (áp suất ống) | `PN16` | `PN16` |
| `K` + số (độ đầm chặt) | `K95` | `K95` |
| `BTN C` + số (bê tông nhựa) | `BTN C12.5` | `BTN C12.5` |

### 1.6 Bảng chuyển đổi B-grade → M-grade

| B-grade | M-grade |
|:---:|:---:|
| B15 | M200 |
| B20 | M250 |
| B25 | M300 |
| B27.5 | M350 |
| B30 | M400 |
| B35 | M450 |
| B40 | M500 |
| B45 | M600 |
| B50 | M700 |

### 1.7 Quy đổi đơn vị về mm

Tất cả kích thước được quy đổi về mm theo Standard Naming Strategy:
- `cm` → nhân 10 → `mm`
- `m` → nhân 1000 → `mm`

### 1.8 Ví dụ chuẩn hóa

| Đầu vào | Đầu ra |
|:---|:---|
| `Đào đất hố móng bằng máy 1.25m3 đất cấp 3` | `Đào đất - máy đào 1.25m3 - đất cấp 3` |
| `Đổ bê tông dầm sàn M350 thương phẩm` | `Bê tông dầm sàn - M350 - đá 1x2` |
| `Lát gạch sàn phòng khách 600x600 Granite` | `Lát sàn - gạch granite - 600x600` |
| `Xây tường gạch đặc 6.5x10.5x22 vữa M75 dày 220` | `Xây tường - gạch đặc 6.5x10.5x22 - M75 - dày 220` |
| `Gia công lắp dựng cốt thép móng D<10 CB300` | `Cốt thép - D<10 - CB300` |

---

## 2. Chuẩn hóa thiết bị MEP

**Nguồn:** `backend/app/services/mep_equipment_normalizer.py`

### 2.1 Tổng quan

MEP Equipment Normalizer xử lý chuẩn hóa riêng cho thiết bị Cơ-Điện-Nước theo Standard Naming Strategy: `[TÊN ĐỐI TƯỢNG] - [CHẤT LIỆU] - [THÔNG SỐ]`. Động từ phụ trợ (`Cung cấp`, `Lắp đặt`, `Thi công`) được loại bỏ.

### 2.2 Các nhóm pattern nhận diện

#### 2.2.1 Cáp điện (Cable)

| Loại | Pattern | Format chuẩn |
|:---|:---|:---|
| Cáp XLPE | `Cáp Cu/XLPE/PVC 4x300mm2` | `Cáp Cu/XLPE/PVC - 4x300mm2` |
| Cáp XLPE | `Cáp Cu/MICA/XLPE/PVC/FR-PVC 4x300mm2` | `Cáp Cu/MICA/XLPE/PVC/FR-PVC - 4x300mm2` |
| Cáp PVC | `Cáp đồng bọc PVC 1x6mm2` | `Cáp Cu/PVC - 1x6mm2` |
| Dây điện | `Dây điện 1x2.5mm2` | `Dây điện Cu - 1x2.5mm2` |
| Cáp trung thế | `Cáp ngầm trung thế 3x50` | `Cáp ngầm trung thế - 3x50mm2` |

#### 2.2.2 Ống (Pipe)

| Loại | Pattern | Format chuẩn |
|:---|:---|:---|
| HDPE | `Ống HDPE D110 PN16` | `Ống HDPE - D110 - PN16` |
| PVC | `Ống uPVC D90` | `Ống PVC - D90` |
| PPR | `Ống PPR D25 PN10` | `Ống PPR - D25 - PN10` |
| Thép mạ kẽm | `Ống thép mạ kẽm DN50` | `Ống thép mạ kẽm - DN50` |
| Thép đen | `Ống thép đen DN80` | `Ống thép đen - DN80` |
| TTK | `Ống TTK DN25` | `Ống TTK - DN25` |
| Ống luồn dây | `Ống luồn dây D20` | `Ống luồn dây - D20` |

#### 2.2.3 Van (Valve)

| Loại | Format chuẩn |
|:---|:---|
| Van cổng | `Van cổng - DN{diameter}` |
| Van bướm | `Van bướm - DN{diameter}` |
| Van bi | `Van bi - DN{diameter}` |
| Van một chiều | `Van một chiều - DN{diameter}` |

#### 2.2.4 Phụ kiện ống (Fitting)

| Loại | Format chuẩn |
|:---|:---|
| Côn thu | `Côn thu - {material} - D{d1}/D{d2}` |
| Cút | `Cút - {material} - DN{diameter}` |
| Tê | `Tê - {material} - DN{diameter}` |
| Bích | `Bích - {material} - DN{diameter}` |
| Khớp nối mềm | `Khớp nối mềm - {material} - DN{diameter}` |
| Măng sông | `Măng sông - {material} - DN{diameter}` |

#### 2.2.5 Thiết bị đóng cắt (Breaker)

| Loại | Format chuẩn |
|:---|:---|
| MCCB | `MCCB - {poles}P - {amps}A {ka}kA` |
| MCB | `MCB - {poles}P - {amps}A` |
| RCCB/RCBO/ELCB | `{type} - {poles}P - {amps}A` |

#### 2.2.6 Phụ kiện điện (Electrical Accessory)

| Loại | Format chuẩn |
|:---|:---|
| Contactor | `Contactor - {poles}P - {amps}A` |
| Aptomat | `Aptomat - {poles}P - {amps}A` |
| Cầu chì | `Cầu chì - {amps}A` |
| Thanh cái đồng | `Thanh cái đồng - {amps}A` |
| Đèn báo pha | `Đèn báo pha` |
| Timer | `Timer hẹn giờ - {amps}A` |
| Rơ le trung gian | `Rơ le trung gian - {amps}A` |

#### 2.2.7 Thiết bị đo (Instrument)

| Loại | Format chuẩn |
|:---|:---|
| Đồng hồ nước | `Đồng hồ nước - DN{diameter}` |
| Đồng hồ đo áp suất | `Đồng hồ đo áp suất - {bar}bar` |
| Đồng hồ lưu lượng | `Đồng hồ lưu lượng - DN{diameter}` |
| Nhiệt kế | `Nhiệt kế` |

#### 2.2.8 Bơm (Pump)

| Loại | Format chuẩn |
|:---|:---|
| Bơm chìm | `Bơm chìm - {power}` |
| Bơm ly tâm | `Bơm ly tâm - {power}` |
| Bơm tăng áp | `Bơm tăng áp - {power}` |
| Bơm chữa cháy | `Bơm chữa cháy - {power}` |

#### 2.2.9 HVAC

| Loại | Format chuẩn |
|:---|:---|
| AHU | `AHU - {capacity}` |
| FCU | `FCU - {capacity}` |
| Điều hòa | `Điều hòa - {capacity}` |
| Dàn lạnh | `Dàn lạnh - {capacity}` |
| Dàn nóng | `Dàn nóng - {capacity}` |
| Ống gió | `Ống gió - {W}x{H}` |
| Quạt thông gió | `Quạt thông gió - {capacity}` |

#### 2.2.10 PCCC (Fire Protection)

| Loại | Format chuẩn |
|:---|:---|
| Sprinkler | `Sprinkler - DN{diameter}` |
| Đầu báo cháy (khói/nhiệt) | `Đầu báo cháy khói` / `Đầu báo cháy nhiệt` |
| Bình chữa cháy | `Bình chữa cháy - {capacity}{unit}` |
| Vòi chữa cháy | `Vòi chữa cháy - DN{diameter}` |
| Tủ chữa cháy | `Tủ chữa cháy` |

#### 2.2.11 Đèn chiếu sáng (Lighting)

| Loại | Format chuẩn |
|:---|:---|
| Đèn chiếu sáng LED | `Đèn chiếu sáng LED - {wattage}W` |
| Đèn tín hiệu báo pha | `Đèn tín hiệu báo pha` |
| Đèn LED panel | `Đèn LED panel - {wattage}W` |

---

## 3. Sinh mã công tác Legacy

**Nguồn:** `backend/app/services/work_code_generator.py`

### 3.1 Format mã

```
{SEC_PREFIX}-{CATEGORY}-{SEQUENCE}
```

Ví dụ: `S01-EARTH-EXCAV-0001`, `S02-CONC-M200-0001`

### 3.2 Ánh xạ SEC Code → Prefix

| SEC Code | Prefix | Mô tả |
|:---|:---:|:---|
| SEC-00 | S00 | Preliminaries |
| SEC-01 (01-01, 01-02, 01-03) | S01 | Phần ngầm (Đất, Cọc, Móng) |
| SEC-02 (02-01 → 02-06) | S02 | Kết cấu (Bê tông, Sàn, Dầm, Cột, Tường, Cốt thép) |
| SEC-03 (03-01 → 03-06) | S03 | Kiến trúc (Xây, Trát, Sơn, Lát, Trần, Cửa) |
| SEC-04 (04-01 → 04-04) | S04 | MEP (Điện, Nước, HVAC, PCCC) |
| SEC-05 (05-01 → 05-03) | S05 | Ngoại thất (Đường, Vỉa, Cây xanh) |

### 3.3 Từ khóa → Category

| Từ khóa | Category | Từ khóa | Category |
|:---|:---:|:---|:---:|
| đào | EARTH | gạch | BRICK |
| đắp | FILL | trát | PLAST |
| cọc | PILE | sơn | PAINT |
| bê tông | CONC | lát | TILE |
| cốt thép | REBAR | ống | PIPE |
| dầm | BEAM | van | VALVE |
| cột | COL | điện | ELEC |
| tường | WALL | bơm | PUMP |

### 3.4 Từ khóa → Sub-category

| Từ khóa | Sub | Từ khóa | Sub |
|:---|:---:|:---|:---:|
| đào đất | EXCAV | van cổng | GATE |
| đắp đất | BACKFILL | van bướm | BFLY |
| cọc khoan | DPILE | côn thu | REDU |
| bê tông | CONC | cút thép | ELBOW |
| ván khuôn | FORM | bích thép | FLANG |
| lát gạch | TILE | khớp nối | JOINT |

### 3.5 Trích xuất mác bê tông

Hỗ trợ 5 pattern: `M+số`, `mác+số`, `grade+số`, `cấp+số`, `B+số` (chuyển đổi).

### 3.6 Sequence number

Sequence được quản lý theo nhóm `{SEC_PREFIX}-{CATEGORY}`, tự tăng, có cache in-memory để tránh trùng lặp trong cùng batch.

---

## 4. Sinh mã công tác V4

**Nguồn:** `backend/app/services/v4_code_generator.py`

### 4.1 Format mã 3 cấp

```
[PREFIX].[GROUP].[TYPE]
  L0       L1      L2
```

Ví dụ: `A.CONC.STR` — Activity, Concrete, Structural

> **Thay đổi từ 5-level sang 3-level:**
> - Discipline (cũ L1: CV, AR, EL...) → attribute `discipline` trên master_work_items
> - Location (cũ L4: COL, FND, GEN...) → attribute `location` trên master_work_items
> - GROUP codes mở rộng: `CON`→`CONC`, `RBR`→`RBAR`, `PIP`→`PIPE`, `CBL`→`CABL`
> - TYPE codes đổi từ action-based sang sub-category: `POUR`→`STR`, `FABR`→`DFM`

> **Nguyên tắc Same Suffix:** Cả 4 bảng A, M, L, E dùng chung GROUP.TYPE:
> `A.CONC.STR`, `M.CONC.STR`, `L.CONC.STR`, `E.CONC.STR`

### 4.2 L0: Prefix (Table Type)

| Prefix | Bảng | Mô tả |
|:---:|:---|:---|
| A | Activity | Hành động thi công |
| M | Material | Vật tư vật lý |
| L | Labour | Nhân công |
| E | Equipment | Máy móc thiết bị |

### 4.3 Discipline (attribute — không nằm trong mã)

Discipline nay là attribute trên `master_work_items`, ánh xạ từ SEC code:

| SEC Code | Discipline | Mô tả |
|:---|:---:|:---|
| SEC-00 | PM | Preliminaries |
| SEC-01, SEC-02 | CV | Civil (Đất, Kết cấu) |
| SEC-03 | AR | Architecture (Hoàn thiện) |
| SEC-04-01 | EL | Electrical |
| SEC-04-02 | PL | Plumbing |
| SEC-04-03 | ME | Mechanical/HVAC |
| SEC-04-04 | FP | Fire Protection |
| SEC-05 | EX | External Works |
| SEC-05-03 | LA | Landscape |

### 4.4 L1: GROUP (Nhóm công tác)

| Từ khóa | GROUP | Từ khóa | GROUP |
|:---|:---:|:---|:---:|
| bê tông | CONC | cáp | CABL |
| cốt thép | RBAR | đèn | LITE |
| ván khuôn | FWRK | tủ điện | PANL |
| đào đất | EXCV | điều hòa | HVAC |
| đắp đất | FILL | pccc | DETC |
| cọc | PILE | đường | ROAD |
| ống | PIPE | cây | PLNT |
| gạch/xây | WALL | van | FITG |
| sơn | PANT | bơm | PUMP |
| trát | WALL | chống thấm | WTPF |
| lát/ốp | FLOR | hàng rào | FNCE |

### 4.5 L2: TYPE theo bảng A/M/L/E

> **QUAN TRỌNG:** TYPE là sub-category — KHÔNG chứa grade/spec (M300, CB40, XLPE).
> Grade được lưu riêng trong `spec_grade`, `spec_material` trên `master_work_items`.

**Bảng A (Activity)** — Sub-category:

| Từ khóa | TYPE | Từ khóa | TYPE |
|:---|:---:|:---|:---:|
| bê tông kết cấu | STR | bê tông lót | LEA |
| bê tông móng | FND | ống/lắp đặt | GEN |
| cốt thép vằn | DFM | chống thấm | GEN |
| cốt thép cuộn | RND | cọc/khoan | BOR |
| ván khuôn | GEN | cáp/dây | GEN |
| đào máy | MCH | đường | GEN |
| đào thủ công | MAN | cây | GEN |
| xây | GEN | lát/ốp | GEN |

**Bảng M (Material)** — Sub-category: `GEN`, `DFM` (deformed), `RND` (round), `CRM` (ceramic), `GRN` (granite)

**Bảng L (Labour)** — Bậc thợ: `GR3`, `GR4`, `GR5`, `LBR`, `OPR`

**Bảng E (Equipment)** — Loại máy: `CRN`, `EXC`, `PMP`, `TRK`, `MIX`, `CMP`, `GEN`

### 4.6 Attributes thay thế L1 và L4

Thông tin trước đây nhúng trong mã 5-level nay lưu dưới dạng attributes trên `master_work_items`:

| Attribute | Nguồn cũ | Kiểu | Ví dụ |
|:---|:---|:---:|:---|
| `discipline` | L1 (Discipline) | VARCHAR(5) | CV, AR, EL, PL |
| `location` | L4 (Location) | VARCHAR(10) | COL, FND, BEM, SLB, GEN |
| `material_type` | L3 (khi M) | VARCHAR(50) | Gạch nung, AAC block |
| `worker_grade` | L3 (khi L) | VARCHAR(10) | 3/7, 4/7, 5/7 |
| `equip_type` | L3 (khi E) | VARCHAR(50) | Máy đào, cẩu tháp |

### 4.7 Validation

Pattern hợp lệ: `^[AMLE]\.[A-Z]{3,4}\.[A-Z0-9]{3}$`

- Chính xác 3 phần, ngăn cách bằng dấu `.`
- L1 (GROUP) là 3-4 char UPPERCASE
- L2 (TYPE) là 3 char UPPERCASE
- Discipline, location, grade lưu riêng trong attributes
- Code KHÔNG thay đổi khi spec thay đổi → stable identity

### 4.8 Reference Code vs Instance Code

Hệ thống SEC v4.1 tách biệt 2 vai trò mã:

| | Reference Code | Instance Code |
|:---|:---|:---|
| **Vai trò** | Phân loại (classification) | Định danh duy nhất (identity) |
| **Tính duy nhất** | Không unique — 1 ref code → N master items | UNIQUE — 1 instance code = 1 master item |
| **Bảng lưu** | `sec_codes_v4.code` (PK) | `master_work_items.instance_code` |
| **FK** | `master_work_items.sec_code_v4` → `sec_codes_v4.code` | — |
| **Format** | `{L0}.{L1}.{L2}` | `{REF_CODE}-{SEQ:03d}` |
| **Ví dụ** | `A.CONC.STR` | `A.CONC.STR-001` |

**Khi nào cần 2 mã khác nhau?**

Khi 2 master items có cùng nhóm công tác nhưng khác discipline, location, hoặc spec:

```
sec_codes_v4:
  A.CONC.STR    "Bê tông kết cấu"

master_work_items:
  instance_code: A.CONC.STR-001   discipline: CV   location: COL   spec_grade: M200
  instance_code: A.CONC.STR-002   discipline: CV   location: COL   spec_grade: M300
  instance_code: A.CONC.STR-003   discipline: CV   location: BEM   spec_grade: M350
```

→ Cả 3 items share cùng reference code, nhưng mỗi item có instance code riêng + attributes riêng.

**Sinh instance code:**
- `V4CodeGenerator.generate_instance_code(ref_code, db)`
- Query DB tìm max sequence hiện có cho ref_code
- Tự tăng +1, format 3 chữ số: `-001`, `-002`, ...

### 4.9 Phát hiện loại item (Item Type Detection)

**Nguồn:** `MasterDatabaseBuilder._detect_item_type(description)`

Thay vì hardcode `item_table_type='A'`, hệ thống phân tích description để xác định loại:

| Loại | Từ khóa nhận diện | Ví dụ |
|:---:|:---|:---|
| **M** (Material) | `vật liệu`, `vật tư`, `cung cấp`, `ống (hdpe/pvc/ppr/thép)`, `cáp (cu/nhôm/điện)`, `van (cổng/bướm/bi)`, `bê tông thương phẩm`, `vữa xây/trát`, `xi măng`, `thép hình/tấm` | Ống PVC D60, Van cổng DN80 |
| **L** (Labour) | `nhân công`, `thợ`, `công nhân`, `bậc N`, `ngày công`, `ca thợ` | Nhân công bậc 3/7 |
| **E** (Equipment) | `máy (đào/xúc/trộn/bơm/khoan)`, `cần trục`, `cẩu`, `xe (tải/ben)`, `ca máy`, `đầm (dùi/bàn/cóc)` | Máy đào 0.8m3 |
| **A** (Activity) | Mặc định khi không khớp M/L/E | Đổ bê tông cột |

Thứ tự ưu tiên: M → L → E → A (fallback)

---

## 5. Ánh xạ SEC Code V4

**Nguồn:** `backend/app/services/sec_code_v4_mapper.py`

### 5.1 Ánh xạ Legacy → V4 Discipline

Bảng ánh xạ đầy đủ tương tự mục 4.3. Hỗ trợ:
- Exact match (ưu tiên): `SEC-04-02` → `PL`
- Prefix match (fallback): `SEC-04` → `EL`
- Default: `CV`

### 5.2 Thuật toán Fuzzy Matching

Tìm mã v4.0 tham chiếu phù hợp với description:

1. **So khớp tên tiếng Việt** (`name_vi`):
   - Chứa toàn bộ → +0.5 điểm
   - Trùng từ một phần → +0.3 × (overlap / total_words)

2. **So khớp từ khóa** (`keywords_vi`):
   - Mỗi từ khóa khớp → +0.2 điểm

3. Sắp xếp theo điểm giảm dần, trả về top-N kết quả.

---

## 6. Kiểm soát chất lượng Master Data

**Nguồn:** `backend/app/services/master_data_gatekeeper.py`

### 6.1 Hệ thống chấm điểm (0–100)

4 chỉ số chất lượng, mỗi chỉ số 25 điểm:

| Chỉ số | Regex pattern | Ý nghĩa |
|:---|:---|:---|
| `has_verb` | `Đào\|Đắp\|Đổ\|Xây\|Trát\|Lắp\|...` | Có động từ thi công |
| `has_material` | `bê tông\|gạch\|thép\|ống\|cáp\|...` | Có vật liệu |
| `has_specs` | `M\d+\|D\d+\|K\d+\|\d+x\d+\|...` | Có thông số kỹ thuật |
| `has_location` | `móng\|cột\|dầm\|sàn\|tường\|...` | Có vị trí thi công |

### 6.2 Ngưỡng phân loại

| Điểm | Trạng thái | Xử lý |
|:---:|:---|:---|
| ≥ 75 | `APPROVED` | Tự động thêm vào Master DB |
| 50–74 | `PENDING_REVIEW` | Chờ review thủ công |
| < 50 | `REJECTED` | Quarantine/loại bỏ |

### 6.3 Điểm thưởng theo nhóm công tác

| Nhóm | Bonus | Lý do |
|:---|:---:|:---|
| Earthworks | +25 | Công tác đào đắp đơn giản, không cần specs |
| Steel/MEP | +25 | MEP thường thiếu specs formal |
| Road | +25 | Hạ tầng đường đơn giản |
| Finishing | +25 | Hoàn thiện có thể thiếu specs |
| Landscaping | +25 | Cây xanh/cảnh quan đơn giản |
| General | +25 | Cho phép linh hoạt |
| Concrete | +0 | Bê tông cần đầy đủ specs |

### 6.4 Giá trị mặc định theo nhóm

| Nhóm | Default grade | Default specs | Yêu cầu tối thiểu |
|:---|:---:|:---:|:---:|
| Earthworks | K95 | — | 1 indicator |
| Concrete | M250 | `đá 1x2` | 2 indicators |
| Steel/MEP | — | — | 1 indicator |

### 6.5 Pattern vật tư được chấp nhận tự động

Các pattern vật tư/thiết bị được auto-approve (score = 75):

- **Vật tư xây dựng:** vải ĐKT, nilon, cáp, dây, ống, tấm, keo, sơn, gạch, đá, thép, biển báo, bó vỉa, tấm đan, CPĐD
- **MEP/Plumbing:** van, mối nối, phụ kiện ống, sprinkler, bình chữa cháy
- **Điện:** đèn, tủ điện, máy biến áp, cột đèn, contactor, aptomat, MCCB/MCB, rơ le, công tơ, cầu chì, thanh cái
- **Nước:** bể, hố ga, nắp, bích, khớp nối, rắc co, măng xông

### 6.6 Pattern bị từ chối (Forbidden)

| Pattern | Lý do |
|:---|:---|
| `^[\?\!\.\,\;\:]+$` | Chỉ có dấu câu |
| `^\d+$` | Chỉ có số |
| `^[a-zA-Z]{1,2}$` | Quá ngắn, vô nghĩa |
| `^(test\|xxx\|abc\|asdf)` | Pattern rác |
| `^\s*$` | Rỗng |
| `^n/a$` | Placeholder |

### 6.7 Device Code Patterns (bỏ qua)

Các pattern mã thiết bị không phải mô tả công tác: `TĐ-1-II-TBA`, `TBA 10`, `1.2.3` (mã mục), `I.1` (La Mã).

---

## 7. Pipeline xây dựng Master Database

**Nguồn:** `backend/app/services/master_database_builder.py`

### 7.1 Pipeline 3 bước

```
Step 1: AGGREGATION → Step 2: STANDARDIZATION → Step 3: CODING & TAGGING
```

### 7.2 Step 1: Aggregation

- Quét `line_items` theo `file_ids`
- Group by `(description, unit)`
- Đếm frequency (số lần xuất hiện)
- Lọc theo `min_frequency` (mặc định: 1)
- Sắp xếp theo frequency giảm dần

### 7.3 Step 2: Standardization

**Normalize:** Gọi `NormalizationOrchestrator` cho tất cả descriptions.

**Clustering (Fuzzy ≥ 0.85):**
- Với ≤ 5000 items: Pairwise fuzzy matching (RapidFuzz hoặc SequenceMatcher)
- Với > 5000 items: Exact-normalized grouping (tránh O(n²))
- Sử dụng Union-Find để nhóm cluster
- Items phải cùng đơn vị mới được cluster

**Elect Canonical:**
1. Sắp xếp theo frequency (giảm dần), rồi độ dài description (giảm dần)
2. Chọn normalized description không bị degenerate
3. Kiểm tra degenerate: < 5 ký tự, từ lặp, quá generic
4. Fallback: dùng raw description nếu tất cả normalized đều degenerate
5. Tất cả raw descriptions trở thành synonym

**Pareto 80/20:**
- Sắp xếp theo frequency giảm dần
- Đánh dấu `is_pareto_top` cho items chiếm 80% cumulative frequency
- Có thể cấu hình `include_only_pareto` để chỉ xử lý top items

### 7.4 Step 3: Coding & Tagging

1. **Phân loại SEC code:** ML Classifier → Rule-based MEP → WorkCategory fallback
2. **Kiểm tra trùng lặp:** Tìm existing master item theo normalized description
3. **Trích xuất specs:** SpecExtractor
4. **Validate:** Gatekeeper → APPROVED/PENDING/REJECTED
5. **Sinh mã:** WorkCodeGenerator (legacy) + V4CodeGenerator (v4.1 3-level reference code)
6. **Detect item type:** `_detect_item_type(description)` → A/M/L/E (thay vì hardcode 'A')
7. **Sinh instance code:** `V4CodeGenerator.generate_instance_code(ref_code, db)` → auto-increment seq (e.g. `A.CONC.STR-001`)
8. **Lưu trữ:**
   - APPROVED → `master_work_items` (với `sec_code_v4`, `instance_code`, `item_table_type`) + synonyms
   - PENDING → `pending_master_items`
   - REJECTED → `quarantine_log`
9. **Back-link:** Cập nhật `line_items.matched_master_id`

### 7.5 Phân loại MEP sub-SEC (Rule-based)

| SEC Code | Patterns |
|:---|:---|
| SEC-04-01 (Electrical) | `mccb`, `mcb`, `contactor`, `aptomat`, `cáp điện`, `dây điện`, `tủ điện`, `cầu chì`, `thanh cái`, `xlpe` |
| SEC-04-02 (Plumbing) | `ống hdpe/pvc/ppr/thép`, `van cổng/bướm/bi`, `côn thu`, `cút`, `tê`, `bích`, `bơm chìm/nước` |
| SEC-04-03 (HVAC) | `điều hòa`, `thông gió`, `ahu`, `fcu`, `ống gió`, `dàn lạnh/nóng` |
| SEC-04-04 (PCCC) | `pccc`, `báo cháy`, `sprinkler`, `bình chữa cháy`, `đầu phun` |

### 7.6 Cấu hình Build

| Tham số | Mặc định | Ý nghĩa |
|:---|:---:|:---|
| `pareto_threshold` | 0.80 | Ngưỡng Pareto |
| `clustering_threshold` | 0.85 | Ngưỡng fuzzy clustering |
| `min_frequency` | 1 | Tần suất tối thiểu |
| `auto_approve` | False | Tự động approve PENDING items |
| `clear_existing` | False | Xóa master data trước khi build |
| `batch_size` | 500 | Kích thước batch |

---

## 8. Vòng đời Specification

**Nguồn:** `backend/app/services/spec_lifecycle_service.py`

### 8.1 Ba trạng thái

```
draft → detailed → final
```

### 8.2 Điều kiện thăng cấp

| Chuyển tiếp | Điều kiện |
|:---|:---|
| draft → detailed | `spec_completeness ≥ 0.50` (50%) |
| detailed → final | `spec_completeness ≥ 0.75` (75%) VÀ `is_verified == True` |

### 8.3 Nguồn dữ liệu và độ tin cậy

| Nguồn (`spec_source`) | Confidence | Ý nghĩa |
|:---|:---:|:---|
| `default` | 0.3 | Giá trị mặc định hệ thống |
| `boq` | 0.5 | Trích xuất từ BOQ |
| `drawing` | 0.8 | Từ bản vẽ kỹ thuật |
| `as_built` | 1.0 | Từ hồ sơ hoàn công |

### 8.4 Tính completeness theo trọng số

| Field | Trọng số | Mô tả |
|:---|:---:|:---|
| `spec_category` | 25% | Danh mục vật liệu (Bê tông, Thép, Ống) |
| `spec_material` | 25% | Loại vật liệu (HDPE, PPR, Cu/XLPE) |
| `spec_grade` | 30% | Mác/Cấp (M200, CB400, PN16) |
| `spec_dimension` | 20% | Kích thước (D110, 4x16mm2, 600x600) |

### 8.5 Audit Trail

Mọi thay đổi spec được ghi nhận trong `SpecChangeLog`:
- `field_name`: Field nào thay đổi
- `old_value` / `new_value`: Giá trị cũ/mới
- `old_status` / `new_status`: Trạng thái cũ/mới
- `change_source`: Nguồn thay đổi
- `changed_by`: User thực hiện
- `changed_at`: Thời điểm

---

## 9. Mô hình dữ liệu

**Nguồn:** `backend/app/models/master_work_item.py`, `backend/app/models/sec_code_v4.py`, `backend/app/models/activity_bom.py`

### 9.1 Bảng `master_work_items`

| Cột | Kiểu | Mô tả |
|:---|:---:|:---|
| `master_id` | INT PK | Khóa chính |
| `work_code` | VARCHAR(50) UNIQUE | Mã công tác legacy |
| `description` | TEXT | Mô tả chuẩn hóa |
| `description_normalized` | VARCHAR(500) | Lowercase, trim (for indexing) |
| `sec_code` | VARCHAR(20) | Mã SEC legacy |
| `unit_standard` | VARCHAR(20) | Đơn vị chuẩn |
| `spec_category` | VARCHAR(100) | Danh mục vật liệu |
| `spec_material` | VARCHAR(100) | Loại vật liệu |
| `spec_grade` | VARCHAR(50) | Mác/Cấp |
| `spec_dimension` | VARCHAR(200) | Kích thước |
| `matching_key` | VARCHAR(255) | Key cho O(1) lookup |
| `spec_status` | ENUM(draft/detailed/final) | Trạng thái spec |
| `spec_source` | ENUM(default/boq/drawing/as_built) | Nguồn spec |
| `spec_confidence` | FLOAT | Độ tin cậy 0.0–1.0 |
| `spec_completeness` | FLOAT | Hoàn thiện 0.0–1.0 |
| `sec_code_v4` | VARCHAR(30) FK | Mã v4.1 3-level reference (e.g. `A.CONC.STR`) |
| `instance_code` | VARCHAR(35) UNIQUE | Mã v4.1 instance (e.g. `A.CONC.STR-001`) |
| `item_table_type` | ENUM(A/M/L/E) | Bảng v4.0 |
| `embedding_vector` | BLOB | Pre-computed SBERT embedding |
| `is_verified` | BOOL | Đã verify bởi user |
| `occurrence_count` | INT | Số lần xuất hiện |

**Indexes:** `sec_code`, `unit_standard`, `is_active`, `description_normalized`, `spec_category`, `spec_material`, `spec_grade`, `spec_status`, `item_table_type`, `matching_key`, `sec_code_v4` (non-unique), `instance_code` (unique)

### 9.2 Bảng `sec_codes_v4`

| Cột | Kiểu | Mô tả |
|:---|:---:|:---|
| `code` | VARCHAR(30) PK | Full code (e.g. `A.CONC.STR`) |
| `table_type` | ENUM(A/M/L/E) | Bảng |
| `discipline` | VARCHAR(5) | L1 (CV, AR, EL...) |
| `group_code` | VARCHAR(5) | L2 (CON, RBR, PIP...) |
| `type_code` | VARCHAR(5) | L3 (POUR, FABR, INST...) |
| `spec_code` | VARCHAR(5) | L4 (COL, FND, GEN...) |
| `name_vi` | VARCHAR(200) | Tên tiếng Việt |
| `name_en` | VARCHAR(200) | Tên tiếng Anh |
| `unit` | VARCHAR(20) | Đơn vị mặc định |
| `keywords_vi` | TEXT | Từ khóa VI (JSON array) |
| `keywords_en` | TEXT | Từ khóa EN (JSON array) |
| `waste_percent` | FLOAT | Hệ số hao hụt chuẩn |

**Indexes:** `table_type`, `discipline`, `group_code`, `type_code`

**Relationship:** `sec_codes_v4.code` ← 1:N → `master_work_items.sec_code_v4` (FK)

### 9.3 Bảng `activity_bom` (Bill of Materials)

Mô hình quan hệ N:M giữa Activity và Resource:

| Cột | Kiểu | Mô tả |
|:---|:---:|:---|
| `bom_id` | INT PK | Khóa chính |
| `activity_code` | VARCHAR(30) FK | Mã Activity (A.*) |
| `resource_code` | VARCHAR(30) FK | Mã Resource (M.*/L.*/E.*) |
| `resource_type` | ENUM(M/L/E) | Loại resource |
| `quantity_factor` | FLOAT | Hệ số tiêu hao |
| `notes` | TEXT | Ghi chú |

**Unique constraint:** `(activity_code, resource_code)`

**Ví dụ BOM:**
```
A.CONC.STR (BT kết cấu)   instance: A.CONC.STR-001, discipline=CV, location=COL, spec_grade=M300
  ├── M.CONC.GEN  × 1.03 (hao hụt 3%)
  ├── L.CONC.GR4  × 0.35 (công/m³)
  └── E.CONC.PMP  × 0.02 (ca/m³)
```

---

## 10. Hệ thống mã SEC v4.1 (3-Level Code + Attribute Model)

**Nguồn:** `backend/docs/SEC_Code_For_CostDatabase.md`

### 10.1 Kiến trúc 4 bảng (Quad-Table) — Mã 3 cấp

| Bảng | Prefix | Bản chất | Người dùng chính |
|:---:|:---:|:---|:---|
| A | `A.` | Hành động thi công | QS, PM, Đấu thầu |
| M | `M.` | Vật tư vật lý | Mua sắm, Kho |
| L | `L.` | Nhân công | HR, QS |
| E | `E.` | Máy móc thiết bị | Thiết bị, QS |

> Đơn giá tổng hợp = Vật tư (M) + Nhân công (L) + Máy móc (E)

**Format mã:** `[PREFIX].[GROUP].[TYPE]` (3 phần)

**Nguyên tắc Same Suffix:** `A.CONC.STR`, `M.CONC.STR`, `L.CONC.STR`, `E.CONC.STR`

**Reference vs Instance:**
- Reference code (1:N): `A.CONC.STR` — phân loại, không unique
- Instance code (unique): `A.CONC.STR-001` — định danh duy nhất cho mỗi master item

### 10.2 Discipline — Attribute (không nằm trong mã)

Discipline nay là attribute trên `master_work_items`, không phải phần của mã:

| Mã | Tên | Mô tả |
|:---:|:---|:---|
| PM | Preliminaries | Chi phí chung |
| CV | Civil | Đất, móng, kết cấu |
| AR | Architecture | Hoàn thiện nội thất |
| EN | Envelope | Mặt dựng, vỏ bao che |
| EL | Electrical | Hệ thống điện |
| PL | Plumbing | Cấp thoát nước |
| ME | Mechanical | HVAC |
| FP | Fire Protection | PCCC |
| LV | Low Voltage | Điện nhẹ, ELV |
| VT | Vertical Transport | Thang máy |
| LA | Landscape | Cảnh quan |
| EX | External Works | Hạ tầng ngoài nhà |

### 10.3 Attributes thay thế các level cũ

| Attribute | Nguồn cũ (5-level) | Lưu ở | Ví dụ |
|:---|:---|:---|:---|
| `discipline` | L1 (Discipline) | `master_work_items.discipline` | CV, AR, EL |
| `location` | L4 (Location) | `master_work_items.location` | COL, FND, BEM |
| `material_type` | L3 (khi M) | `master_work_items.material_type` | Gạch nung |
| `worker_grade` | L3 (khi L) | `master_work_items.worker_grade` | 3/7, 4/7 |
| `equip_type` | L3 (khi E) | `master_work_items.equip_type` | Máy đào |
| `spec_grade` | (giữ nguyên) | `master_work_items.spec_grade` | M300, CB400 |
| `spec_material` | (giữ nguyên) | `master_work_items.spec_material` | HDPE, Cu/XLPE |

### 10.4 Quy tắc Validation

| # | Quy tắc |
|:---:|:---|
| 1 | Mã phải đúng 3 phần, ngăn cách bằng `.` |
| 2 | L0 phải là `A`, `M`, `L`, hoặc `E` |
| 3 | L1 (GROUP) phải 3-4 char UPPERCASE, nằm trong danh sách |
| 4 | L2 (TYPE) phải 3 char UPPERCASE |
| 5 | Mã KHÔNG chứa discipline, location, grade, spec |
| 6 | Instance code format: `{REF_CODE}-{SEQ:03d}` |
| 7 | Discipline phải nằm trong danh sách 12 bộ môn (attribute) |

### 10.5 Đơn vị chuẩn hóa

| Input variants | Chuẩn | Ghi chú |
|:---|:---:|:---|
| m3, m3, met khoi | **m3** | Be tong, dat |
| m2, m2, met vuong | **m2** | Van khuon, op lat |
| md, m, ml, met dai | **md** | Ong, cap |
| kg, KG, kilogram | **kg** | Thep, ket cau |
| tan, T | **tan** | Asphalt |
| cai, Cai | **cai** | Thiet bi roi |
| bo, Bo | **bo** | Thiet bi lap, cua |
| he thong, HT | **TT** | Goi thau |
| cong | **cong** | Nhan cong (1 cong = 8h) |
| ca | **ca** | Ca may (1 ca = 8h) |

### 10.6 Ví dụ so sánh v4.0 → v4.1

| Mô tả | v4.0 (5-level) | v4.1 (3-level ref) | v4.1 Instance + Attributes |
|:---|:---|:---|:---|
| Đổ BT cột M300 | `A.CV.CON.POUR.COL` | `A.CONC.STR` | `A.CONC.STR-001` discipline=CV, location=COL, spec_grade=M300 |
| Đổ BT dầm M350 | `A.CV.CON.POUR.BEM` | `A.CONC.STR` | `A.CONC.STR-002` discipline=CV, location=BEM, spec_grade=M350 |
| Đổ BT lót M100 | `A.CV.CON.M100.LEA` | `A.CONC.LEA` | `A.CONC.LEA-001` discipline=CV, location=FND, spec_grade=M100 |
| Thép CB400 D16 | `M.CV.RBR.CB40.0016` | `M.RBAR.DFM` | `M.RBAR.DFM-001` spec_grade=CB400, spec_dimension=D16 |
| Thợ BT bậc 4 | `L.CV.CON.THO4.GEN` | `L.CONC.GR4` | `L.CONC.GR4-001` discipline=CV, worker_grade=4/7 |
| Máy bơm BT | `E.CV.CON.PUMP.GEN` | `E.CONC.PMP` | `E.CONC.PMP-001` discipline=CV |
