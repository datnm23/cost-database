# HỆ THỐNG MÃ SEC CODE CHO COST DATABASE
**Version:** 4.1 — 3-Level Code Architecture (PREFIX.GROUP.TYPE) + Attribute Model
**Mục đích:** Upload, Parse, Classify BOQ & MRD tự động — Hỗ trợ AI/NLP/Fuzzy Matching
**Ngày cập nhật:** 11/02/2026
**Kiến trúc:** Data Architect / BIM Manager / QS Director Review Applied
**Schema Version:** `SEC-COST-DB-v4.1`

---

## I. TỔNG QUAN KIẾN TRÚC (ARCHITECTURE OVERVIEW)

### 1.1 Mô hình 4 bảng — Tứ trụ Cost Database

> 🏗️ **Đơn giá tổng hợp = Vật tư (M) + Nhân công (L) + Máy móc (E)**
>
> Bảng A (Activity) là bảng **tổ hợp** — kết nối M, L, E thông qua bảng BOM trung gian.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BẢNG A — ACTIVITY / BOQ                         │
│          (Hành động thi công, dùng cho QS/Đấu thầu)               │
│                                                                     │
│   ref_code:  A.CONC.STR                                            │
│   instance:  A.CONC.STR-001  "Đổ BT cột"                          │
│   attributes:                                                       │
│     discipline: CV    location: COL   spec_grade: M300             │
│        │                                                            │
│        ├──── BOM Link ────►  M.CONC.GEN   (BT thương phẩm)       │
│        │                     × 1.03 (hao hụt 3%)                   │
│        │                                                            │
│        ├──── BOM Link ────►  L.CONC.GR3   (Thợ bậc 3/7)          │
│        │                     × 0.35 (công/m³)                      │
│        │                                                            │
│        └──── BOM Link ────►  E.CONC.PMP   (Máy bơm BT)           │
│                              × 0.02 (ca/m³)                        │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Nguyên tắc phân tách tuyệt đối

| Bảng | Tiền tố | Bản chất | Người dùng chính | Có vị trí? |
|:---:|:---:|:---|:---|:---:|
| **A** | `A.` | Hành động thi công (Activity/BOQ) | QS, PM, Đấu thầu | ✅ Có |
| **M** | `M.` | Vật tư vật lý (Material/MRD) | Mua sắm, Kho bãi | ❌ Không |
| **L** | `L.` | Nhân công (Labour) | HR, QS, Đơn giá | ❌ Không |
| **E** | `E.` | Máy móc thiết bị (Equipment) | Thiết bị, QS, Đơn giá | ❌ Không |

> *"Đào đất là Hành động (A). Thép CB300 ɸ10 là Vật tư (M). Thợ bậc 4 là Nhân công (L). Máy đào 1.2m³ là Thiết bị (E). Không bao giờ trộn lẫn."*

---

## II. CẤU TRÚC MÃ ĐỊNH DANH (SMART CODE 3-LEVEL)

### 2.1 Công thức mã

```
[PREFIX].[GROUP].[TYPE]

   L0        L1       L2
   1 char    3-4 char 3 char
```

> **Chính xác 3 phần**, ngăn cách bằng dấu chấm (`.`). Discipline và location **không nằm trong mã** — chúng là attributes trên `master_work_items`.
>
> **Nguyên tắc "Same Suffix":** Cả 4 bảng A, M, L, E dùng chung GROUP.TYPE khi cùng loại công tác:
> `A.CONC.STR`, `M.CONC.STR`, `L.CONC.STR`, `E.CONC.STR`

### 2.2 Bảng quy tắc mã hóa theo từng bảng

| Level | Ý nghĩa | Bảng A (Activity) | Bảng M (Material) | Bảng L (Labour) | Bảng E (Equipment) |
|:---:|:---|:---|:---|:---|:---|
| **L0** | Tiền tố | `A` | `M` | `L` | `E` |
| **L1** | Nhóm (GROUP) | CONC, RBAR, PIPE... | CONC, RBAR, PIPE... | CONC, RBAR, PIPE... | CONC, EXCV, CRAN... |
| **L2** | Phân loại (TYPE) | STR, LEA, FND... | GEN, RND, DFM... | GR3, GR4, GR5... | PMP, VIB, MIX... |

> **Thay đổi từ v4.0 → v4.1:**
> - L1 (Discipline) bị loại khỏi mã → trở thành attribute `discipline` trên master_work_items
> - L4 (Location/Spec) bị loại khỏi mã → trở thành attributes `location`, `spec_grade`, `spec_material`
> - GROUP codes mở rộng từ 3→4 char: `CON`→`CONC`, `RBR`→`RBAR`, `PIP`→`PIPE`, `CBL`→`CABL`
> - TYPE codes không còn action-based (POUR, FABR) mà là sub-category (STR, LEA, FND)

#### Nguyên tắc GROUP và TYPE (QUAN TRỌNG)

**GROUP (L1)** phản ánh nhóm công tác / vật liệu chính:

| GROUP | Tiếng Việt | English | Dùng cho |
|:---:|:---|:---|:---|
| CONC | Bê tông | Concrete | A, M, L, E |
| RBAR | Cốt thép | Rebar | A, M, L |
| FWRK | Ván khuôn | Formwork | A, M, L |
| EXCV | Đào đất | Excavation | A, L, E |
| PILE | Cọc móng | Piling | A, M, L, E |
| STLS | Kết cấu thép | Structural Steel | A, M, L, E |
| PIPE | Ống | Piping | A, M, L |
| CABL | Cáp điện | Cable | A, M, L |
| WALL | Tường | Wall | A, M, L |
| CEIL | Trần | Ceiling | A, M, L |
| FLOR | Sàn | Floor | A, M, L |
| PANT | Sơn | Paint | A, M, L |
| DOOR | Cửa | Door | A, M, L |
| WTPF | Chống thấm | Waterproofing | A, M, L |

**TYPE (L2)** phản ánh phân loại phụ (sub-category), không còn action-based:

| Bảng | TYPE phản ánh | Ví dụ | KHÔNG dùng |
|:---:|:---|:---|:---|
| A | Sub-category công tác | STR (structural), LEA (lean), FND (foundation) | ~~POUR~~, ~~FABR~~, ~~FORM~~ |
| M | Sub-category vật tư | GEN (general), RND (round), DFM (deformed) | ~~M300~~, ~~CB40~~ |
| L | Bậc thợ | GR3 (grade 3), GR4 (grade 4), GR5, OPR | ~~THO3~~, ~~THO4~~ |
| E | Sub-category máy | PMP (pump), VIB (vibrator), MIX (mixer), CRN (crane) | |

### 2.3 Reference Code vs Instance Code

Mã SEC v4.1 có **2 hệ thống**:

| | Reference Code | Instance Code |
|:---|:---|:---|
| **Mục đích** | Phân loại (1:N) | Định danh duy nhất |
| **Tính duy nhất** | Không unique | UNIQUE |
| **Bảng lưu** | `sec_codes_v4.code` | `master_work_items.instance_code` |
| **Ví dụ** | `A.CONC.STR` | `A.CONC.STR-001` |
| **Format** | `{L0}.{L1}.{L2}` | `{REF_CODE}-{SEQ:03d}` |

```
sec_codes_v4 (Reference — PK, không đổi)
  A.CONC.STR    "Bê tông kết cấu"
       │
       │ 1:N
       ▼
master_work_items (Instance — mỗi item có mã riêng + attributes)
  instance_code: A.CONC.STR-001   discipline: CV   location: COL   spec_grade: M200
  instance_code: A.CONC.STR-002   discipline: CV   location: COL   spec_grade: M300
  instance_code: A.CONC.STR-003   discipline: CV   location: BEM   spec_grade: M350
```

> Khi 2 master items có cùng nhóm công tác (bê tông kết cấu) nhưng khác discipline, location, hoặc spec (M200 vs M300), chúng share cùng reference code nhưng có instance code riêng. Discipline, location, và spec được lưu riêng trong attributes trên `master_work_items`.

### 2.4 Attributes trên master_work_items (thay thế L1, L4)

Thông tin trước đây nhúng trong mã 5-level nay lưu dưới dạng attributes:

| Attribute | Nguồn cũ (v4.0) | Kiểu | Ví dụ |
|:---|:---|:---:|:---|
| `discipline` | L1 (Discipline) | VARCHAR(5) | CV, AR, EL, PL, ME |
| `location` | L4 (Location) | VARCHAR(10) | COL, FND, BEM, SLB, GEN |
| `material_type` | L3 (khi M) | VARCHAR(50) | Gạch nung, AAC block |
| `worker_grade` | L3 (khi L) | VARCHAR(10) | 3/7, 4/7, 5/7 |
| `equip_type` | L3 (khi E) | VARCHAR(50) | Máy đào, cẩu tháp |
| `spec_grade` | (giữ nguyên) | VARCHAR(50) | M300, CB400, PN16 |
| `spec_material` | (giữ nguyên) | VARCHAR(100) | Cu/XLPE/PVC, HDPE |
| `spec_dimension` | (giữ nguyên) | VARCHAR(200) | D110, 4x16mm2, 600x600 |

> **Lợi ích:** Mã ngắn gọn, dễ nhớ, ổn định. Thông tin chi tiết truy vấn qua attributes, linh hoạt hơn khi mở rộng.

### 2.5 Danh sách mã Discipline (attribute — không nằm trong mã)

| Mã L1 | Tên Bộ môn | Mô tả | A | M | L | E |
|:---:|:---|:---|:---:|:---:|:---:|:---:|
| **PM** | Preliminaries | Chi phí chung, quản lý | ✅ | ❌ | ❌ | ❌ |
| **CV** | Civil | Đất, móng, kết cấu | ✅ | ✅ | ✅ | ✅ |
| **AR** | Architecture | Hoàn thiện nội thất | ✅ | ✅ | ✅ | ✅ |
| **EN** | Envelope | Mặt dựng, vỏ bao che | ✅ | ✅ | ✅ | ✅ |
| **EL** | Electrical | Hệ thống điện | ✅ | ✅ | ✅ | ✅ |
| **PL** | Plumbing | Cấp thoát nước | ✅ | ✅ | ✅ | ✅ |
| **ME** | Mechanical | HVAC | ✅ | ✅ | ✅ | ✅ |
| **FP** | Fire Protection | PCCC | ✅ | ✅ | ✅ | ✅ |
| **LV** | Low Voltage | Điện nhẹ, ELV | ✅ | ✅ | ✅ | ✅ |
| **VT** | Vertical Transport | Thang máy | ✅ | ✅ | ❌ | ❌ |
| **LA** | Landscape | Cảnh quan | ✅ | ✅ | ✅ | ✅ |
| **EX** | External Works | Hạ tầng ngoài nhà | ✅ | ✅ | ✅ | ✅ |

---
---

# BẢNG A — MASTER BOQ (ACTIVITY CODE TABLE)

> **Mục đích:** QS, Lập dự toán, Đấu thầu, Nghiệm thu.  
> **Nguyên tắc:** Mô tả **hành động thi công** tại **vị trí cụ thể**.  
> **Kết nối:** Mỗi Activity liên kết tới M, L, E qua bảng BOM (Phụ lục B).  
> **Cột bảng chuẩn hóa:**

| Cột | Kiểu | Ý nghĩa |
|:---|:---:|:---|
| `CODE` | string | Mã Activity 3-level (ref_code) |
| `TÊN CÔNG TÁC` | string | Mô tả hành động thi công |
| `ĐƠN VỊ` | enum | Đơn vị tính chuẩn hóa (Phụ lục C) |
| `KEYWORDS_VI` | string | Từ khóa tiếng Việt cho NLP |
| `KEYWORDS_EN` | string | Từ khóa tiếng Anh cho NLP |
| `BOM_M` | string[] | Danh sách mã M liên kết (không dùng wildcard) |
| `BOM_L` | string | Mã L (nhân công) liên kết |
| `BOM_E` | string | Mã E (máy móc) liên kết |

---

## A.PM — CHI PHÍ CHUNG (PRELIMINARIES)

| CODE | TÊN CÔNG TÁC | ĐƠN VỊ | KEYWORDS_VI | KEYWORDS_EN |
|:---|:---|:---:|:---|:---|
| **A.PM.GEN.GEN.GEN** | **Chi phí chung** | TT | chung, tổng, gói | general, lump sum |
| **A.PM.MGT.xxx** | **Quản lý** | | | |
| A.PM.MGT.PROJ.GEN | Quản lý dự án | TT | quản lý, PM, BQLDA | project management, supervision |
| A.PM.MGT.SUPV.GEN | Tư vấn giám sát | TT | TVGS, giám sát | construction supervision |
| A.PM.MGT.OFFC.SIT | Văn phòng công trường | TT | văn phòng, site office, lán trại | site office, temporary facility |
| **A.PM.DSN.xxx** | **Thiết kế** | | | |
| A.PM.DSN.ARCH.GEN | Thiết kế kiến trúc | TT | thiết kế, KT, kiến trúc | architectural design |
| A.PM.DSN.STRU.GEN | Thiết kế kết cấu | TT | kết cấu, KC | structural design |
| A.PM.DSN.MEPD.GEN | Thiết kế MEP | TT | MEP, cơ điện, M&E | MEP design |
| A.PM.DSN.REVW.GEN | Thẩm tra thiết kế | TT | thẩm tra, review | design review |
| **A.PM.SRV.xxx** | **Khảo sát** | | | |
| A.PM.SRV.SOIL.BOR | Khảo sát địa chất | TT | địa chất, khoan, soil | geotechnical survey, boring |
| A.PM.SRV.TOPO.GEN | Đo đạc địa hình | TT | đo đạc, địa hình | topographic survey |
| **A.PM.INS.xxx** | **Bảo hiểm & An toàn** | | | |
| A.PM.INS.CARR.GEN | Bảo hiểm công trình | TT | bảo hiểm, CAR | contractor all risks insurance |
| A.PM.INS.SAFE.HSE | An toàn lao động | TT | an toàn, HSE, PPE | health safety environment |
| **A.PM.PER.xxx** | **Giấy phép** | | | |
| A.PM.PER.BLDG.GPX | Giấy phép xây dựng | TT | giấy phép, GPXD | building permit |
| A.PM.PER.FIRE.PCC | Thẩm duyệt PCCC | TT | PCCC, thẩm duyệt | fire approval |
| **A.PM.CTG.xxx** | **Dự phòng** | | | |
| A.PM.CTG.DESG.GEN | Dự phòng thiết kế | % | dự phòng, contingency | design contingency |
| A.PM.CTG.ESCL.GEN | Dự phòng trượt giá | % | trượt giá, escalation | price escalation |

---

## A.CV — CÔNG TÁC ĐẤT & KẾT CẤU (CIVIL WORKS)

> 💡 Đây là **hành động thi công** — không thể "mua" hay "nhập kho".

| CODE              | TÊN CÔNG TÁC               | ĐƠN VỊ | KEYWORDS_VI                | KEYWORDS_EN                | BOM_M                                                      | BOM_L             | BOM_E             |
| :---------------- | :------------------------- | :----: | :------------------------- | :------------------------- | :--------------------------------------------------------- | :---------------- | :---------------- |
| **A.CV.EXC.xxx**  | **Công tác đất**           |        |                            |                            |                                                            |                   |                   |
| A.CV.EXC.MACH.GEN | Đào đất móng bằng máy      |   m³   | đào, đất, máy, excavation  | machine excavation         | —                                                          | L.CV.EXC.OPER.GEN | E.CV.EXC.EXCA.GEN |
| A.CV.EXC.MANU.GEN | Đào đất móng thủ công      |   m³   | đào, thủ công, manual      | manual excavation          | —                                                          | L.CV.EXC.THO3.GEN | —                 |
| A.CV.EXC.BKFL.GEN | Đắp đất công trình         |   m³   | đắp, lấp, backfill         | backfill                   | —                                                          | L.CV.EXC.THO3.GEN | E.CV.EXC.COMP.GEN |
| A.CV.EXC.LEVL.GEN | San nền                    |   m³   | san, nền, leveling         | site leveling              | —                                                          | L.CV.EXC.OPER.GEN | E.CV.EXC.BULL.GEN |
| A.CV.EXC.TRAN.GEN | Vận chuyển đất             |   m³   | vận chuyển, đổ thải        | soil transport             | —                                                          | L.CV.EXC.OPER.GEN | E.CV.EXC.TRUK.GEN |
| **A.CV.PIL.xxx**  | **Thi công cọc**           |        |                            |                            |                                                            |                   |                   |
| A.CV.PIL.BORE.D08 | TC cọc khoan nhồi D800     |   md   | khoan nhồi, bored pile     | bored pile D800            | M.CV.CON.M400.GEN                                          | L.CV.PIL.THO4.GEN | E.CV.PIL.BRIG.GEN |
| A.CV.PIL.BORE.D10 | TC cọc khoan nhồi D1000    |   md   | khoan nhồi, bored pile     | bored pile D1000           | M.CV.CON.M400.GEN                                          | L.CV.PIL.THO4.GEN | E.CV.PIL.BRIG.GEN |
| A.CV.PIL.BORE.D12 | TC cọc khoan nhồi D1200    |   md   | khoan nhồi, bored pile     | bored pile D1200           | M.CV.CON.M400.GEN                                          | L.CV.PIL.THO4.GEN | E.CV.PIL.BRIG.GEN |
| A.CV.PIL.DRVN.300 | TC cọc ép 300x300          |   md   | cọc ép, driven pile        | driven pile 300            | M.CV.CON.M350.GEN                                          | L.CV.PIL.THO4.GEN | E.CV.PIL.JACK.GEN |
| A.CV.PIL.DRVN.350 | TC cọc ép 350x350          |   md   | cọc ép, driven pile        | driven pile 350            | M.CV.CON.M350.GEN                                          | L.CV.PIL.THO4.GEN | E.CV.PIL.JACK.GEN |
| A.CV.PIL.HAMR.300 | TC cọc đóng 300x300        |   md   | cọc đóng, hammer           | hammer driven pile         | M.CV.CON.M300.GEN                                          | L.CV.PIL.THO4.GEN | E.CV.PIL.HAMR.GEN |
| A.CV.PIL.SOIL.D06 | TC cọc xi măng đất D600    |   md   | xi măng đất, soil mixing   | soil cement column         | —                                                          | L.CV.PIL.THO4.GEN | E.CV.PIL.MIXR.GEN |
| A.CV.PIL.TEST.PDA | Thí nghiệm cọc PDA         |  cọc   | thí nghiệm, PDA            | PDA test                   | —                                                          | —                 | —                 |
| A.CV.PIL.TEST.SLT | Thí nghiệm nén tĩnh        |  cọc   | thí nghiệm, nén tĩnh       | static load test           | —                                                          | —                 | —                 |
| **A.CV.CON.xxx**  | **Đổ bê tông**             |        |                            |                            |                                                            |                   |                   |
| A.CV.CON.M100.LEA | Đổ BT lót móng M100        |   m³   | BT lót, lót móng           | lean concrete M100         | M.CV.CON.M100.GEN                                          | L.CV.CON.THO3.GEN | E.CV.CON.PUMP.GEN |
| A.CV.CON.M250.PAD | Đổ BT móng đơn M250        |   m³   | móng đơn, pad              | pad foundation M250        | M.CV.CON.M250.GEN                                          | L.CV.CON.THO3.GEN | E.CV.CON.PUMP.GEN |
| A.CV.CON.M250.STP | Đổ BT móng băng M250       |   m³   | móng băng, strip           | strip foundation M250      | M.CV.CON.M250.GEN                                          | L.CV.CON.THO3.GEN | E.CV.CON.PUMP.GEN |
| A.CV.CON.M300.PCA | Đổ BT đài móng M300        |   m³   | đài móng, pile cap         | pile cap M300              | M.CV.CON.M300.GEN                                          | L.CV.CON.THO3.GEN | E.CV.CON.PUMP.GEN |
| A.CV.CON.M250.GBM | Đổ BT giằng móng M250      |   m³   | giằng móng, grade beam     | grade beam M250            | M.CV.CON.M250.GEN                                          | L.CV.CON.THO3.GEN | E.CV.CON.PUMP.GEN |
| A.CV.CON.M300.BSM | Đổ BT sàn hầm M300         |   m³   | sàn hầm, basement slab     | basement slab M300         | M.CV.CON.M300.GEN                                          | L.CV.CON.THO3.GEN | E.CV.CON.PUMP.GEN |
| A.CV.CON.M300.COL | Đổ BT cột M300             |   m³   | BT cột, column             | column concrete M300       | M.CV.CON.M300.GEN                                          | L.CV.CON.THO4.GEN | E.CV.CON.PUMP.GEN |
| A.CV.CON.M300.BEM | Đổ BT dầm M300             |   m³   | BT dầm, beam               | beam concrete M300         | M.CV.CON.M300.GEN                                          | L.CV.CON.THO4.GEN | E.CV.CON.PUMP.GEN |
| A.CV.CON.M250.SLB | Đổ BT sàn M250             |   m³   | BT sàn, slab, floor        | slab concrete M250         | M.CV.CON.M250.GEN                                          | L.CV.CON.THO3.GEN | E.CV.CON.PUMP.GEN |
| A.CV.CON.M350.SHW | Đổ BT vách M350            |   m³   | BT vách, shear wall        | shear wall M350            | M.CV.CON.M350.GEN                                          | L.CV.CON.THO4.GEN | E.CV.CON.PUMP.GEN |
| A.CV.CON.M350.COR | Đổ BT lõi thang M350       |   m³   | lõi thang, core            | core wall M350             | M.CV.CON.M350.GEN                                          | L.CV.CON.THO4.GEN | E.CV.CON.PUMP.GEN |
| A.CV.CON.M250.STR | Đổ BT cầu thang M250       |   m³   | cầu thang, stair           | stair concrete M250        | M.CV.CON.M250.GEN                                          | L.CV.CON.THO3.GEN | E.CV.CON.PUMP.GEN |
| A.CV.CON.M200.LNT | Đổ BT lanh tô M200         |   m³   | lanh tô, lintel            | lintel M200                | M.CV.CON.M200.GEN                                          | L.CV.CON.THO3.GEN | —                 |
| A.CV.CON.M200.CNP | Đổ BT ô văng M200          |   m³   | ô văng, canopy             | canopy M200                | M.CV.CON.M200.GEN                                          | L.CV.CON.THO3.GEN | —                 |
| A.CV.CON.M350.BWL | Đổ BT tường hầm M350       |   m³   | tường hầm                  | basement wall M350         | M.CV.CON.M350.GEN                                          | L.CV.CON.THO4.GEN | E.CV.CON.PUMP.GEN |
| **A.CV.RBR.xxx**  | **Gia công & lắp thép**    |        |                            |                            |                                                            |                   |                   |
| A.CV.RBR.CB30.FND | GC thép móng CB300 D≤10    |   kg   | thép, móng, d10            | rebar CB300 foundation     | M.CV.RBR.CB30.0010                                         | L.CV.RBR.THO4.GEN | —                 |
| A.CV.RBR.CB40.FND | GC thép móng CB400 D12-18  |   kg   | thép, móng, d12-d18        | rebar CB400 foundation     | M.CV.RBR.CB40.0016; M.CV.RBR.CB40.0018                     | L.CV.RBR.THO4.GEN | —                 |
| A.CV.RBR.CB50.FND | GC thép móng CB500 D20-32  |   kg   | thép, móng, d20-d28        | rebar CB500 foundation     | M.CV.RBR.CB50.0025; M.CV.RBR.CB50.0028                     | L.CV.RBR.THO4.GEN | —                 |
| A.CV.RBR.CB30.COL | GC thép cột CB300 D≤10     |   kg   | thép, cột, d10             | rebar CB300 column         | M.CV.RBR.CB30.0010                                         | L.CV.RBR.THO4.GEN | —                 |
| A.CV.RBR.CB40.COL | GC thép cột CB400 D12-18   |   kg   | thép, cột, d12-d18         | rebar CB400 column         | M.CV.RBR.CB40.0016; M.CV.RBR.CB40.0018                     | L.CV.RBR.THO4.GEN | —                 |
| A.CV.RBR.CB50.COL | GC thép cột CB500 D20-32   |   kg   | thép, cột, d20+            | rebar CB500 column         | M.CV.RBR.CB50.0025; M.CV.RBR.CB50.0028; M.CV.RBR.CB50.0032 | L.CV.RBR.THO4.GEN | —                 |
| A.CV.RBR.CB30.BEM | GC thép dầm CB300 D≤10     |   kg   | thép, dầm, d10             | rebar CB300 beam           | M.CV.RBR.CB30.0010                                         | L.CV.RBR.THO4.GEN | —                 |
| A.CV.RBR.CB40.BEM | GC thép dầm CB400 D12-18   |   kg   | thép, dầm                  | rebar CB400 beam           | M.CV.RBR.CB40.0016; M.CV.RBR.CB40.0018                     | L.CV.RBR.THO4.GEN | —                 |
| A.CV.RBR.CB50.BEM | GC thép dầm CB500 D20-32   |   kg   | thép, dầm                  | rebar CB500 beam           | M.CV.RBR.CB50.0025; M.CV.RBR.CB50.0028                     | L.CV.RBR.THO4.GEN | —                 |
| A.CV.RBR.CB24.SLB | GC thép sàn CB240 D≤10     |   kg   | thép, sàn                  | rebar CB240 slab           | M.CV.RBR.CB24.0010                                         | L.CV.RBR.THO3.GEN | —                 |
| A.CV.RBR.CB30.SLB | GC thép sàn CB300 D≤12     |   kg   | thép, sàn                  | rebar CB300 slab           | M.CV.RBR.CB30.0012                                         | L.CV.RBR.THO3.GEN | —                 |
| A.CV.RBR.CB40.WAL | GC thép vách CB400         |   kg   | thép, vách                 | rebar CB400 wall           | M.CV.RBR.CB40.0016; M.CV.RBR.CB40.0020                     | L.CV.RBR.THO4.GEN | —                 |
| A.CV.RBR.CB30.STR | GC thép cầu thang CB300    |   kg   | thép, cầu thang            | rebar CB300 stair          | M.CV.RBR.CB30.0010; M.CV.RBR.CB30.0012                     | L.CV.RBR.THO3.GEN | —                 |
| **A.CV.FWK.xxx**  | **Lắp dựng ván khuôn**     |        |                            |                            |                                                            |                   |                   |
| A.CV.FWK.WOOD.FND | Lắp VK gỗ móng             |   m²   | ván khuôn, coffa, gỗ, móng | timber formwork foundation | M.CV.FWK.WOOD.GEN                                          | L.CV.FWK.THO4.GEN | —                 |
| A.CV.FWK.STEL.FND | Lắp VK thép móng           |   m²   | ván khuôn, thép, móng      | steel formwork foundation  | M.CV.FWK.STEL.GEN                                          | L.CV.FWK.THO4.GEN | E.CV.CRN.TOWE.GEN |
| A.CV.FWK.WOOD.COL | Lắp VK gỗ cột              |   m²   | VK, coffa, cột             | timber formwork column     | M.CV.FWK.WOOD.GEN                                          | L.CV.FWK.THO4.GEN | —                 |
| A.CV.FWK.WOOD.BEM | Lắp VK gỗ dầm              |   m²   | VK, coffa, dầm             | timber formwork beam       | M.CV.FWK.WOOD.GEN                                          | L.CV.FWK.THO4.GEN | —                 |
| A.CV.FWK.WOOD.SLB | Lắp VK gỗ sàn              |   m²   | VK, coffa, sàn             | timber formwork slab       | M.CV.FWK.WOOD.GEN                                          | L.CV.FWK.THO4.GEN | —                 |
| A.CV.FWK.STEL.WAL | Lắp VK thép vách           |   m²   | VK, coffa, vách            | steel formwork wall        | M.CV.FWK.STEL.GEN                                          | L.CV.FWK.THO4.GEN | E.CV.CRN.TOWE.GEN |
| A.CV.FWK.WOOD.STR | Lắp VK gỗ cầu thang        |   m²   | VK, coffa, cầu thang       | timber formwork stair      | M.CV.FWK.WOOD.GEN                                          | L.CV.FWK.THO4.GEN | —                 |
| **A.CV.BSM.xxx**  | **Tường hầm & Chống thấm** |        |                            |                            |                                                            |                   |                   |
| A.CV.BSM.WPRP.MEM | TC chống thấm ngầm         |   m²   | chống thấm, waterproof     | basement waterproofing     | M.CV.WPF.MEMB.GEN                                          | L.CV.WPF.THO4.GEN | —                 |
| A.CV.BSM.DWLL.D08 | TC tường vây D800          |   m²   | tường vây, diaphragm wall  | diaphragm wall D800        | M.CV.CON.M350.GEN                                          | L.CV.PIL.THO4.GEN | E.CV.PIL.GRAB.GEN |
| **A.CV.STL.xxx**  | **Lắp kết cấu thép**       |        |                            |                            |                                                            |                   |                   |
| A.CV.STL.STRH.GEN | Lắp thép hình H/I          |   kg   | thép hình, H, I            | structural steel H/I       | M.CV.STL.STRH.GEN                                          | L.CV.STL.THO5.GEN | E.CV.CRN.MOBI.GEN |
| A.CV.STL.DECK.GEN | Lắp sàn deck thép          |   m²   | sàn deck, steel deck       | steel deck                 | M.CV.STL.DECK.075                                          | L.CV.STL.THO4.GEN | —                 |
| A.CV.STL.STRS.GEN | Lắp cầu thang thép         |   bộ   | cầu thang thép             | steel stair                | M.CV.STL.STRS.GEN                                          | L.CV.STL.THO4.GEN | E.CV.CRN.MOBI.GEN |
| **A.CV.ROF.xxx**  | **Lắp kết cấu mái**        |        |                            |                            |                                                            |                   |                   |
| A.CV.ROF.TRUS.GEN | Lắp giàn thép mái          |   kg   | giàn, dàn mái, truss       | steel roof truss           | M.CV.STL.TRUS.GEN                                          | L.CV.STL.THO4.GEN | E.CV.CRN.MOBI.GEN |
| A.CV.ROF.PURL.GEN | Lắp xà gồ mái              |   kg   | xà gồ, purlin              | roof purlin                | M.CV.STL.PURL.GEN                                          | L.CV.STL.THO4.GEN | —                 |
| A.CV.ROF.BRAC.GEN | Lắp giằng mái              |   kg   | giằng, bracing             | roof bracing               | M.CV.STL.BRAC.GEN                                          | L.CV.STL.THO4.GEN | —                 |

---

## A.AR — HOÀN THIỆN NỘI THẤT (INTERIOR FINISHES)

| CODE              | TÊN CÔNG TÁC                | ĐƠN VỊ | KEYWORDS_VI                | KEYWORDS_EN                 | BOM_M              | BOM_L             | BOM_E |
| :---------------- | :-------------------------- | :----: | :------------------------- | :-------------------------- | :----------------- | :---------------- | :---- |
| **A.AR.WLL.xxx**  | **Xây & trát tường**        |        |                            |                             |                    |                   |       |
| A.AR.WLL.BRCK.100 | Xây gạch tường 100          |   m²   | xây, gạch, tường 10        | brick wall 100mm            | M.AR.WLL.BRCK.0100 | L.AR.WLL.THO4.GEN | —     |
| A.AR.WLL.BRCK.200 | Xây gạch tường 200          |   m²   | xây, gạch, tường 20        | brick wall 200mm            | M.AR.WLL.BRCK.0200 | L.AR.WLL.THO4.GEN | —     |
| A.AR.WLL.AACB.100 | Xây block AAC 100           |   m²   | block, bê tông nhẹ, AAC    | AAC block 100mm             | M.AR.WLL.AACB.0100 | L.AR.WLL.THO3.GEN | —     |
| A.AR.WLL.AACB.150 | Xây block AAC 150           |   m²   | block, AAC                 | AAC block 150mm             | M.AR.WLL.AACB.0150 | L.AR.WLL.THO3.GEN | —     |
| A.AR.WLL.PLST.INT | Trát tường trong            |   m²   | trát, tô, plaster          | internal plastering         | M.AR.WLL.PLST.GEN  | L.AR.WLL.THO4.GEN | —     |
| A.AR.WLL.PUTY.INT | Bả matit tường trong        |   m²   | bả, matit, putty           | putty wall                  | M.AR.WLL.PUTY.GEN  | L.AR.WLL.THO3.GEN | —     |
| A.AR.WLL.GYPB.PAR | Lắp vách thạch cao          |   m²   | thạch cao, gyp, partition  | gypsum partition            | M.AR.WLL.GYPB.0012 | L.AR.CLG.THO4.GEN | —     |
| A.AR.WLL.GLAS.PAR | Lắp vách kính nội bộ        |   m²   | vách kính, glass partition | glass partition             | M.AR.WLL.GLAS.0012 | L.AR.CLG.THO4.GEN | —     |
| **A.AR.CLG.xxx**  | **Trần**                    |        |                            |                             |                    |                   |       |
| A.AR.CLG.GYPB.FLT | Lắp trần thạch cao phẳng    |   m²   | trần, thạch cao            | flat gypsum ceiling         | M.AR.CLG.GYPB.0009 | L.AR.CLG.THO4.GEN | —     |
| A.AR.CLG.GYPB.DRP | Lắp trần thạch cao giật cấp |   m²   | trần, giật cấp             | drop gypsum ceiling         | M.AR.CLG.GYPB.0009 | L.AR.CLG.THO4.GEN | —     |
| A.AR.CLG.ALUM.GEN | Lắp trần nhôm               |   m²   | trần nhôm                  | aluminum ceiling            | M.AR.CLG.ALUM.GEN  | L.AR.CLG.THO4.GEN | —     |
| A.AR.CLG.WOOD.GEN | Lắp trần gỗ                 |   m²   | trần gỗ                    | wood ceiling                | M.AR.CLG.WOOD.GEN  | L.AR.CLG.THO4.GEN | —     |
| A.AR.CLG.PANT.GEN | Sơn trần                    |   m²   | sơn, trần                  | ceiling painting            | M.AR.PNT.INTR.GEN  | L.AR.PNT.THO3.GEN | —     |
| **A.AR.FLR.xxx**  | **Lát nền**                 |        |                            |                             |                    |                   |       |
| A.AR.FLR.CERM.600 | Lát ceramic 600x600         |   m²   | gạch, ceramic, lát nền     | ceramic tile 600            | M.AR.FLR.CERM.0600 | L.AR.FLR.THO4.GEN | —     |
| A.AR.FLR.CERM.800 | Lát ceramic 800x800         |   m²   | gạch, ceramic              | ceramic tile 800            | M.AR.FLR.CERM.0800 | L.AR.FLR.THO4.GEN | —     |
| A.AR.FLR.GRNT.600 | Lát granite 600x600         |   m²   | granite, lát nền           | granite tile 600            | M.AR.FLR.GRNT.0600 | L.AR.FLR.THO4.GEN | —     |
| A.AR.FLR.MARB.GEN | Lát đá marble tự nhiên      |   m²   | đá, marble, stone          | natural marble              | M.AR.FLR.MARB.GEN  | L.AR.FLR.THO5.GEN | —     |
| A.AR.FLR.QRTZ.GEN | Lát đá quartz nhân tạo      |   m²   | đá nhân tạo, quartz        | quartz stone                | M.AR.FLR.QRTZ.GEN  | L.AR.FLR.THO4.GEN | —     |
| A.AR.FLR.LAMI.GEN | Lát sàn gỗ công nghiệp      |   m²   | sàn gỗ, laminate           | laminate flooring           | M.AR.FLR.LAMI.0008 | L.AR.FLR.THO3.GEN | —     |
| A.AR.FLR.HARD.GEN | Lát sàn gỗ tự nhiên         |   m²   | gỗ tự nhiên, hardwood      | hardwood flooring           | M.AR.FLR.HARD.0015 | L.AR.FLR.THO4.GEN | —     |
| A.AR.FLR.VYNL.GEN | Lát sàn vinyl/SPC           |   m²   | vinyl, SPC, nhựa           | vinyl/SPC flooring          | M.AR.FLR.VYNL.0005 | L.AR.FLR.THO3.GEN | —     |
| A.AR.FLR.EPXY.GEN | TC sàn epoxy                |   m²   | epoxy, sơn sàn             | epoxy flooring              | M.AR.FLR.EPXY.GEN  | L.AR.FLR.THO4.GEN | —     |
| **A.AR.TIL.xxx**  | **Ốp tường**                |        |                            |                             |                    |                   |       |
| A.AR.TIL.CERM.WCV | Ốp gạch WC                  |   m²   | ốp, gạch, WC, toilet       | WC wall tile                | M.AR.TIL.CERM.0300 | L.AR.FLR.THO4.GEN | —     |
| A.AR.TIL.STON.DEC | Ốp đá trang trí             |   m²   | ốp đá, stone cladding      | decorative stone            | M.AR.TIL.STON.GEN  | L.AR.FLR.THO5.GEN | —     |
| A.AR.TIL.WOOD.PNL | Ốp gỗ trang trí             |   m²   | ốp gỗ, wood panel          | wood panel cladding         | M.AR.TIL.WOOD.GEN  | L.AR.CLG.THO4.GEN | —     |
| A.AR.TIL.LAMI.CMP | Ốp laminate/compact         |   m²   | laminate, compact          | laminate cladding           | M.AR.TIL.LAMI.GEN  | L.AR.CLG.THO3.GEN | —     |
| **A.AR.PNT.xxx**  | **Sơn nội thất**            |        |                            |                             |                    |                   |       |
| A.AR.PNT.INTR.2CT | Sơn tường trong 2 lớp       |   m²   | sơn, tường trong           | interior wall paint 2 coats | M.AR.PNT.INTR.GEN  | L.AR.PNT.THO3.GEN | —     |
| A.AR.PNT.WPRF.INT | Sơn chống thấm trong        |   m²   | chống thấm, trong          | interior waterproof paint   | M.AR.PNT.WPRF.GEN  | L.AR.PNT.THO3.GEN | —     |
| **A.AR.DOR.xxx**  | **Lắp cửa nội thất**        |        |                            |                             |                    |                   |       |
| A.AR.DOR.WOOD.ROM | Lắp cửa gỗ thông phòng      |   bộ   | cửa gỗ, cửa phòng          | timber room door            | M.AR.DOR.WOOD.0900 | L.AR.DOR.THO4.GEN | —     |
| A.AR.DOR.WOOD.WCV | Lắp cửa gỗ WC               |   bộ   | cửa WC, toilet door        | timber WC door              | M.AR.DOR.WOOD.0700 | L.AR.DOR.THO4.GEN | —     |
| A.AR.DOR.FIRE.GEN | Lắp cửa chống cháy          |   bộ   | chống cháy, fire door      | fire rated door             | M.AR.DOR.FIRE.0900 | L.AR.DOR.THO4.GEN | —     |
| A.AR.DOR.ALGL.INT | Lắp cửa nhôm kính trong     |   bộ   | cửa nhôm, trong            | internal aluminum door      | M.AR.DOR.ALGL.GEN  | L.AR.DOR.THO4.GEN | —     |
| **A.AR.SAN.xxx**  | **Lắp TBVS**                |        |                            |                             |                    |                   |       |
| A.AR.SAN.TOLT.GEN | Lắp bồn cầu                 |   bộ   | bồn cầu, WC, toilet        | toilet installation         | M.AR.SAN.TOLT.GEN  | L.PL.PIP.THO4.GEN | —     |
| A.AR.SAN.BASI.GEN | Lắp lavabo                  |   bộ   | lavabo, chậu rửa           | basin installation          | M.AR.SAN.BASI.GEN  | L.PL.PIP.THO4.GEN | —     |
| A.AR.SAN.SHWR.GEN | Lắp sen tắm                 |   bộ   | sen, vòi sen, shower       | shower installation         | M.AR.SAN.SHWR.GEN  | L.PL.PIP.THO4.GEN | —     |
| A.AR.SAN.BTUB.GEN | Lắp bồn tắm                 |   bộ   | bồn tắm, bathtub           | bathtub installation        | M.AR.SAN.BTUB.GEN  | L.PL.PIP.THO4.GEN | —     |
| A.AR.SAN.ACCS.GEN | Lắp phụ kiện WC             |   bộ   | phụ kiện, accessory        | sanitary accessories        | M.AR.SAN.ACCS.GEN  | L.PL.PIP.THO3.GEN | —     |
| **A.AR.RLG.xxx**  | **Lắp lan can nội thất**    |        |                            |                             |                    |                   |       |
| A.AR.RLG.GLAS.STR | Lắp lan can kính cầu thang  |   md   | lan can, kính, cầu thang   | glass balustrade stair      | M.AR.RLG.GLAS.0012 | L.AR.CLG.THO4.GEN | —     |
| A.AR.RLG.INOX.STR | Lắp lan can inox cầu thang  |   md   | lan can, inox              | stainless balustrade stair  | M.AR.RLG.INOX.GEN  | L.CV.STL.THO4.GEN | —     |
| A.AR.RLG.WOOD.HND | Lắp tay vịn gỗ              |   md   | tay vịn, gỗ                | timber handrail             | M.AR.RLG.WOOD.GEN  | L.AR.DOR.THO4.GEN | —     |

---

## A.EN — MẶT DỰNG (ENVELOPE) · A.EL — ĐIỆN · A.PL — NƯỚC · A.ME — HVAC · A.FP — PCCC · A.LV — ELV · A.VT — THANG MÁY · A.LA — CẢNH QUAN · A.EX — HẠ TẦNG

> 📌 **Cấu trúc bảng giống hệt A.CV, A.AR** — thêm cột `BOM_M`, `BOM_L`, `BOM_E`, `KEYWORDS_EN`.
> Chi tiết các mã A cho EN, EL, PL, ME, FP, LV, VT, LA, EX giữ nguyên nội dung v3.0 với bổ sung:
> - Tách `KEYWORDS` → `KEYWORDS_VI` + `KEYWORDS_EN`
> - Thêm cột `BOM_L` và `BOM_E`
> - Thay wildcard `*` bằng liệt kê cụ thể `;`

### A.EN — MẶT DỰNG & VỎ BAO (ENVELOPE)

| CODE | TÊN CÔNG TÁC | ĐƠN VỊ | KEYWORDS_VI | KEYWORDS_EN | BOM_M | BOM_L | BOM_E |
|:---|:---|:---:|:---|:---|:---|:---|:---|
| **A.EN.CWL.xxx** | **Lắp mặt dựng kính** | | | | | | |
| A.EN.CWL.GLAS.CTW | Lắp vách kính mặt dựng | m² | curtain wall, vách kính | curtain wall glass | M.EN.CWL.GLAS.0012 | L.EN.CWL.THO5.GEN | E.CV.CRN.TOWE.GEN |
| A.EN.CWL.ALGL.WND | Lắp cửa sổ nhôm kính | m² | cửa sổ, window, nhôm kính | aluminum window | M.EN.CWL.ALGL.GEN | L.EN.CWL.THO4.GEN | — |
| A.EN.CWL.ALGL.ENT | Lắp cửa đi nhôm kính | bộ | cửa đi, entrance | aluminum entrance door | M.EN.CWL.ALGL.GEN | L.EN.CWL.THO4.GEN | — |
| **A.EN.CLD.xxx** | **Ốp mặt dựng** | | | | | | |
| A.EN.CLD.ALUM.PNL | Ốp aluminium panel | m² | alu, aluminium, cladding | aluminum cladding | M.EN.CLD.ALUM.0004 | L.EN.CWL.THO4.GEN | — |
| A.EN.CLD.GRNT.EXT | Ốp đá granite ngoài | m² | đá granite, đá treo | exterior granite cladding | M.EN.CLD.GRNT.0030 | L.EN.CWL.THO5.GEN | E.CV.CRN.TOWE.GEN |
| A.EN.CLD.LOVR.GEN | Lắp lam chắn nắng | m² | lam, louver, chắn nắng | sun louver | M.EN.CLD.LOVR.GEN | L.EN.CWL.THO4.GEN | — |
| A.EN.CLD.TERC.EXT | Ốp gốm/terracotta ngoài | m² | gốm, terracotta | terracotta cladding | M.EN.CLD.TERC.GEN | L.EN.CWL.THO4.GEN | — |
| **A.EN.ROF.xxx** | **Lợp mái** | | | | | | |
| A.EN.ROF.METL.GEN | Lợp tôn | m² | tôn, mái tôn | metal roofing | M.EN.ROF.METL.0045 | L.CV.STL.THO4.GEN | — |
| A.EN.ROF.TILE.GEN | Lợp ngói | m² | ngói, mái ngói | tile roofing | M.EN.ROF.TILE.GEN | L.AR.FLR.THO4.GEN | — |
| A.EN.ROF.PCAR.SKY | Lắp tấm lấy sáng | m² | lấy sáng, skylight | polycarbonate skylight | M.EN.ROF.PCAR.GEN | L.CV.STL.THO4.GEN | — |
| A.EN.ROF.GLAS.GEN | Lắp mái kính | m² | mái kính, glass roof | glass roof | M.EN.ROF.GLAS.0012 | L.EN.CWL.THO5.GEN | E.CV.CRN.TOWE.GEN |
| **A.EN.WPF.xxx** | **Chống thấm vỏ** | | | | | | |
| A.EN.WPF.MEMB.ROF | TC chống thấm mái | m² | chống thấm, mái | roof waterproofing | M.EN.WPF.MEMB.GEN | L.CV.WPF.THO4.GEN | — |
| A.EN.WPF.MEMB.BAL | TC chống thấm ban công | m² | chống thấm, ban công | balcony waterproofing | M.EN.WPF.MEMB.GEN | L.CV.WPF.THO4.GEN | — |
| A.EN.WPF.MEMB.GUT | TC chống thấm sênô | m² | sênô, máng nước | gutter waterproofing | M.EN.WPF.MEMB.GEN | L.CV.WPF.THO4.GEN | — |
| **A.EN.INS.xxx** | **Cách nhiệt** | | | | | | |
| A.EN.INS.FOAM.ROF | TC cách nhiệt mái | m² | cách nhiệt, mái | roof insulation | M.EN.INS.FOAM.0050 | L.CV.WPF.THO3.GEN | — |
| A.EN.INS.FOAM.WAL | TC cách nhiệt tường | m² | cách nhiệt, tường | wall insulation | M.EN.INS.FOAM.0025 | L.CV.WPF.THO3.GEN | — |
| **A.EN.PNT.xxx** | **Sơn ngoài** | | | | | | |
| A.EN.PNT.EXTR.GEN | Sơn tường ngoài | m² | sơn ngoài | exterior paint | M.EN.PNT.EXTR.GEN | L.AR.PNT.THO3.GEN | — |
| **A.EN.RLG.xxx** | **Lan can ngoại thất** | | | | | | |
| A.EN.RLG.GLAS.BAL | Lắp lan can kính ban công | md | lan can, kính, ban công | glass balustrade balcony | M.EN.RLG.GLAS.0012 | L.AR.CLG.THO4.GEN | — |
| A.EN.RLG.STEL.BAL | Lắp lan can sắt ban công | md | lan can, sắt, ban công | steel balustrade balcony | M.EN.RLG.STEL.GEN | L.CV.STL.THO4.GEN | — |

---

### A.EL — HỆ THỐNG ĐIỆN (ELECTRICAL)

| CODE | TÊN CÔNG TÁC | ĐƠN VỊ | KEYWORDS_VI | KEYWORDS_EN | BOM_M | BOM_L | BOM_E |
|:---|:---|:---:|:---|:---|:---|:---|:---|
| **A.EL.PNL.xxx** | **Lắp tủ điện** | | | | | | |
| A.EL.PNL.STEL.MSB | Lắp tủ điện tổng MSB | bộ | MSB, tủ tổng | main switchboard | M.EL.PNL.STEL.MSB | L.EL.PNL.THO5.GEN | E.CV.CRN.MOBI.GEN |
| A.EL.PNL.STEL.DB0 | Lắp tủ điện tầng DB | bộ | DB, tủ tầng | distribution board | M.EL.PNL.STEL.DB0 | L.EL.PNL.THO4.GEN | — |
| A.EL.PNL.STEL.CTR | Lắp tủ điều khiển | bộ | tủ điều khiển | control panel | M.EL.PNL.STEL.CTR | L.EL.PNL.THO5.GEN | — |
| **A.EL.CBL.xxx** | **Kéo cáp điện** | | | | | | |
| A.EL.CBL.XLPE.MAN | Kéo cáp nguồn chính | md | cáp nguồn, main cable | main power cable | M.EL.CBL.XLPE.0120 | L.EL.CBL.THO4.GEN | — |
| A.EL.CBL.XLPE.BRC | Kéo cáp nhánh | md | cáp nhánh, branch cable | branch cable | M.EL.CBL.XLPE.0035 | L.EL.CBL.THO3.GEN | — |
| A.EL.CBL.PVC0.GEN | Kéo dây điện đơn | md | dây điện, wire | single wire | M.EL.CBL.PVC0.0004 | L.EL.CBL.THO3.GEN | — |
| **A.EL.CDT.xxx** | **Lắp ống luồn dây** | | | | | | |
| A.EL.CDT.GALV.GEN | Lắp ống thép GI | md | ống thép, conduit, GI | GI conduit | M.EL.CDT.GALV.0025 | L.EL.CBL.THO3.GEN | — |
| A.EL.CDT.PVCR.GEN | Lắp ống PVC điện | md | ống nhựa, PVC conduit | PVC conduit | M.EL.CDT.PVCR.0020 | L.EL.CBL.THO3.GEN | — |
| A.EL.CDT.TRAY.GEN | Lắp máng cáp | md | máng cáp, cable tray | cable tray | M.EL.CDT.TRAY.0200 | L.EL.CBL.THO4.GEN | — |
| **A.EL.SWG.xxx** | **Lắp thiết bị đóng cắt** | | | | | | |
| A.EL.SWG.MCCB.GEN | Lắp MCCB | cái | aptomat, CB, breaker | MCCB circuit breaker | M.EL.SWG.MCCB.GEN | L.EL.PNL.THO4.GEN | — |
| A.EL.SWG.OUTL.GEN | Lắp ổ cắm điện | cái | ổ cắm, outlet, socket | power outlet | M.EL.SWG.OUTL.GEN | L.EL.CBL.THO3.GEN | — |
| A.EL.SWG.SWCH.GEN | Lắp công tắc | cái | công tắc, switch | light switch | M.EL.SWG.SWCH.GEN | L.EL.CBL.THO3.GEN | — |
| **A.EL.LGT.xxx** | **Lắp đèn** | | | | | | |
| A.EL.LGT.LED0.PNL | Lắp đèn LED panel | bộ | đèn LED, panel | LED panel light | M.EL.LGT.LED0.0018 | L.EL.CBL.THO3.GEN | — |
| A.EL.LGT.LED0.TUB | Lắp đèn LED tuýp | bộ | đèn tuýp, tube | LED tube light | M.EL.LGT.LED0.0036 | L.EL.CBL.THO3.GEN | — |
| A.EL.LGT.LED0.DEC | Lắp đèn trang trí | bộ | đèn trang trí | decorative light | M.EL.LGT.LED0.DEC | L.EL.CBL.THO3.GEN | — |
| A.EL.LGT.LED0.EXT | Lắp đèn exit/emergency | bộ | đèn exit, khẩn cấp | exit/emergency light | M.EL.LGT.LED0.0003 | L.EL.CBL.THO3.GEN | — |
| **A.EL.GRD.xxx** | **Chống sét & tiếp địa** | | | | | | |
| A.EL.GRD.COPR.ROD | Lắp kim thu sét | bộ | kim thu sét | lightning rod | M.EL.GRD.COPR.LRD | L.EL.CBL.THO4.GEN | — |
| A.EL.GRD.COPR.WIR | Kéo dây tiếp địa | md | tiếp địa, grounding | grounding wire | M.EL.GRD.COPR.0050 | L.EL.CBL.THO3.GEN | — |
| A.EL.GRD.COPR.GRD | Đóng cọc tiếp địa | cọc | cọc tiếp địa | ground rod | M.EL.GRD.COPR.ROD | L.EL.CBL.THO3.GEN | — |
| **A.EL.PWR.xxx** | **Nguồn dự phòng** | | | | | | |
| A.EL.PWR.GNRT.GEN | Lắp máy phát điện | bộ | máy phát, generator | diesel generator | M.EL.PWR.GNRT.GEN | L.EL.PNL.THO5.GEN | E.CV.CRN.MOBI.GEN |
| A.EL.PWR.ATSS.GEN | Lắp tủ ATS | bộ | ATS, chuyển nguồn | automatic transfer switch | M.EL.PWR.ATSS.GEN | L.EL.PNL.THO4.GEN | — |
| A.EL.PWR.UPSS.GEN | Lắp UPS | bộ | UPS, lưu điện | UPS system | M.EL.PWR.UPSS.GEN | L.EL.PNL.THO4.GEN | — |

---

### A.PL — CẤP THOÁT NƯỚC (PLUMBING)

| CODE | TÊN CÔNG TÁC | ĐƠN VỊ | KEYWORDS_VI | KEYWORDS_EN | BOM_M | BOM_L | BOM_E |
|:---|:---|:---:|:---|:---|:---|:---|:---|
| **A.PL.PIP.xxx** | **Lắp ống nước** | | | | | | |
| A.PL.PIP.PPR0.SUP | Lắp ống PPR cấp nước | md | PPR, cấp nước | PPR supply pipe | M.PL.PIP.PPR0.0025; M.PL.PIP.PPR0.0032 | L.PL.PIP.THO4.GEN | — |
| A.PL.PIP.HDPE.SUP | Lắp ống HDPE cấp nước | md | HDPE, ống nhựa | HDPE supply pipe | M.PL.PIP.HDPE.0063 | L.PL.PIP.THO4.GEN | E.PL.PIP.WELD.GEN |
| A.PL.PIP.GALV.SUP | Lắp ống thép mạ kẽm | md | thép mạ, galvanized | galvanized steel pipe | M.PL.PIP.GALV.0050 | L.PL.PIP.THO4.GEN | — |
| A.PL.PIP.INOX.SUP | Lắp ống inox | md | inox, stainless | stainless steel pipe | M.PL.PIP.INOX.0050 | L.PL.PIP.THO4.GEN | — |
| A.PL.PIP.PVCD.DRN | Lắp ống PVC thoát | md | PVC, thoát, drainage | PVC drain pipe | M.PL.PIP.PVCD.0110; M.PL.PIP.PVCD.0160 | L.PL.PIP.THO3.GEN | — |
| A.PL.PIP.HDPE.DRN | Lắp ống HDPE thoát | md | HDPE thoát | HDPE drain pipe | M.PL.PIP.HDPE.0160 | L.PL.PIP.THO4.GEN | E.PL.PIP.WELD.GEN |
| A.PL.PIP.CAST.DRN | Lắp ống gang thoát | md | gang, cast iron | cast iron drain pipe | M.PL.PIP.CAST.0100 | L.PL.PIP.THO4.GEN | — |
| **A.PL.FTG.xxx** | **Lắp phụ kiện ống** | | | | | | |
| A.PL.FTG.PPR0.SUP | Lắp phụ kiện cấp PPR | bộ | co, tê, nối, cấp | PPR fittings | M.PL.FTG.PPR0.GEN | L.PL.PIP.THO3.GEN | — |
| A.PL.FTG.PVCD.DRN | Lắp phụ kiện thoát PVC | bộ | co, tê, nối, thoát | PVC drain fittings | M.PL.FTG.PVCD.GEN | L.PL.PIP.THO3.GEN | — |
| A.PL.FTG.BRAS.VLV | Lắp van đồng | cái | van, valve | brass valve | M.PL.FTG.BRAS.GEN | L.PL.PIP.THO4.GEN | — |
| **A.PL.PMP.xxx** | **Lắp bơm** | | | | | | |
| A.PL.PMP.CENT.SUP | Lắp bơm cấp nước | bộ | bơm cấp, water pump | water supply pump | M.PL.PMP.CENT.GEN | L.PL.PIP.THO4.GEN | — |
| A.PL.PMP.BSTR.GEN | Lắp bơm tăng áp | bộ | bơm tăng áp, booster | booster pump | M.PL.PMP.BSTR.GEN | L.PL.PIP.THO4.GEN | — |
| A.PL.PMP.SUBM.SEW | Lắp bơm bể phốt | bộ | bơm bể phốt | sewage pump | M.PL.PMP.SUBM.GEN | L.PL.PIP.THO4.GEN | — |
| **A.PL.TNK.xxx** | **TC bể chứa** | | | | | | |
| A.PL.TNK.CONC.UGN | TC bể nước ngầm BTCT | m³ | bể ngầm | underground RC tank | M.CV.CON.M300.GEN | L.CV.CON.THO4.GEN | E.CV.CON.PUMP.GEN |
| A.PL.TNK.INOX.ROF | Lắp bể nước mái inox | m³ | bể mái, roof tank | roof stainless tank | M.PL.TNK.INOX.GEN | L.PL.PIP.THO4.GEN | E.CV.CRN.MOBI.GEN |
| A.PL.TNK.CONC.SEP | TC bể tự hoại | m³ | bể phốt, septic tank | septic tank | M.CV.CON.M250.GEN | L.CV.CON.THO3.GEN | — |

---

### A.ME — HVAC · A.FP — PCCC · A.LV — ELV · A.VT — THANG MÁY · A.LA — CẢNH QUAN · A.EX — HẠ TẦNG

> 📌 Tất cả mã M cho EN, EL, PL, ME, FP, LV, VT, LA, EX **giữ nguyên v3.0**.  
> Bổ sung cột `WASTE_%` và `KEYWORDS_EN` khi triển khai SQL/CSV.

---
---

# BẢNG M — MASTER RESOURCE DICTIONARY (MATERIAL CODE TABLE)

> **Mục đích:** Mua sắm (Procurement), Kho bãi (Warehouse), Quản lý tồn kho FIFO/LIFO.  
> **Nguyên tắc TUYỆT ĐỐI:**
> - Mô tả **vật tư vật lý** có thể mua, nhận, lưu kho.
> - **KHÔNG** có vị trí thi công, hành động, nhân công, hay máy móc.
> - Thép CB300 ɸ10 là **1 mã duy nhất**, dù dùng cho móng, cột, hay dầm.

> **Cột bảng chuẩn hóa:**

| Cột | Kiểu | Ý nghĩa |
|:---|:---:|:---|
| `CODE` | string | Mã Material 3-level (ref_code) |
| `TÊN VẬT TƯ` | string | Mô tả vật tư vật lý |
| `ĐƠN VỊ` | enum | Đơn vị chuẩn hóa |
| `WASTE_%` | float | Hệ số hao hụt chuẩn (%) |
| `KEYWORDS_VI` | string | Từ khóa tiếng Việt |
| `KEYWORDS_EN` | string | Từ khóa tiếng Anh |

---

## M.CV — VẬT TƯ XÂY DỰNG (CIVIL MATERIALS)

### Bê tông thương phẩm

| CODE | TÊN VẬT TƯ | ĐƠN VỊ | WASTE_% | KEYWORDS_VI | KEYWORDS_EN |
|:---|:---|:---:|:---:|:---|:---|
| M.CV.CON.M100.GEN | BT thương phẩm M100 | m³ | 3 | BT, mác 100, lean | concrete M100, lean |
| M.CV.CON.M150.GEN | BT thương phẩm M150 | m³ | 3 | BT, mác 150 | concrete M150 |
| M.CV.CON.M200.GEN | BT thương phẩm M200 | m³ | 3 | BT, mác 200 | concrete M200 |
| M.CV.CON.M250.GEN | BT thương phẩm M250 | m³ | 3 | BT, mác 250 | concrete M250 |
| M.CV.CON.M300.GEN | BT thương phẩm M300 | m³ | 3 | BT, mác 300 | concrete M300 |
| M.CV.CON.M350.GEN | BT thương phẩm M350 | m³ | 3 | BT, mác 350 | concrete M350 |
| M.CV.CON.M400.GEN | BT thương phẩm M400 | m³ | 3 | BT, mác 400 | concrete M400 |

### Cốt thép xây dựng

> ⚠️ Thép CB300 ɸ10 dùng cho móng, cột, hay dầm đều là **1 mã M duy nhất**.

| CODE | TÊN VẬT TƯ | ĐƠN VỊ | WASTE_% | KEYWORDS_VI | KEYWORDS_EN |
|:---|:---|:---:|:---:|:---|:---|
| M.CV.RBR.CB24.0006 | Thép cuộn CB240 ɸ6 | kg | 5 | thép, CB240, phi 6, cuộn | rebar CB240 D6, coil |
| M.CV.RBR.CB24.0008 | Thép cuộn CB240 ɸ8 | kg | 5 | thép, CB240, phi 8, cuộn | rebar CB240 D8, coil |
| M.CV.RBR.CB24.0010 | Thép cuộn CB240 ɸ10 | kg | 5 | thép, CB240, phi 10 | rebar CB240 D10 |
| M.CV.RBR.CB30.0010 | Thép vằn CB300 ɸ10 | kg | 3 | thép, CB300, phi 10, vằn | deformed bar CB300 D10 |
| M.CV.RBR.CB30.0012 | Thép vằn CB300 ɸ12 | kg | 3 | thép, CB300, phi 12 | deformed bar CB300 D12 |
| M.CV.RBR.CB30.0014 | Thép vằn CB300 ɸ14 | kg | 3 | thép, CB300, phi 14 | deformed bar CB300 D14 |
| M.CV.RBR.CB40.0016 | Thép vằn CB400 ɸ16 | kg | 2 | thép, CB400, phi 16 | deformed bar CB400 D16 |
| M.CV.RBR.CB40.0018 | Thép vằn CB400 ɸ18 | kg | 2 | thép, CB400, phi 18 | deformed bar CB400 D18 |
| M.CV.RBR.CB40.0020 | Thép vằn CB400 ɸ20 | kg | 2 | thép, CB400, phi 20 | deformed bar CB400 D20 |
| M.CV.RBR.CB40.0022 | Thép vằn CB400 ɸ22 | kg | 2 | thép, CB400, phi 22 | deformed bar CB400 D22 |
| M.CV.RBR.CB50.0025 | Thép vằn CB500 ɸ25 | kg | 2 | thép, CB500, phi 25 | deformed bar CB500 D25 |
| M.CV.RBR.CB50.0028 | Thép vằn CB500 ɸ28 | kg | 2 | thép, CB500, phi 28 | deformed bar CB500 D28 |
| M.CV.RBR.CB50.0032 | Thép vằn CB500 ɸ32 | kg | 2 | thép, CB500, phi 32 | deformed bar CB500 D32 |

### Ván khuôn

| CODE | TÊN VẬT TƯ | ĐƠN VỊ | WASTE_% | KEYWORDS_VI | KEYWORDS_EN |
|:---|:---|:---:|:---:|:---|:---|
| M.CV.FWK.WOOD.GEN | Ván khuôn gỗ (bao gồm PK) | m² | 15 | ván khuôn, coffa, gỗ | timber formwork |
| M.CV.FWK.STEL.GEN | Ván khuôn thép (bao gồm PK) | m² | 5 | ván khuôn, coffa, thép | steel formwork |

### Kết cấu thép

| CODE | TÊN VẬT TƯ | ĐƠN VỊ | WASTE_% | KEYWORDS_VI | KEYWORDS_EN |
|:---|:---|:---:|:---:|:---|:---|
| M.CV.STL.STRH.GEN | Thép hình H/I kết cấu | kg | 5 | thép hình, H, I | structural steel H/I |
| M.CV.STL.DECK.075 | Tôn sàn deck 0.75mm | m² | 5 | sàn deck | steel deck 0.75mm |
| M.CV.STL.STRS.GEN | Lắp cầu thang thép | bộ | 0 | cầu thang thép | steel staircase |
| M.CV.STL.TRUS.GEN | Thép giàn mái | kg | 5 | giàn, dàn mái, truss | steel roof truss |
| M.CV.STL.PURL.GEN | Xà gồ thép mái | kg | 5 | xà gồ, purlin | steel purlin |
| M.CV.STL.BRAC.GEN | Giằng thép mái | kg | 5 | giằng, bracing | steel bracing |

### Chống thấm

| CODE | TÊN VẬT TƯ | ĐƠN VỊ | WASTE_% | KEYWORDS_VI | KEYWORDS_EN |
|:---|:---|:---:|:---:|:---|:---|
| M.CV.WPF.MEMB.GEN | Màng chống thấm (membrane) | m² | 10 | chống thấm, waterproof | waterproof membrane |

---

## M.AR — VẬT TƯ HOÀN THIỆN (ARCHITECTURE MATERIALS)

*(Giữ nguyên tất cả mã M.AR từ v3.0, bổ sung cột `WASTE_%` và `KEYWORDS_EN`)*

### Vật liệu tường

| CODE | TÊN VẬT TƯ | ĐƠN VỊ | WASTE_% | KEYWORDS_VI | KEYWORDS_EN |
|:---|:---|:---:|:---:|:---|:---|
| M.AR.WLL.BRCK.0100 | Gạch nung 100mm | viên | 5 | gạch, nung, 100 | clay brick 100mm |
| M.AR.WLL.BRCK.0200 | Gạch nung 200mm | viên | 5 | gạch, nung, 200 | clay brick 200mm |
| M.AR.WLL.AACB.0100 | Gạch AAC block 100mm | viên | 3 | AAC, block, bê tông nhẹ | AAC block 100mm |
| M.AR.WLL.AACB.0150 | Gạch AAC block 150mm | viên | 3 | AAC, block, 150 | AAC block 150mm |
| M.AR.WLL.PLST.GEN | Vữa trát tường | kg | 10 | vữa, trát, plaster | plastering mortar |
| M.AR.WLL.PUTY.GEN | Bột bả matit | kg | 10 | matit, putty, bả | wall putty |
| M.AR.WLL.GYPB.0009 | Tấm thạch cao 9mm | tấm | 5 | thạch cao, gypsum, 9mm | gypsum board 9mm |
| M.AR.WLL.GYPB.0012 | Tấm thạch cao 12mm | tấm | 5 | thạch cao, gypsum, 12mm | gypsum board 12mm |
| M.AR.WLL.GLAS.0012 | Kính cường lực 12mm | m² | 3 | kính, cường lực, 12mm | tempered glass 12mm |

### Vật liệu trần · Sàn · Ốp · Sơn · Cửa · TBVS · Lan can

*(Nội dung mã giữ nguyên v3.0 — bổ sung `WASTE_%` 3-10% tùy loại, thêm `KEYWORDS_EN`)*

---

## M.EN · M.EL · M.PL · M.ME · M.FP · M.LV · M.VT · M.LA · M.EX

> 📌 Tất cả mã M cho EN, EL, PL, ME, FP, LV, VT, LA, EX **giữ nguyên v3.0**.  
> Bổ sung cột `WASTE_%` và `KEYWORDS_EN` khi triển khai SQL/CSV.

---
---

# BẢNG L — MASTER LABOUR DICTIONARY (NHÂN CÔNG)

> **Mục đích:** Tính đơn giá nhân công, định mức lao động.  
> **Nguyên tắc:**
> - Phân theo bộ môn (L1) và nhóm công tác (L2).
> - L3 = Bậc thợ (THO3 = Thợ bậc 3/7, THO4 = Thợ bậc 4/7, THO5 = Thợ bậc 5/7, OPER = Vận hành máy).
> - L4 = `GEN` (chung).

| CODE | TÊN NHÂN CÔNG | ĐƠN VỊ | KEYWORDS_VI | KEYWORDS_EN |
|:---|:---|:---:|:---|:---|
| **L.CV.EXC.xxx** | **NC Công tác đất** | | | |
| L.CV.EXC.THO3.GEN | Thợ đào đất bậc 3/7 | công | thợ, đào đất, bậc 3 | earthwork labourer grade 3 |
| L.CV.EXC.OPER.GEN | Thợ vận hành máy đào | công | vận hành, máy đào, lái máy | excavator operator |
| **L.CV.CON.xxx** | **NC Đổ bê tông** | | | |
| L.CV.CON.THO3.GEN | Thợ bê tông bậc 3/7 | công | thợ, bê tông, bậc 3 | concrete worker grade 3 |
| L.CV.CON.THO4.GEN | Thợ bê tông bậc 4/7 | công | thợ, bê tông, bậc 4 | concrete worker grade 4 |
| **L.CV.RBR.xxx** | **NC Cốt thép** | | | |
| L.CV.RBR.THO3.GEN | Thợ sắt bậc 3/7 | công | thợ sắt, cốt thép, bậc 3 | rebar worker grade 3 |
| L.CV.RBR.THO4.GEN | Thợ sắt bậc 4/7 | công | thợ sắt, cốt thép, bậc 4 | rebar worker grade 4 |
| **L.CV.FWK.xxx** | **NC Ván khuôn** | | | |
| L.CV.FWK.THO4.GEN | Thợ ván khuôn bậc 4/7 | công | thợ VK, coffa, bậc 4 | formwork carpenter grade 4 |
| **L.CV.PIL.xxx** | **NC Cọc móng** | | | |
| L.CV.PIL.THO4.GEN | Thợ cọc bậc 4/7 | công | thợ cọc, khoan nhồi | piling worker grade 4 |
| **L.CV.STL.xxx** | **NC Kết cấu thép** | | | |
| L.CV.STL.THO4.GEN | Thợ lắp thép bậc 4/7 | công | thợ thép hình, lắp dựng | steel erector grade 4 |
| L.CV.STL.THO5.GEN | Thợ lắp thép bậc 5/7 | công | thợ thép hình, bậc 5 | steel erector grade 5 |
| **L.CV.WPF.xxx** | **NC Chống thấm** | | | |
| L.CV.WPF.THO3.GEN | Thợ chống thấm bậc 3/7 | công | chống thấm, bậc 3 | waterproofing worker grade 3 |
| L.CV.WPF.THO4.GEN | Thợ chống thấm bậc 4/7 | công | chống thấm, bậc 4 | waterproofing worker grade 4 |
| **L.AR.WLL.xxx** | **NC Xây trát** | | | |
| L.AR.WLL.THO3.GEN | Thợ xây bậc 3/7 | công | thợ xây, bậc 3 | bricklayer grade 3 |
| L.AR.WLL.THO4.GEN | Thợ xây bậc 4/7 | công | thợ xây, bậc 4 | bricklayer grade 4 |
| **L.AR.FLR.xxx** | **NC Lát ốp** | | | |
| L.AR.FLR.THO3.GEN | Thợ lát bậc 3/7 | công | thợ lát, ốp, bậc 3 | tile setter grade 3 |
| L.AR.FLR.THO4.GEN | Thợ lát bậc 4/7 | công | thợ lát, ốp, bậc 4 | tile setter grade 4 |
| L.AR.FLR.THO5.GEN | Thợ lát đá cao cấp bậc 5/7 | công | thợ lát đá, bậc 5 | stone mason grade 5 |
| **L.AR.CLG.xxx** | **NC Trần & Vách** | | | |
| L.AR.CLG.THO4.GEN | Thợ trần/vách bậc 4/7 | công | thợ trần, thạch cao | ceiling installer grade 4 |
| **L.AR.PNT.xxx** | **NC Sơn** | | | |
| L.AR.PNT.THO3.GEN | Thợ sơn bậc 3/7 | công | thợ sơn, bậc 3 | painter grade 3 |
| **L.AR.DOR.xxx** | **NC Cửa** | | | |
| L.AR.DOR.THO4.GEN | Thợ lắp cửa bậc 4/7 | công | thợ cửa, lắp cửa | door installer grade 4 |
| **L.EN.CWL.xxx** | **NC Mặt dựng** | | | |
| L.EN.CWL.THO4.GEN | Thợ mặt dựng bậc 4/7 | công | thợ mặt dựng, curtain wall | curtain wall installer grade 4 |
| L.EN.CWL.THO5.GEN | Thợ mặt dựng bậc 5/7 | công | thợ mặt dựng, bậc 5 | curtain wall installer grade 5 |
| **L.EL.CBL.xxx** | **NC Điện** | | | |
| L.EL.CBL.THO3.GEN | Thợ điện bậc 3/7 | công | thợ điện, bậc 3 | electrician grade 3 |
| L.EL.CBL.THO4.GEN | Thợ điện bậc 4/7 | công | thợ điện, bậc 4 | electrician grade 4 |
| **L.EL.PNL.xxx** | **NC Tủ điện** | | | |
| L.EL.PNL.THO4.GEN | Thợ lắp tủ điện bậc 4/7 | công | thợ tủ điện, bậc 4 | panel installer grade 4 |
| L.EL.PNL.THO5.GEN | Thợ lắp tủ điện bậc 5/7 | công | thợ tủ điện, bậc 5 | panel installer grade 5 |
| **L.PL.PIP.xxx** | **NC Cấp thoát nước** | | | |
| L.PL.PIP.THO3.GEN | Thợ ống nước bậc 3/7 | công | thợ ống, plumber, bậc 3 | plumber grade 3 |
| L.PL.PIP.THO4.GEN | Thợ ống nước bậc 4/7 | công | thợ ống, plumber, bậc 4 | plumber grade 4 |

---
---

# BẢNG E — MASTER EQUIPMENT DICTIONARY (MÁY MÓC THIẾT BỊ)

> **Mục đích:** Tính đơn giá ca máy, định mức thiết bị cho từng Activity.  
> **Nguyên tắc:**
> - Phân theo bộ môn (L1) và loại máy (L2).
> - L3 = Tên máy viết tắt.
> - L4 = `GEN` (chung) hoặc công suất.

| CODE | TÊN MÁY MÓC | ĐƠN VỊ | KEYWORDS_VI | KEYWORDS_EN |
|:---|:---|:---:|:---|:---|
| **E.CV.EXC.xxx** | **Máy đào & San** | | | |
| E.CV.EXC.EXCA.GEN | Máy đào bánh xích (≤1.2m³) | ca | máy đào, excavator | crawler excavator |
| E.CV.EXC.BULL.GEN | Máy ủi D6 | ca | máy ủi, bulldozer | bulldozer D6 |
| E.CV.EXC.COMP.GEN | Máy đầm lu rung | ca | đầm lu, lu rung | vibratory roller |
| E.CV.EXC.TRUK.GEN | Xe tải tự đổ 10T | ca | xe tải, tự đổ | dump truck 10T |
| **E.CV.CON.xxx** | **Máy bê tông** | | | |
| E.CV.CON.PUMP.GEN | Máy bơm bê tông cần | ca | bơm BT, concrete pump | concrete boom pump |
| E.CV.CON.VIBR.GEN | Đầm dùi bê tông | ca | đầm dùi, vibrator | concrete vibrator |
| E.CV.CON.MIXR.GEN | Xe trộn bê tông 6m³ | ca | xe trộn, mixer truck | concrete mixer truck |
| **E.CV.PIL.xxx** | **Máy ép cọc** | | | |
| E.CV.PIL.JACK.GEN | Máy ép cọc thủy lực | ca | máy ép, hydraulic jack | hydraulic pile press |
| E.CV.PIL.HAMR.GEN | Búa đóng cọc diesel | ca | búa đóng, diesel hammer | diesel pile hammer |
| E.CV.PIL.BRIG.GEN | Máy khoan nhồi | ca | máy khoan, bored pile rig | bored pile drilling rig |
| E.CV.PIL.GRAB.GEN | Gầu đào tường vây | ca | gầu đào, diaphragm grab | diaphragm wall grab |
| E.CV.PIL.MIXR.GEN | Máy trộn xi măng đất | ca | trộn xi măng đất | soil cement mixing rig |
| **E.CV.CRN.xxx** | **Cẩu** | | | |
| E.CV.CRN.TOWE.GEN | Cẩu tháp | ca | cẩu tháp, tower crane | tower crane |
| E.CV.CRN.MOBI.GEN | Cẩu bánh lốp 25T | ca | cẩu bánh lốp, mobile crane | mobile crane 25T |
| **E.PL.PIP.xxx** | **Máy hàn ống** | | | |
| E.PL.PIP.WELD.GEN | Máy hàn ống HDPE | ca | hàn ống, HDPE welder | HDPE pipe fusion welder |

---
---

# PHỤ LỤC

## A. BẢNG SO SÁNH MÃ CŨ → MỚI

| Mã v2.0 | Mã v4.0 (5-level) | Mã v4.1 (3-level ref) | Instance + Attributes | Ghi chú |
|:---|:---|:---|:---|:---|
| CV.RBR.CB30.D010.FND0 | A.CV.RBR.CB30.FND | A.RBAR.DFM | A.RBAR.DFM-001 discipline=CV, location=FND, spec_grade=CB300 | Discipline + location → attributes |
| CV.RBR.CB30.D010.COL0 | A.CV.RBR.CB30.COL | A.RBAR.DFM | A.RBAR.DFM-002 discipline=CV, location=COL, spec_grade=CB300 | Same ref code, different instance |
| CV.EXC.MACH.0000.M3V0 | A.CV.EXC.MACH.GEN | A.EXCV.MCH | A.EXCV.MCH-001 discipline=CV | Hành động đào đất |
| CV.CON.M300.0000.COL0 | A.CV.CON.M300.COL | A.CONC.STR | A.CONC.STR-001 discipline=CV, location=COL, spec_grade=M300 | Đầy đủ attributes |

## B. MÔ HÌNH LIÊN KẾT N:M (BOM — Bill of Materials)

```
┌────────────────────────────────────────────────────────────────────┐
│                        BẢNG A (Activity/BOQ)                      │
│  ref_code: A.CONC.STR                                             │
│  instance: A.CONC.STR-001  "Đổ BT cột"                           │
│  attributes: discipline=CV, location=COL, spec_grade=M300         │
│        │                                                           │
│        ├──►  BOM_M: M.CONC.GEN          × 1.03 (waste 3%)        │
│        ├──►  BOM_L: L.CONC.GR4          × 0.35 (công/m³)         │
│        └──►  BOM_E: E.CONC.PMP          × 0.02 (ca/m³)           │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  MÔ HÌNH QUAN HỆ 1:N (Reference → Instance)                      │
│                                                                    │
│  A.CONC.STR (BT kết cấu) ─────► Instances:                       │
│     • A.CONC.STR-001  discipline=CV  location=COL  M300           │
│     • A.CONC.STR-002  discipline=CV  location=BEM  M300           │
│     • A.CONC.STR-003  discipline=CV  location=SLB  M250           │
│     • A.CONC.STR-004  discipline=CV  location=SHW  M350           │
│                                                                    │
│  A.CONC.LEA (BT lót) ─────► Instances:                            │
│     • A.CONC.LEA-001  discipline=CV  location=FND  M100           │
│                                                                    │
│  M.CONC.GEN (BT thương phẩm) ──► Dùng bởi:                      │
│     • A.CONC.STR-001, A.CONC.STR-002, A.CONC.LEA-001             │
│                                                                    │
│  ► Thủ kho quản lý 1 mã M. HR quản lý 1 mã L. Thiết bị 1 mã E. │
│  ► Mã ngắn gọn, chi tiết nằm trong attributes.                   │
└────────────────────────────────────────────────────────────────────┘
```

## C. MAPPING ĐƠN VỊ TÍNH CHUẨN

> ⚠️ Đơn vị tính là **Attribute**, nằm ở **cột riêng**, KHÔNG nhúng vào mã ID.

| Input variants | Chuẩn hóa | Ghi chú |
|:---|:---:|:---|
| m³, m3, mét khối, M3, khối | **m³** | Bê tông, đất, bể |
| m², m2, mét vuông, M2 | **m²** | Ván khuôn, ốp lát, sơn |
| md, m, ml, mét dài | **md** | Ống, cáp, lan can |
| kg, KG, Kg, kilogram | **kg** | Thép, kết cấu |
| tấn, T, tan | **tấn** | Asphalt, thép hình lớn |
| cái, Cái, CÁI, c | **cái** | Thiết bị rời, đầu báo |
| bộ, Bộ, BỘ, set | **bộ** | Thiết bị lắp, cửa, tủ |
| hệ thống, HT, trọn gói | **TT** | Gói thầu, hệ thống |
| %, phần trăm | **%** | Dự phòng |
| lít, L, lit | **lít** | Sơn |
| viên, v | **viên** | Gạch |
| tấm, sheet | **tấm** | Thạch cao, tôn |
| bình | **bình** | Bình chữa cháy |
| cây, cây | **cây** | Cây xanh |
| công | **công** | **MỚI** — Nhân công (1 công = 8h) |
| ca | **ca** | **MỚI** — Ca máy (1 ca = 8h) |
| cọc | **cọc** | Thí nghiệm cọc |
| hố | **hố** | Hố ga |
| trạm | **trạm** | Trạm biến áp |
| cột | **cột** | Cột đèn |

## D. QUY TẮC MÃ HÓA 3-LEVEL

| Level | Ý nghĩa | Quy tắc | Ví dụ |
|:---|:---|:---|:---|
| **L0** (PREFIX) | Bảng | 1 char: A, M, L, E | `A`, `M` |
| **L1** (GROUP) | Nhóm công tác / vật tư | 3-4 char UPPERCASE | CONC, RBAR, PIPE, CABL |
| **L2** (TYPE) | Phân loại phụ | 3 char UPPERCASE | STR, LEA, FND, GEN, GR3 |

> **Discipline, Location, Spec** nay là attributes trên `master_work_items`, không nằm trong mã.

| Attribute | Lưu ở | Ví dụ |
|:---|:---|:---|
| Discipline (bộ môn) | `master_work_items.discipline` | CV, AR, EL, PL |
| Location (vị trí) | `master_work_items.location` | COL, FND, BEM, SLB, GEN |
| Spec grade | `master_work_items.spec_grade` | M300, CB400, PN16 |
| Spec material | `master_work_items.spec_material` | Cu/XLPE/PVC, HDPE |
| Spec dimension | `master_work_items.spec_dimension` | D110, 600x600 |

## E. TỪ ĐIỂN VIẾT TẮT GROUP / TYPE (ABBREVIATION DICTIONARY)

### Viết tắt GROUP (L1 — Nhóm)

| GROUP (v4.1) | Cũ (v4.0) | Tiếng Việt | English |
|:---:|:---:|:---|:---|
| CONC | CON | Bê tông | Concrete |
| RBAR | RBR | Cốt thép | Rebar |
| FWRK | FWK | Ván khuôn | Formwork |
| EXCV | EXC | Đào đất | Excavation |
| PILE | PIL | Cọc móng | Piling |
| STLS | STL | Kết cấu thép | Structural Steel |
| ROOF | ROF | Mái | Roofing |
| BSMT | BSM | Tường hầm | Basement |
| WALL | WLL | Tường | Wall |
| CEIL | CLG | Trần | Ceiling |
| FLOR | FLR | Sàn | Floor |
| TILE | TIL | Ốp tường | Wall Tile |
| PANT | PNT | Sơn | Paint |
| DOOR | DOR | Cửa | Door |
| SNTY | SAN | Thiết bị vệ sinh | Sanitary |
| RAIL | RLG | Lan can | Railing |
| CWAL | CWL | Mặt dựng kính | Curtain Wall |
| CLAD | CLD | Ốp ngoài | Cladding |
| WTPF | WPF | Chống thấm | Waterproofing |
| INSL | INS | Cách nhiệt | Insulation |
| PANL | PNL | Tủ điện | Panel |
| CABL | CBL | Cáp điện | Cable |
| CNDT | CDT | Ống luồn dây | Conduit |
| SWGR | SWG | Đóng cắt | Switchgear |
| LITE | LGT | Đèn | Lighting |
| GRND | GRD | Tiếp địa | Grounding |
| POWR | PWR | Nguồn điện | Power |
| PIPE | PIP | Ống nước | Piping |
| FITG | FTG | Phụ kiện ống | Fitting |
| PUMP | PMP | Bơm | Pump |
| TANK | TNK | Bể chứa | Tank |
| HVAC | ACU | Điều hòa | Air Conditioning Unit |
| DUCT | DCT | Ống gió | Duct |
| FANS | FAN | Quạt | Fan |
| COOL | CLT | Tháp giải nhiệt | Cooling Tower |
| DETC | DET | Báo cháy | Detection |
| SPRK | SPR | Sprinkler | Sprinkler |
| GASS | GAS | Chữa cháy khí | Gas Suppression |
| SMOK | SMK | Hút khói | Smoke |
| PASV | PSV | Chống cháy thụ động | Passive Fire |
| NETW | NET | Mạng | Network |
| CCTV | CTV | Camera | CCTV |
| ACCS | ACS | Kiểm soát ra vào | Access Control |
| AUDI | AUD | Âm thanh | Audio |
| BMSS | BMS | Quản lý tòa nhà | Building Management |
| ELEV | ELV | Thang máy | Elevator |
| ESCL | ESC | Thang cuốn | Escalator |
| PLNT | PLT | Cây xanh | Planting |
| PAVE | PAV | Lát đường | Paving |
| FEAT | FTR | Tiểu cảnh | Feature |
| POOL | POL | Hồ bơi | Pool |
| FURN | FRN | Tiện ích | Furniture |
| GRAD | GRD | San nền | Grading |
| ROAD | ROD | Đường | Road |
| DRAN | DRN | Thoát nước | Drainage |
| FNCE | FNC | Hàng rào | Fence |
| PARK | PRK | Bãi đỗ xe | Parking |
| CRAN | CRN | Cẩu | Crane |

### Viết tắt TYPE (L2) phổ biến

| TYPE | Ý nghĩa | Dùng cho |
|:---:|:---|:---|
| STR | Structural / Kết cấu | A: BT kết cấu, thép kết cấu |
| LEA | Lean / Lót | A: BT lót |
| FND | Foundation / Móng | A: Công tác móng |
| GEN | General / Chung | A, M: Mặc định |
| DFM | Deformed / Vằn | M: Thép vằn |
| RND | Round / Tròn, cuộn | M: Thép cuộn |
| GR3 | Grade 3 / Bậc 3 | L: Thợ bậc 3/7 |
| GR4 | Grade 4 / Bậc 4 | L: Thợ bậc 4/7 |
| GR5 | Grade 5 / Bậc 5 | L: Thợ bậc 5/7 |
| OPR | Operator / Vận hành | L: Thợ vận hành máy |
| PMP | Pump / Bơm | E: Máy bơm |
| VIB | Vibrator / Đầm | E: Đầm dùi |
| MIX | Mixer / Trộn | E: Xe trộn |
| CRN | Crane / Cẩu | E: Cẩu |
| MCH | Machine / Máy | A, E: Đào máy |
| MAN | Manual / Thủ công | A: Đào thủ công |

## F. QUY TẮC QUẢN TRỊ & MỞ RỘNG (GOVERNANCE)

### F.1 Quy trình thêm mã mới

```
1. Người yêu cầu → Lập Phiếu yêu cầu (Code Request Form)
2. Data Steward  → Kiểm tra trùng lặp, validate format 3-level
3. QS Manager    → Xác nhận bảng A (nếu có)
4. Procurement   → Xác nhận bảng M (nếu có)
5. Data Architect→ Duyệt & cập nhật Master Database
6. Thông báo     → Broadcast tới tất cả hệ thống liên quan
```

### F.2 Quy tắc đặt mã

| # | Quy tắc | Vi phạm → |
|:---:|:---|:---|
| 1 | Mã phải đúng 3 phần, ngăn cách bằng `.` | Reject |
| 2 | L0 phải là `A`, `M`, `L`, hoặc `E` | Reject |
| 3 | L1 (GROUP) phải 3-4 char UPPERCASE, nằm trong danh sách | Reject |
| 4 | L2 (TYPE) phải 3 char UPPERCASE | Reject |
| 5 | Discipline phải nằm trong danh sách 12 bộ môn (attribute) | Reject |
| 6 | Mã KHÔNG chứa grade/spec (M300, CB40, XLPE...) | Reject |
| 7 | Mã KHÔNG chứa vị trí (FND, COL, BEM, SLB...) | Reject |
| 8 | Mã KHÔNG chứa discipline (CV, AR, EL...) | Reject |
| 9 | Đơn vị tính phải nằm trong bảng chuẩn hóa (Phụ lục C) | Reject |
| 10 | Instance code phải có format `{REF_CODE}-{SEQ:03d}` | Reject |

### F.3 Versioning

| Field | Format | Ví dụ |
|:---|:---|:---|
| Schema Version | `SEC-COST-DB-vX.Y` | `SEC-COST-DB-v4.1` |
| Ngày cập nhật | DD/MM/YYYY | 11/02/2026 |
| Changelog | Markdown bullet list | Xem bên dưới |

---

**Changelog v4.1 (từ v4.0):**
- **Chuyển từ 5-level sang 3-level** — `PREFIX.GROUP.TYPE` thay vì `PREFIX.DISCIPLINE.GROUP.TYPE.LOCATION`.
- **Discipline → attribute** — Không còn nằm trong mã, lưu trong `master_work_items.discipline`.
- **Location → attribute** — Không còn nằm trong mã, lưu trong `master_work_items.location`.
- **GROUP codes mở rộng** — `CON`→`CONC`, `RBR`→`RBAR`, `PIP`→`PIPE`, `CBL`→`CABL`, v.v.
- **TYPE codes đổi từ action-based sang sub-category** — `POUR`→`STR`, `FABR`→`DFM`, `THO3`→`GR3`, v.v.
- **Nguyên tắc Same Suffix** — 4 bảng dùng chung GROUP.TYPE: `A.CONC.STR`, `M.CONC.STR`, `L.CONC.STR`, `E.CONC.STR`.
- **Thêm attributes** — `material_type`, `worker_grade`, `equip_type` trên `master_work_items`.
- **Instance code ngắn hơn** — `A.CONC.STR-001` thay vì `A.CV.CON.POUR.COL-001`.

**Changelog v4.0 (từ v3.0):**
- **Sửa Level Count** — Khai báo chính xác 5 phần (L0.L1.L2.L3.L4), không còn nhầm lẫn 6 tầng.
- **Thêm Bảng L (Labour)** — Nhân công phân theo bộ môn + bậc thợ.
- **Thêm Bảng E (Equipment)** — Máy móc phân theo loại.
- **Thêm cột WASTE_%** trong Bảng M.
- **Thêm KEYWORDS_EN** — Từ khóa song ngữ.
- **Loại bỏ wildcard `*`** trong Link M-Code.
- **Thêm cột BOM_L, BOM_E** trong Bảng A.
- **Mô hình BOM N:M**.
- **Thêm Schema Version**.

