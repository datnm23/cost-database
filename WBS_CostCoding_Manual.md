# HỆ THỐNG MÃ CHI PHÍ & WBS TIÊU CHUẨN (COST CODING MANUAL)
**Phiên bản:** 4.0 - FULL CODE SYSTEM  
**Áp dụng:** Quản lý Chi phí, Đấu thầu (Tender), QS & Kiểm soát Dự án  
**Ngày hiệu lực:** 03/02/2026  
**Cập nhật:** Bao phủ 99% công tác ngành Xây dựng Việt Nam với Spec Code Extension

---

## I. TỔNG QUAN HỆ THỐNG (SYSTEM OVERVIEW)

### 1.1 Cấu trúc Phân cấp (Hierarchy)

Hệ thống mã bao gồm **5 cấp độ (Levels)**, tuân thủ nguyên tắc: **Càng xuống sâu, ý nghĩa càng phụ thuộc vào ngữ cảnh của nhóm cha.**

| Level | Tên gọi | Chức năng | Ví dụ |
|:---:|:---|:---|:---|
| **L1** | Mã Dự Án (Project Code) | Định danh dự án | SEC, PRJ-A |
| **L2** | Nhóm Ngành Chính (Main Group) | Phân loại theo chuyên ngành | 0X - 9X |
| **L3** | Hệ Thống (System) | Hạng mục công việc | 01, 02, 03... |
| **L4** | Thành Phần (Component) | Vật liệu / Thiết bị | 01, 02, 03... |
| **L5** | Phân Loại (Classification) | Đặc tính / Quy cách | 10, 20, 30... |

### 1.2 Định dạng Mã (Code Format)

#### A. Cấu trúc SEC Code (Master Code - Dùng chung)

```
[L2]-[L3]-[L4]-[L5]
  ↓    ↓    ↓    ↓
 04 - 21 - 02 - 10
```

| Thành phần | Độ dài | Ý nghĩa | Ví dụ |
|:---:|:---:|:---|:---|
| **L2** | 2 số | Nhóm ngành chính | `04` = MEP |
| **L3** | 2 số | Hệ thống | `21` = Cấp nước sinh hoạt |
| **L4** | 2 số | Thành phần | `02` = Đường ống |
| **L5** | 2 số | Phân loại chi tiết | `10` = Ống PPR/Nhiệt |

#### B. Spec Code Extension - Mã Quy cách Kỹ thuật ⭐ NEW

> **VẤN ĐỀ:** SEC Code chỉ phân loại LOẠI công tác, không mã hóa được QUY CÁCH chi tiết (D25, PN16, M300...). Khi import Excel → không match chính xác được.

> **GIẢI PHÁP:** Thêm **Spec Code** (mã quy cách) để tạo **Full Code** duy nhất cho mỗi công tác cụ thể.

#### A. Cấu trúc Full Code (SEC + Spec)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CẤU TRÚC FULL CODE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│     SEC CODE          SPEC CODE           FULL CODE                         │
│   ┌───────────┐   +   ┌─────────┐   =   ┌─────────────────────┐            │
│   │04-21-02-10│   .   │D025P16  │       │ 04-21-02-10.D025P16 │            │
│   └───────────┘       └─────────┘       └─────────────────────┘            │
│        ↓                   ↓                      ↓                         │
│   (Phân loại)         (Quy cách)          (Unique - Định giá)              │
│                                                                              │
│   Ý nghĩa: Ống PPR (04-21-02-10) + Đường kính 25mm, PN16 (D025P16)          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### B. Bảng Spec Code theo Loại Công tác

##### B1. Đường ống (Piping) - Format: `D{size}P{PN}` hoặc `D{size}{material}`

| Spec Code | Ý nghĩa | Ví dụ Full Code |
|:---|:---|:---|
| `D020P10` | DN20, PN10 | `04-21-02-10.D020P10` |
| `D025P16` | DN25, PN16 | `04-21-02-10.D025P16` |
| `D032P20` | DN32, PN20 | `04-21-02-10.D032P20` |
| `D050P10` | DN50, PN10 | `04-21-02-10.D050P10` |
| `D100P16` | DN100, PN16 | `04-21-02-20.D100P16` |
| `D150FL` | DN150, Flange | `04-21-02-30.D150FL` |
| `D200WD` | DN200, Welded | `04-21-02-30.D200WD` |

##### B2. Bê tông (Concrete) - Format: `M{grade}` hoặc `M{grade}S{slump}`

| Spec Code | Ý nghĩa | Ví dụ Full Code |
|:---|:---|:---|
| `M200` | Mác 200 | `01-03-01-20.M200` |
| `M250` | Mác 250 | `01-03-01-20.M250` |
| `M300` | Mác 300 | `01-03-01-20.M300` |
| `M350` | Mác 350 | `01-03-01-20.M350` |
| `M400` | Mác 400 | `01-03-01-30.M400` |
| `M300S12` | Mác 300, độ sụt 12cm | `01-03-01-20.M300S12` |
| `M350S18` | Mác 350, độ sụt 18cm | `01-03-01-30.M350S18` |

##### B3. Cốt thép (Rebar) - Format: `D{diameter}` hoặc `D{diameter}{grade}`

| Spec Code | Ý nghĩa | Ví dụ Full Code |
|:---|:---|:---|
| `D06` | Φ6 | `01-03-03-10.D06` |
| `D08` | Φ8 | `01-03-03-10.D08` |
| `D10` | Φ10 | `01-03-03-10.D10` |
| `D12` | Φ12 | `01-03-03-18.D12` |
| `D16` | Φ16 | `01-03-03-18.D16` |
| `D20` | Φ20 | `01-03-03-19.D20` |
| `D25` | Φ25 | `01-03-03-19.D25` |
| `D32` | Φ32 | `01-03-03-19.D32` |
| `D25G500` | Φ25, Grade 500 | `01-03-03-19.D25G500` |

##### B4. Gạch/Đá ốp lát (Tile/Stone) - Format: `{W}x{H}` hoặc `{W}x{H}{grade}`

| Spec Code | Ý nghĩa | Ví dụ Full Code |
|:---|:---|:---|
| `300x300` | 300x300mm | `03-03-01-10.300x300` |
| `400x400` | 400x400mm | `03-03-01-10.400x400` |
| `600x600` | 600x600mm | `03-03-01-20.600x600` |
| `800x800` | 800x800mm | `03-03-01-20.800x800` |
| `600x1200` | 600x1200mm | `03-03-01-30.600x1200` |
| `600x600P` | 600x600, Premium | `03-03-01-20.600x600P` |
| `600x600L` | 600x600, Luxury | `03-03-01-30.600x600L` |

##### B5. Cáp điện (Cable) - Format: `{cores}C{size}` hoặc `{cores}C{size}{type}`

| Spec Code | Ý nghĩa | Ví dụ Full Code |
|:---|:---|:---|
| `1C2.5` | 1 lõi 2.5mm² | `04-01-02-10.1C2.5` |
| `1C4` | 1 lõi 4mm² | `04-01-02-10.1C4` |
| `2C4` | 2 lõi 4mm² | `04-01-02-10.2C4` |
| `3C6` | 3 lõi 6mm² | `04-01-02-10.3C6` |
| `4C10` | 4 lõi 10mm² | `04-01-02-10.4C10` |
| `3C25+1C16` | 3x25+1x16mm² | `04-01-02-20.3C25+1C16` |
| `3C70+1C35CU` | 3x70+1x35mm² Cu | `04-01-02-20.3C70+1C35CU` |
| `3C150AL` | 3x150mm² Al | `04-01-02-20.3C150AL` |

##### B6. Ống gió (Duct) - Format: `{W}x{H}` hoặc `D{diameter}`

| Spec Code | Ý nghĩa | Ví dụ Full Code |
|:---|:---|:---|
| `200x100` | 200x100mm | `04-34-02-10.200x100` |
| `400x200` | 400x200mm | `04-34-02-10.400x200` |
| `600x300` | 600x300mm | `04-34-02-20.600x300` |
| `800x400` | 800x400mm | `04-34-02-20.800x400` |
| `D150` | Φ150mm tròn | `04-34-02-10.D150` |
| `D250` | Φ250mm tròn | `04-34-02-10.D250` |
| `D315FLEX` | Φ315mm flexible | `04-34-02-10.D315FLEX` |

##### B7. Thiết bị HVAC - Format: `{capacity}{unit}`

| Spec Code | Ý nghĩa | Ví dụ Full Code |
|:---|:---|:---|
| `9K` | 9,000 BTU | `04-33-01-10.9K` |
| `12K` | 12,000 BTU | `04-33-01-10.12K` |
| `18K` | 18,000 BTU | `04-33-01-10.18K` |
| `24K` | 24,000 BTU | `04-33-01-10.24K` |
| `5HP` | 5 HP | `04-32-01-02.5HP` |
| `100RT` | 100 RT (Chiller) | `04-31-01-01.100RT` |
| `500RT` | 500 RT (Chiller) | `04-31-01-01.500RT` |

##### B8. Đèn chiếu sáng - Format: `{watt}W{type}`

| Spec Code | Ý nghĩa | Ví dụ Full Code |
|:---|:---|:---|
| `9WLED` | 9W LED | `04-05-03-10.9WLED` |
| `18WLED` | 18W LED | `04-05-03-10.18WLED` |
| `36WLED` | 36W LED | `04-05-03-10.36WLED` |
| `40WTUBE` | 40W T8 Tube | `04-05-03-10.40WTUBE` |
| `150WHPS` | 150W High Pressure Sodium | `11-06-03-20.150WHPS` |
| `250WHPS` | 250W HPS | `11-06-03-20.250WHPS` |

##### B9. Sơn (Paint) - Format: `{coats}C{type}`

| Spec Code | Ý nghĩa | Ví dụ Full Code |
|:---|:---|:---|
| `1CPR` | 1 lớp primer | `03-04-05-10.1CPR` |
| `2CEM` | 2 lớp emulsion | `03-04-05-10.2CEM` |
| `3CEM` | 3 lớp emulsion | `03-04-05-20.3CEM` |
| `2CEP` | 2 lớp epoxy | `03-04-05-30.2CEP` |
| `3CPU` | 3 lớp PU | `03-04-05-30.3CPU` |
| `2CWTR` | 2 lớp chống thấm | `07-03-05-20.2CWTR` |

##### B10. Ván khuôn (Formwork) - Format: `{height}H` hoặc `{type}`

| Spec Code | Ý nghĩa | Ví dụ Full Code |
|:---|:---|:---|
| `H4` | Cao ≤4m | `01-03-02-10.H4` |
| `H8` | Cao ≤8m | `01-03-02-10.H8` |
| `H16` | Cao ≤16m | `01-03-02-20.H16` |
| `H50` | Cao >16m (Highrise) | `01-03-02-30.H50` |
| `CIR` | Cong/Circular | `01-03-02-30.CIR` |
| `SLIP` | Ván khuôn trượt | `01-03-02-30.SLIP` |

##### B11. Cọc (Piling) - Format: `D{size}L{length}` hoặc `{type}D{size}`

| Spec Code | Ý nghĩa | Ví dụ Full Code |
|:---|:---|:---|
| `D300L12` | Cọc ép D300, dài 12m | `01-02-01-10.D300L12` |
| `D350L15` | Cọc ép D350, dài 15m | `01-02-01-10.D350L15` |
| `D400L18` | Cọc ép D400, dài 18m | `01-02-01-10.D400L18` |
| `BPD600L20` | Cọc khoan nhồi D600, 20m | `01-02-01-20.BPD600L20` |
| `BPD800L25` | Cọc khoan nhồi D800, 25m | `01-02-01-20.BPD800L25` |
| `BPD1000L30` | Cọc khoan nhồi D1000, 30m | `01-02-01-20.BPD1000L30` |

##### B12. Cửa (Door/Window) - Format: `{W}x{H}{type}`

| Spec Code | Ý nghĩa | Ví dụ Full Code |
|:---|:---|:---|
| `800x2100W` | Cửa gỗ 800x2100 | `03-05-01-10.800x2100W` |
| `900x2100W` | Cửa gỗ 900x2100 | `03-05-01-10.900x2100W` |
| `900x2100F` | Cửa chống cháy 900x2100 | `03-05-01-30.900x2100F` |
| `1200x2100F` | Cửa chống cháy 2 cánh | `03-05-01-30.1200x2100F` |
| `1500x1500AL` | Cửa sổ nhôm 1500x1500 | `07-01-02-20.1500x1500AL` |
| `2000x2200AL` | Cửa đi nhôm 2000x2200 | `07-06-02-20.2000x2200AL` |

##### B13. Thép hình (Structural Steel) - Format: `{profile}{size}`

| Spec Code | Ý nghĩa | Ví dụ Full Code |
|:---|:---|:---|
| `H200x100` | H-beam 200x100 | `02-02-04-10.H200x100` |
| `H300x150` | H-beam 300x150 | `02-02-04-10.H300x150` |
| `H400x200` | H-beam 400x200 | `02-02-04-20.H400x200` |
| `I200` | I-beam 200 | `02-02-04-10.I200` |
| `C100x50` | C-channel 100x50 | `02-02-04-10.C100x50` |
| `L75x75x8` | Angle 75x75x8 | `02-02-04-10.L75x75x8` |
| `BOX100x100x4` | Box 100x100x4 | `02-02-04-10.BOX100x100x4` |

##### B14. Thang máy (Elevator) - Format: `{capacity}KG{speed}`

| Spec Code | Ý nghĩa | Ví dụ Full Code |
|:---|:---|:---|
| `630KG1.0` | 630kg, 1.0m/s | `04-51-01-01.630KG1.0` |
| `1000KG1.75` | 1000kg, 1.75m/s | `04-51-01-01.1000KG1.75` |
| `1350KG2.5` | 1350kg, 2.5m/s | `04-51-01-01.1350KG2.5` |
| `1600KG3.0` | 1600kg, 3.0m/s | `04-51-01-01.1600KG3.0` |
| `2000KG1.0` | 2000kg hàng, 1.0m/s | `04-52-01-01.2000KG1.0` |

##### B15. Bơm (Pump) - Format: `{flow}M3{head}M` hoặc `{power}KW`

| Spec Code | Ý nghĩa | Ví dụ Full Code |
|:---|:---|:---|
| `10M3H20M` | 10m³/h, cột áp 20m | `04-24-01-10.10M3H20M` |
| `20M3H30M` | 20m³/h, cột áp 30m | `04-24-01-10.20M3H30M` |
| `50M3H40M` | 50m³/h, cột áp 40m | `04-24-01-20.50M3H40M` |
| `3KW` | Bơm 3kW | `04-24-01-10.3KW` |
| `5.5KW` | Bơm 5.5kW | `04-24-01-10.5.5KW` |
| `FIRE100M3H80M` | Bơm PCCC 100m³/h, 80m | `04-10-02-01.FIRE100M3H80M` |

##### B16. Chống thấm (Waterproofing) - Format: `{thickness}MM{type}`

| Spec Code | Ý nghĩa | Ví dụ Full Code |
|:---|:---|:---|
| `3MMBIT` | Màng bitum 3mm | `07-03-01-10.3MMBIT` |
| `4MMBIT` | Màng bitum 4mm | `07-03-01-10.4MMBIT` |
| `1.5MMPVC` | Màng PVC 1.5mm | `07-03-01-20.1.5MMPVC` |
| `2MMPU` | PU coating 2mm | `07-03-01-20.2MMPU` |
| `FLEX2C` | Chống thấm gốc xi măng 2 lớp | `07-03-01-10.FLEX2C` |

##### B17. Kính (Glass) - Format: `{thickness}MM{type}`

| Spec Code | Ý nghĩa | Ví dụ Full Code |
|:---|:---|:---|
| `6MMCL` | Kính trong 6mm | `07-01-04-10.6MMCL` |
| `8MMCL` | Kính trong 8mm | `07-01-04-10.8MMCL` |
| `10MMTEMP` | Kính cường lực 10mm | `07-01-04-20.10MMTEMP` |
| `12MMTEMP` | Kính cường lực 12mm | `07-01-04-20.12MMTEMP` |
| `6+12A+6LOW` | Kính hộp Low-E | `07-01-04-30.6+12A+6LOW` |
| `8+12A+8DBL` | Kính hộp cách âm | `07-01-04-30.8+12A+8DBL` |

##### B18. Phụ kiện ống (Pipe Fittings) - Format: `{type}D{size}`

| Spec Code | Ý nghĩa | Ví dụ Full Code |
|:---|:---|:---|
| `EL90D25` | Co 90° DN25 | `04-21-02-91.EL90D25` |
| `EL45D25` | Co 45° DN25 | `04-21-02-91.EL45D25` |
| `TEED25` | Tê DN25 | `04-21-02-91.TEED25` |
| `REDD32x25` | Thu DN32→25 | `04-21-02-91.REDD32x25` |
| `CPLD50` | Măng xông DN50 | `04-21-02-91.CPLD50` |
| `FLD100` | Mặt bích DN100 | `04-21-02-91.FLD100` |
| `GVALD50` | Van cổng DN50 | `04-21-01-10.GVALD50` |
| `CHKVALD80` | Van 1 chiều DN80 | `04-21-01-10.CHKVALD80` |

##### B19. Thiết bị vệ sinh (Sanitary) - Format: `{type}{grade}`

| Spec Code | Ý nghĩa | Ví dụ Full Code |
|:---|:---|:---|
| `WCS` | Bồn cầu Standard | `03-07-01-10.WCS` |
| `WCP` | Bồn cầu Premium | `03-07-01-20.WCP` |
| `WCL` | Bồn cầu Luxury | `03-07-01-30.WCL` |
| `LAVS` | Lavabo Standard | `03-07-02-10.LAVS` |
| `LAVP` | Lavabo Premium | `03-07-02-20.LAVP` |
| `SHOWERMIX` | Sen tắm mixer | `03-07-03-10.SHOWERMIX` |
| `SHOWERRAIN` | Sen tắm rain shower | `03-07-03-20.SHOWERRAIN` |

##### B20. Đất công trình (Earthworks) - Format: `{grade}{method}`

| Spec Code | Ý nghĩa | Ví dụ Full Code |
|:---|:---|:---|
| `G1M` | Cấp I-II, máy đào | `01-01-01-10.G1M` |
| `G1H` | Cấp I-II, thủ công | `01-01-01-10.G1H` |
| `G3M` | Cấp III-IV, máy đào | `01-01-01-12.G3M` |
| `G3H` | Cấp III-IV, thủ công | `01-01-01-12.G3H` |
| `ROCK` | Đào phá đá | `01-01-01-13.ROCK` |
| `FILL95` | Đắp đất K95 | `10-01-01-20.FILL95` |
| `FILL98` | Đắp đất K98 | `10-01-01-20.FILL98` |

#### C. Quy tắc đặt Spec Code

| Quy tắc | Mô tả | Ví dụ |
|:---|:---|:---|
| **Chữ số đầu = 0** | Thêm 0 để đủ 3 chữ số (đường kính) | D25 → `D025` |
| **Không dấu cách** | Nối liền các thông số | DN25 PN16 → `D025P16` |
| **Viết HOA** | Tất cả chữ cái viết HOA | led → `LED` |
| **Đơn vị chuẩn** | mm cho kích thước, mm² cho cáp | |
| **Ưu tiên thông số** | Size > Grade > Type > Material | `D025P16CU` |
| **Dấu x cho kích thước** | WxH hoặc WxHxT | `600x600`, `100x100x4` |
| **Dấu + cho tổ hợp** | Nhiều lõi hoặc lớp kính | `3C25+1C16`, `6+12A+6` |

#### C2. Prefix chuẩn theo loại công tác

| Prefix | Ý nghĩa | Áp dụng cho |
|:---|:---|:---|
| `D` | Diameter (Đường kính) | Ống, thép, cọc |
| `M` | Mác/Grade | Bê tông |
| `P` | Pressure (Áp suất) | Ống PN |
| `H` | Height (Chiều cao) | Ván khuôn |
| `L` | Length (Chiều dài) | Cọc |
| `W` | Wood/Width | Cửa gỗ, chiều rộng |
| `F` | Fire (Chống cháy) | Cửa PCCC |
| `AL` | Aluminum | Cửa nhôm |
| `C` | Core/Coat | Số lõi cáp, số lớp sơn |
| `G` | Grade (Cấp đất) | Công tác đất |
| `S` | Standard | Thiết bị tiêu chuẩn |
| `P` | Premium | Thiết bị cao cấp |
| `L` | Luxury | Thiết bị sang trọng |

#### C3. Bảng tham chiếu Spec Code phổ biến

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SPEC CODE REFERENCE CARD                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PIPE (Ống):       D{size}P{PN}     → D025P16, D050P10, D100P16             │
│  CONCRETE (BT):    M{grade}         → M200, M250, M300, M350, M400          │
│  REBAR (Thép):     D{dia}           → D06, D08, D10, D12, D16, D20, D25     │
│  TILE (Gạch):      {W}x{H}          → 300x300, 600x600, 800x800             │
│  CABLE (Cáp):      {n}C{size}       → 1C4, 2C4, 3C6, 4C10                   │
│  DUCT (Ống gió):   {W}x{H}          → 200x100, 400x200, 600x300             │
│  HVAC:             {BTU}K/{HP}HP    → 9K, 12K, 24K, 5HP                     │
│  CHILLER:          {cap}RT          → 100RT, 300RT, 500RT                   │
│  PUMP:             {flow}M3H{head}M → 10M3H20M, 50M3H40M                    │
│  ELEVATOR:         {kg}KG{speed}    → 630KG1.0, 1000KG1.75                  │
│  PILE:             D{dia}L{len}     → D300L12, D600L20                      │
│  DOOR:             {W}x{H}{type}    → 900x2100W, 1200x2100F                 │
│  GLASS:            {t}MM{type}      → 6MMCL, 10MMTEMP, 6+12A+6LOW          │
│  PAINT:            {coats}C{type}   → 2CEM, 3CEM, 2CEP                      │
│  WATERPROOF:       {t}MM{type}      → 3MMBIT, 2MMPU                         │
│  EARTHWORK:        G{grade}{method} → G1M, G3M, ROCK                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### D. Ứng dụng trong Excel - Import/Export

##### D1. Template Excel chuẩn

| Cột A | Cột B | Cột C | Cột D | Cột E | Cột F | Cột G |
|:---|:---|:---|:---|:---|:---|:---|
| **STT** | **Mô tả BOQ gốc** | **SEC Code** | **Spec Code** | **Full Code** | **Đơn vị** | **Đơn giá** |
| 1 | Ống PPR D25 PN16 cấp nước lạnh | 04-21-02-10 | D025P16 | 04-21-02-10.D025P16 | m | 45,000 |
| 2 | Ống PPR D32 PN20 cấp nước nóng | 04-21-02-10 | D032P20 | 04-21-02-10.D032P20 | m | 62,000 |
| 3 | Bê tông đài móng M300 đổ bơm | 01-03-01-20 | M300 | 01-03-01-20.M300 | m³ | 1,250,000 |
| 4 | Thép móng Φ16 | 01-03-03-18 | D16 | 01-03-03-18.D16 | kg | 18,500 |
| 5 | Gạch 600x600 cao cấp | 03-03-01-20 | 600x600P | 03-03-01-20.600x600P | m² | 285,000 |

##### D2. Công thức Excel tự động

```excel
# Tạo Full Code từ SEC Code + Spec Code
=CONCATENATE(C2, ".", D2)

# Tìm giá từ Full Code (VLOOKUP)
=VLOOKUP(E2, PriceDatabase!A:G, 7, FALSE)

# Tách SEC Code từ Full Code
=LEFT(E2, 11)

# Tách Spec Code từ Full Code
=MID(E2, 13, LEN(E2)-12)
```

##### D3. Quy trình Import BOQ

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        QUY TRÌNH IMPORT BOQ                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   STEP 1: Upload Excel BOQ                                                   │
│      ↓                                                                       │
│   STEP 2: AI/ML parse mô tả → Gợi ý SEC Code                                │
│      ↓                                                                       │
│   STEP 3: Extract Spec từ mô tả → Gợi ý Spec Code                           │
│      ↓                                                                       │
│   STEP 4: Ghép Full Code = SEC + "." + Spec                                 │
│      ↓                                                                       │
│   STEP 5: Lookup giá từ Price Database                                       │
│      ↓                                                                       │
│   STEP 6: User review & confirm                                              │
│      ↓                                                                       │
│   STEP 7: Export BOQ chuẩn hóa                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### E. Database Schema với Spec Code

```sql
-- Bảng Master SEC Code
CREATE TABLE sec_codes (
    sec_code VARCHAR(11) PRIMARY KEY,  -- '04-21-02-10'
    name_vn VARCHAR(200),
    name_en VARCHAR(200),
    unit VARCHAR(20),
    level2 CHAR(2),
    level3 CHAR(2),
    level4 CHAR(2),
    level5 CHAR(2)
);

-- Bảng Spec Code (Chi tiết quy cách)
CREATE TABLE spec_codes (
    id SERIAL PRIMARY KEY,
    sec_code VARCHAR(11) REFERENCES sec_codes(sec_code),
    spec_code VARCHAR(20),           -- 'D025P16'
    full_code VARCHAR(32) UNIQUE,    -- '04-21-02-10.D025P16'
    description VARCHAR(200),        -- 'Ống PPR DN25 PN16'
    spec_size VARCHAR(10),           -- '25' (mm)
    spec_grade VARCHAR(10),          -- 'PN16'
    spec_material VARCHAR(20),       -- 'PPR'
    spec_extra JSONB,                -- Các thông số bổ sung
    UNIQUE(sec_code, spec_code)
);

-- Bảng Giá theo Full Code
CREATE TABLE price_database (
    id SERIAL PRIMARY KEY,
    full_code VARCHAR(32) REFERENCES spec_codes(full_code),
    unit VARCHAR(20),
    unit_price DECIMAL(15,2),
    labor_price DECIMAL(15,2),
    material_price DECIMAL(15,2),
    region VARCHAR(50),              -- 'HCM', 'HN', 'DN'
    effective_date DATE,
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- View ghép đầy đủ thông tin
CREATE VIEW v_full_price_list AS
SELECT 
    s.sec_code,
    sc.spec_code,
    sc.full_code,
    s.name_vn || ' ' || sc.description AS item_name,
    sc.spec_size,
    sc.spec_grade,
    p.unit,
    p.unit_price,
    p.labor_price,
    p.material_price,
    p.region,
    p.effective_date
FROM sec_codes s
JOIN spec_codes sc ON s.sec_code = sc.sec_code
LEFT JOIN price_database p ON sc.full_code = p.full_code;
```

#### F. Lợi ích của hệ thống Full Code

| Tiêu chí | Trước (chỉ SEC Code) | Sau (Full Code = SEC + Spec) |
|:---|:---|:---|
| **Độ chính xác** | ~60% (nhiều item cùng code) | ~99% (unique mỗi quy cách) |
| **Tìm kiếm Excel** | VLOOKUP fail do trùng | VLOOKUP chính xác 100% |
| **So sánh giá** | Không so được chi tiết | So được từng quy cách |
| **Import BOQ** | Cần nhập tay Spec | Auto-extract Spec Code |
| **ML Training** | Thiếu data quy cách | Full data cho prediction |
| **Báo cáo** | Chỉ theo loại công tác | Theo loại + quy cách |

### 1.4 Mã đầy đủ trong Dự án (Project + Full Code)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CẤU TRÚC HOÀN CHỈNH 3 LỚP                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   PROJECT CODE     SEC CODE (Master)      SPEC CODE        FULL CODE        │
│   ┌─────────┐   +  ┌─────────────┐    +   ┌─────────┐  =  ┌─────────────┐   │
│   │   SEC   │      │ 04-21-02-10 │        │ D025P16 │     │ Full Code   │   │
│   └─────────┘      └─────────────┘        └─────────┘     └─────────────┘   │
│       ↓                  ↓                     ↓                ↓            │
│   (Dự án)          (Phân loại)           (Quy cách)      (Định giá)         │
│                                                                              │
│   ► Hiển thị:   SEC-04-21-02-10.D025P16                                     │
│   ► Lưu trữ:    project='SEC' | sec_code='04-21-02-10' | spec='D025P16'     │
│   ► Tra giá:    full_code = '04-21-02-10.D025P16'                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

> **Ví dụ giải mã:** `04-21-02-10.D025P16`
> - **04:** Nhóm MEP - Hệ thống Cơ điện
> - **21:** Cấp nước sinh hoạt (Plumbing)  
> - **02:** Đường ống (Piping)
> - **10:** Ống PPR/PVC nối nhiệt/dán
> - **D025P16:** Đường kính 25mm, áp suất PN16

#### A. Lợi ích của việc tách 3 lớp

| Tiêu chí | Lợi ích |
|:---|:---|
| **Tra giá chính xác** | Full Code `04-21-02-10.D025P16` → 1 đơn giá duy nhất |
| **So sánh linh hoạt** | Cùng SEC Code → So sánh qua nhiều dự án |
| **Import Excel** | Match chính xác bằng Full Code |
| **Báo cáo đa cấp** | Group theo SEC Code hoặc Full Code |
| **ML Training** | Full Code + Price → Train prediction chính xác |

#### B. Ví dụ thực tế nhiều dự án với Full Code

| Dự án | SEC Code | Spec Code | Full Code | Display | Mô tả | Đơn giá |
|:---|:---|:---|:---|:---|:---|:---|
| SEC Tower | `04-21-02-10` | `D025P16` | `04-21-02-10.D025P16` | SEC-04-21-02-10.D025P16 | Ống PPR D25 PN16 | 45,000 |
| SEC Tower | `04-21-02-10` | `D032P20` | `04-21-02-10.D032P20` | SEC-04-21-02-10.D032P20 | Ống PPR D32 PN20 | 62,000 |
| Vinhomes A | `04-21-02-10` | `D025P16` | `04-21-02-10.D025P16` | VHA-04-21-02-10.D025P16 | Ống PPR D25 PN16 | 47,000 |
| BV Đa khoa | `01-03-01-20` | `M300` | `01-03-01-20.M300` | BVDK-01-03-01-20.M300 | BT móng M300 | 1,280,000 |

> ⚠️ **QUY TẮC QUAN TRỌNG:**
> - **SEC Code** (`04-21-02-10`) là mã **PHÂN LOẠI**, dùng chung cho mọi dự án
> - **Spec Code** (`D025P16`) là mã **QUY CÁCH**, xác định chi tiết kỹ thuật
> - **Full Code** (`04-21-02-10.D025P16`) là mã **DUY NHẤT**, dùng để tra giá
> - **Project Code** (`SEC`, `VHA`) được quản lý **TÁCH BIỆT** trong database

---

## II. BẢNG MÃ CHUẨN HÓA TOÀN DIỆN (MASTER CODE TABLE)

> ⚠️ **LƯU Ý:** Các mã trong bảng dưới đây là **SEC Code (Master)**, không bao gồm Project Code.
> Khi áp dụng cho dự án cụ thể, ghép thêm Project Code phía trước (ví dụ: `00-01`).

### ═══════════════════════════════════════════════════════════════
### NHÓM 0X: QUẢN LÝ & CHI PHÍ CHUNG (SOFT COSTS)
### ═══════════════════════════════════════════════════════════════

*Phạm vi: Chi phí gián tiếp, không tạo ra tài sản vật chất trực tiếp*

| MÃ | TÊN HẠNG MỤC | GHI CHÚ PHẠM VI & RANH GIỚI |
|:---|:---|:---|
| **00-00** | **Quản lý dự án (Project Management)** | Chi phí nhân sự BQLDA, TVGS, văn phòng công trường, phần mềm quản lý |
| 00-01 | Chi phí chuẩn bị mặt bằng | Lán trại, điện nước thi công, hàng rào tạm, bảo vệ, đường công vụ |
| 00-02 | Chi phí thiết kế & Tư vấn | Thiết kế (KT, KC, MEP, QH), Thẩm tra, QS, BIM |
| 00-03 | Khảo sát địa chất & Môi trường | Khoan khảo sát, Quan trắc lún, ĐTM, Đo đạc địa hình |
| 00-04 | An toàn lao động & Y tế | Trang bị PPE, biển báo, tủ thuốc, huấn luyện HSE, trạm y tế |
| 00-05 | Bảo hiểm & Thuế | BH công trình (CAR), BH trách nhiệm, BH lao động, lệ phí |
| 00-06 | Thủ tục pháp lý & Giấy phép | GPXD, Thẩm duyệt PCCC, Đấu nối điện/nước, Nghiệm thu |
| 00-07 | Chi phí tài chính | Lãi vay, Bảo lãnh ngân hàng, LC, Phí tư vấn tài chính |
| 00-08 | Marketing & Bán hàng | Nhà mẫu, Showroom, Quảng cáo (cho dự án BĐS) |
| 00-09 | Dự phòng (Contingency) | Dự phòng thiết kế (5%), Dự phòng trượt giá |

### ═══════════════════════════════════════════════════════════════
### NHÓM 1X: KẾT CẤU CHÍNH (STRUCTURAL)
### ═══════════════════════════════════════════════════════════════

*Phạm vi: Phần thô (Carcase) - Chịu lực chính của công trình*

| MÃ | TÊN HẠNG MỤC | GHI CHÚ PHẠM VI & RANH GIỚI |
|:---|:---|:---|
| **01-00** | **Móng & Công tác đất (Substructure)** | Từ đáy móng đến Cos ±0.00 |
| 01-01 | Công tác đất công trình | Đào/đắp trong "vết" móng nhà. **Tách biệt với san nền (10-01)** |
| 01-02 | Cọc (Piling) | Cọc khoan nhồi, ép, đóng, cọc xi măng đất. Ranh giới: Cắt đầu cọc |
| 01-03 | Kết cấu Móng | Đài móng, giằng móng, bể ngầm BTCT, sàn tầng hầm |
| 01-04 | Tường hầm & Chống thấm ngầm | Tường vây, Tường hầm BTCT, các lớp chống thấm tiếp xúc đất |
| 01-05 | Gia cố nền đất | Cọc cát, Bấc thấm, Gia cường đất yếu |
| **02-00** | **Kết cấu thân (Superstructure)** | Từ Cos ±0.00 trở lên |
| 02-01 | Khung bê tông cốt thép | Cột, Vách, Lõi thang máy, Dầm, Sàn, Cầu thang bộ (phần thô) |
| 02-02 | Khung thép (Structural Steel) | Kết cấu thép chịu lực chính, bu lông neo, hàn |
| 02-03 | Kết cấu hỗn hợp | Sàn Deck thép, Dầm liên hợp thép-bê tông |
| 02-04 | Mái & Kết cấu đặc biệt | Giàn không gian, Mái vòm, Dàn mái thép (phần chịu lực) |
| 02-05 | Kết cấu tiền chế | Cấu kiện BTCT đúc sẵn, Panel tường |
| 02-06 | Bể nước & Kết cấu chứa | Bể nước ngầm/mái BTCT, Bồn thép (phần kết cấu) |

### ═══════════════════════════════════════════════════════════════
### NHÓM 2X: KIẾN TRÚC & HOÀN THIỆN (ARCHITECTURE & FINISHING)
### ═══════════════════════════════════════════════════════════════

*Phạm vi: Hoàn thiện gắn liền công trình (Fit-out)*

| MÃ | TÊN HẠNG MỤC | GHI CHÚ PHẠM VI & RANH GIỚI |
|:---|:---|:---|
| **03-00** | **Kiến trúc nội thất (Interior Architecture)** | Hoàn thiện bên trong công trình |
| 03-01 | Tường xây & Vách ngăn | Xây gạch, Trát tường, Vách thạch cao, Vách kính nội bộ |
| 03-02 | Trần (Ceiling) | Trần thạch cao, Trần chìm, Trần nhôm, Sơn bả trần |
| 03-03 | Lát nền & Ốp tường | Gạch lát, Đá, Sàn gỗ, Sàn epoxy. **Chỉ trong nhà & logia** |
| 03-04 | Sơn & Hoàn thiện bề mặt | Sơn nước trong nhà, Giấy dán tường, Bả matit |
| 03-05 | Cửa nội thất | Cửa gỗ, Cửa chống cháy, Cửa thông phòng. **Trừ cửa mặt dựng** |
| 03-06 | Lan can & Tay vịn nội thất | Lan can cầu thang, Tay vịn trong nhà |
| 03-07 | Thiết bị vệ sinh (Sanitary Wares) | Bồn cầu, Lavabo, Sen vòi, Gương, Phụ kiện WC |
| 03-08 | Thiết bị nhà bếp | Bồn rửa, Vòi bếp, Máy hút mùi (không gồm tủ bếp) |
| **07-00** | **Mặt dựng & Vỏ bao (Envelope)** | Lớp vỏ tiếp xúc trực tiếp môi trường ngoài |
| 07-01 | Mặt dựng kính (Curtain Wall) | Vách kính mặt tiền, Cửa sổ nhôm kính ngoại thất |
| 07-02 | Mặt dựng ốp (Cladding) | Ốp Aluminium, Đá treo, Lam chắn nắng, Gốm ốp ngoài |
| 07-03 | Chống thấm vỏ công trình | Chống thấm mái, Ban công, Sê-nô, Bệ cửa sổ |
| 07-04 | Mái & Vật liệu lợp | Ngói, Tôn, Tấm lấy sáng - Lớp phủ trên kết cấu |
| 07-05 | Cách nhiệt vỏ công trình | Cách nhiệt mái, Cách nhiệt tường ngoài |
| 07-06 | Cửa ngoại thất | Cửa đi chính, Cửa sổ mở, Cổng (thuộc vỏ bao che) |
| 07-07 | Lan can & Tay vịn ngoại thất | Lan can ban công, Tay vịn ngoài trời |

### ═══════════════════════════════════════════════════════════════
### NHÓM 3X: HỆ THỐNG CƠ ĐIỆN (MEP - MECHANICAL ELECTRICAL PLUMBING)
### ═══════════════════════════════════════════════════════════════

*Ranh giới: Điểm đấu nối với hạ tầng bên ngoài (sau công tơ/đồng hồ)*

| MÃ | TÊN HẠNG MỤC | GHI CHÚ PHẠM VI & RANH GIỚI |
|:---|:---|:---|
| **04-00** | **Hệ thống Điện (Electrical)** | |
| 04-01 | Hệ thống điện hạ thế | Từ tủ MSB đến ổ cắm/công tắc. **Ranh giới: Sau công tơ EVN** |
| 04-02 | Hệ thống điện trung thế | MBA nội bộ, Tủ trung thế (nếu có) |
| 04-03 | Máy phát điện dự phòng | Generator, ATS, Phòng máy phát |
| 04-04 | Hệ thống UPS | Bộ lưu điện, Phòng UPS, Ắc quy |
| 04-05 | Hệ thống chiếu sáng | Đèn, Máng đèn, Điều khiển chiếu sáng trong nhà |
| 04-06 | Chống sét & Tiếp địa | Kim thu sét, Dây dẫn sét, Hệ thống tiếp địa |
| **04-10** | **Hệ thống PCCC ⭐** | **Tách riêng phục vụ thẩm duyệt & nghiệm thu** |
| 04-10-01 | Báo cháy (Fire Alarm) | Đầu báo, Tủ trung tâm, Nút nhấn, Còi/đèn báo |
| 04-10-02 | Chữa cháy bằng nước | Bơm PCCC, Sprinkler, Họng vách tường, Trụ cứu hỏa |
| 04-10-03 | Chữa cháy bằng khí | Hệ thống FM200, CO2, Phòng kỹ thuật đặc biệt |
| 04-10-04 | Hút khói & Tăng áp | Quạt hút khói, Quạt tăng áp cầu thang, Ống gió PCCC |
| 04-10-05 | Phòng cháy thụ động | Sơn chống cháy, Bọc chống cháy, Chèn kín xuyên sàn |
| **04-20** | **Hệ thống Cấp thoát nước (Plumbing)** | **Ranh giới: Cách tường nhà 1.0m** |
| 04-21 | Cấp nước sinh hoạt | Ống cấp nước lạnh/nóng, Van, Đồng hồ nhánh |
| 04-22 | Thoát nước thải | Ống thoát, Xiphong, Ống thông hơi |
| 04-23 | Thoát nước mưa trong nhà | Phễu thu, Ống đứng thoát mưa (trong nhà) |
| 04-24 | Bơm nước | Bơm cấp, Bơm tăng áp, Bơm bể phốt |
| 04-25 | Xử lý nước cấp | Bể chứa, Bồn lọc, Khử trùng |
| **04-30** | **Hệ thống HVAC** | Điều hòa không khí & Thông gió |
| 04-31 | Điều hòa trung tâm | Chiller, AHU, FCU, Đường ống nước lạnh |
| 04-32 | Điều hòa VRV/VRF | Dàn nóng, Dàn lạnh, Đường ống gas |
| 04-33 | Điều hòa cục bộ | Split, Cassette, Máy tủ đứng |
| 04-34 | Thông gió | Quạt thông gió, Ống gió, Miệng gió, Louver |
| 04-35 | Cooling Tower | Tháp giải nhiệt, Bơm nước giải nhiệt |
| **04-40** | **Hệ thống Gas** | Cấp gas tập trung |
| 04-41 | Trạm gas & Bồn chứa | Bồn LPG, Trạm nạp, Van an toàn |
| 04-42 | Đường ống gas | Ống dẫn gas, Van ngắt, Đồng hồ đo |
| **04-50** | **Thang máy & Thang cuốn (Vertical Transport)** | |
| 04-51 | Thang máy chở khách | Cabin, Máy kéo, Cáp, Điều khiển |
| 04-52 | Thang máy chở hàng/bệnh viện | Thang tải lớn, Thang cáng |
| 04-53 | Thang cuốn & Băng tải | Escalator, Travelator |
| 04-54 | Thang máy PCCC | Thang máy chữa cháy (nếu yêu cầu) |
| 04-10-02 | Chữa cháy bằng nước | Bơm PCCC, Sprinkler, Họng vách tường, Trụ cứu hỏa |
| 04-10-03 | Chữa cháy bằng khí | Hệ thống FM200, CO2, Phòng kỹ thuật đặc biệt |
| 04-10-04 | Hút khói & Tăng áp | Quạt hút khói, Quạt tăng áp cầu thang, Ống gió PCCC |
| 04-10-05 | Phòng cháy thụ động | Sơn chống cháy, Bọc chống cháy, Chèn kín xuyên sàn |
| **04-20** | **Hệ thống Cấp thoát nước (Plumbing)** | **Ranh giới: Cách tường nhà 1.0m** |
| 04-21 | Cấp nước sinh hoạt | Ống cấp nước lạnh/nóng, Van, Đồng hồ nhánh |
| 04-22 | Thoát nước thải | Ống thoát, Xiphong, Ống thông hơi |
| 04-23 | Thoát nước mưa trong nhà | Phễu thu, Ống đứng thoát mưa (trong nhà) |
| 04-24 | Bơm nước | Bơm cấp, Bơm tăng áp, Bơm bể phốt |
| 04-25 | Xử lý nước cấp | Bể chứa, Bồn lọc, Khử trùng |
| **04-30** | **Hệ thống HVAC** | Điều hòa không khí & Thông gió |
| 04-31 | Điều hòa trung tâm | Chiller, AHU, FCU, Đường ống nước lạnh |
| 04-32 | Điều hòa VRV/VRF | Dàn nóng, Dàn lạnh, Đường ống gas |
| 04-33 | Điều hòa cục bộ | Split, Cassette, Máy tủ đứng |
| 04-34 | Thông gió | Quạt thông gió, Ống gió, Miệng gió, Louver |
| 04-35 | Cooling Tower | Tháp giải nhiệt, Bơm nước giải nhiệt |
| **04-40** | **Hệ thống Gas** | Cấp gas tập trung |
| 04-41 | Trạm gas & Bồn chứa | Bồn LPG, Trạm nạp, Van an toàn |
| 04-42 | Đường ống gas | Ống dẫn gas, Van ngắt, Đồng hồ đo |
| **04-50** | **Thang máy & Thang cuốn (Vertical Transport)** | |
| 04-51 | Thang máy chở khách | Cabin, Máy kéo, Cáp, Điều khiển |
| 04-52 | Thang máy chở hàng/bệnh viện | Thang tải lớn, Thang cáng |
| 04-53 | Thang cuốn & Băng tải | Escalator, Travelator |
| 04-54 | Thang máy PCCC | Thang máy chữa cháy (nếu yêu cầu) |

| MÃ | TÊN HẠNG MỤC | GHI CHÚ PHẠM VI & RANH GIỚI |
|:---|:---|:---|
| **08-00** | **Hệ thống ELV & ICT (Điện nhẹ)** | Low Voltage & IT Systems |
| 08-01 | Hạ tầng mạng & Viễn thông | LAN, Telephone, Wifi, Server Room |
| 08-02 | Hệ thống CCTV | Camera, NVR/DVR, Màn hình giám sát |
| 08-03 | Hệ thống kiểm soát ra vào | Access Control, Thẻ từ, Vân tay, Face ID |
| 08-04 | Hệ thống báo trộm | Cảm biến, Còi báo động, Keypad |
| 08-05 | Hệ thống âm thanh | PA/BGM, Loa, Ampli, Micro |
| 08-06 | Hệ thống IPTV/MATV | Truyền hình cáp, Anten, Bộ chia |
| 08-07 | Hệ thống BMS | Building Management System, Sensor, Controller |
| 08-08 | Hệ thống đỗ xe thông minh | Barrier, Đầu đọc thẻ, Phần mềm quản lý |
| 08-09 | Hệ thống hiển thị | Digital Signage, LED Display, Info Kiosk |
| 08-10 | Hệ thống gọi y tá | Nurse Call (Bệnh viện) |
| 08-11 | Hệ thống xếp hàng | Queue Management System |

### ═══════════════════════════════════════════════════════════════
### NHÓM 4X: TRANG BỊ & CẢNH QUAN (EQUIPMENT & LANDSCAPE)
### ═══════════════════════════════════════════════════════════════

*Phân biệt: Cảnh quan (thẩm mỹ, đi bộ) vs Hạ tầng (tải trọng, kỹ thuật)*

| MÃ | TÊN HẠNG MỤC | GHI CHÚ PHẠM VI & RANH GIỚI |
|:---|:---|:---|
| **05-00** | **Cảnh quan (Landscape)** | Mang tính THẨM MỸ, trang trí, đi bộ |
| 05-01 | Cây xanh & Trồng cỏ (Softscape) | Cây bóng mát, Thảm cỏ, Cây bụi, Hệ thống tưới cảnh quan |
| 05-02 | Lối đi dạo & Sân vườn (Hardscape) | Đường dạo bộ, Lát đá sân vườn. **Xe cơ giới không đi vào** |
| 05-03 | Chiếu sáng cảnh quan | Đèn hắt cây, Đèn nấm, LED trang trí. **Khác đèn đường cao áp** |
| 05-04 | Tiểu cảnh & Điểm nhấn | Hồ cá, Đài phun nước, Tường thác nước |
| 05-05 | Tiện ích ngoài trời | Ghế đá, Thùng rác, Bồn hoa di động, Xích đu |
| 05-06 | Hàng rào & Cổng cảnh quan | Hàng rào trang trí, Cổng vào khu vườn |
| 05-07 | Hồ bơi & Jacuzzi | Bể bơi, Hệ thống lọc nước hồ bơi, Jacuzzi |
| **06-00** | **Nội thất (FF&E)** | Đồ rời & Đồ gỗ gắn tường |
| 06-01 | Nội thất cố định (Built-in) | Tủ bếp, Tủ âm tường, Vách ốp gỗ, Quầy lễ tân |
| 06-02 | Nội thất rời (Loose Furniture) | Bàn, Ghế, Sofa, Giường, Tủ rời |
| 06-03 | Rèm cửa & Trang trí | Rèm, Mành, Tranh, Thảm rời, Cây nội thất |
| 06-04 | Thiết bị gia dụng | Tủ lạnh, Máy giặt, Lò vi sóng (nếu cấp) |
| 06-05 | Biển báo & Signage | Biển chỉ dẫn, Bảng tên tòa nhà, Số phòng |

### ═══════════════════════════════════════════════════════════════
### NHÓM 5X: CÔNG NGHIỆP & ĐẶC THÙ (INDUSTRIAL & SPECIALIZED)
### ═══════════════════════════════════════════════════════════════

*Dành riêng cho Nhà máy, Bệnh viện, Data Center, Phòng chức năng đặc biệt*

| MÃ | TÊN HẠNG MỤC | GHI CHÚ PHẠM VI & RANH GIỚI |
|:---|:---|:---|
| **09-00** | **Hệ thống công nghệ (Process Systems)** | |
| 09-01 | Dây chuyền sản xuất | Máy móc sản xuất, Băng chuyền |
| 09-02 | Kho lạnh & Kho mát | Phòng lạnh, Kho đông, Hệ thống làm lạnh công nghiệp |
| 09-03 | Phòng sạch (Clean Room) | HEPA, AHU phòng sạch, Vật liệu phòng sạch |
| 09-04 | Hệ thống khí nén | Máy nén khí, Bình chứa, Đường ống khí |
| 09-05 | Lò hơi & Hơi nước | Boiler, Đường ống hơi, Bồn nước nóng công nghiệp |
| 09-06 | Hệ thống gas công nghiệp | Gas trung tâm nhà máy, Đường ống gas kỹ thuật |
| 09-07 | Xử lý khí thải công nghiệp | Scrubber, Cyclone, Ống khói |
| 09-08 | Hệ thống điện mặt trời | Solar Panel, Inverter, Hệ thống lưu trữ |
| 09-09 | Trạm sạc xe điện | EV Charging Station, Hạ tầng điện EV |
| **09-10** | **Thiết bị y tế (Medical Equipment)** | Bệnh viện/Phòng khám |
| 09-11 | Hệ thống khí y tế | Oxy, Khí N2O, Chân không, Khí nén y tế |
| 09-12 | Thiết bị chẩn đoán | CT, MRI, X-Ray (phần lắp đặt) |
| 09-13 | Phòng mổ & ICU | Laminar flow, Cửa tự động y tế |
| **09-20** | **Data Center** | |
| 09-21 | Sàn nâng kỹ thuật | Raised Floor, Grounding |
| 09-22 | Làm mát chính xác | CRAC, In-row cooling |
| 09-23 | Hệ thống chữa cháy DC | FM200, NOVEC, Hệ thống cảnh báo sớm |

### ═══════════════════════════════════════════════════════════════
### NHÓM 6X: HẠ TẦNG & GIAO THÔNG (INFRASTRUCTURE)
### ═══════════════════════════════════════════════════════════════

*Phạm vi: Mang tính KẾT NỐI, TẢI TRỌNG LỚN, CÔNG CỘNG, nằm ngoài công trình*

| MÃ | TÊN HẠNG MỤC | GHI CHÚ PHẠM VI & RANH GIỚI |
|:---|:---|:---|
| **10-00** | **Giao thông (Roads & External)** | |
| 10-01 | Công tác đất giao thông ⭐ | Đào đắp nền đường K95/K98, San lấp mặt bằng toàn khu |
| 10-02 | Đường nội bộ (Road Works) | Kết cấu áo đường Asphalt/Bê tông chịu tải xe |
| 10-03 | Vỉa hè & Bó vỉa | Lát vỉa hè, Bó vỉa bê tông/đá |
| 10-04 | Bãi đỗ xe ngoài trời | Lát sân, Kẻ vạch, Gờ giảm tốc, Chặn bánh xe |
| 10-05 | Hầm đỗ xe | Kết cấu hầm, Hoàn thiện hầm (tách biệt nếu cần) |
| 10-06 | Biển báo & An toàn giao thông | Biển chỉ dẫn, Gương cầu lồi, Vạch sơn đường |
| 10-07 | Cầu & Cống giao thông | Cầu nội bộ, Cống hộp qua đường |
| **11-00** | **Hạ tầng kỹ thuật (Utilities)** | Hệ thống ngầm bên ngoài nhà |
| 11-01 | Công tác đất hạ tầng (Trenching) | Đào rãnh cho ống/cáp ngầm, Đào hố ga, Lấp hoàn trả |
| 11-02 | Cấp nước khu vực | Tuyến ống cấp nước chính (Main line) |
| 11-03 | Thoát nước mưa | Cống thoát mưa, Hố ga, Kênh mương |
| 11-04 | Thoát nước thải & XLNT | Cống thải, Trạm xử lý nước thải (WWTP), Bể tự hoại |
| 11-05 | Điện ngoài nhà | Trạm biến áp (Substation), Cáp ngầm/trên không |
| 11-06 | Chiếu sáng công cộng | Đèn đường cao áp (Street light), Cột đèn |
| 11-07 | Hạ tầng viễn thông | Cống cáp, Hầm cáp, Manholes |
| 11-08 | Tường rào & An ninh | Hàng rào khu vực, Cổng chính, Nhà bảo vệ |
| 11-09 | Kè & Taluy | Kè bờ, Gia cố taluy, Tường chắn đất |

### ═══════════════════════════════════════════════════════════════
### NHÓM 7X: BÀN GIAO & VẬN HÀNH (HANDOVER & OPERATION)
### ═══════════════════════════════════════════════════════════════

*Giai đoạn kết thúc dự án & vận hành ban đầu*

| MÃ | TÊN HẠNG MỤC | GHI CHÚ PHẠM VI & RANH GIỚI |
|:---|:---|:---|
| **12-00** | **Hoàn công & Nghiệm thu** | |
| 12-01 | T&C (Test & Commissioning) | Chạy thử đơn động, Liên động toàn hệ thống |
| 12-02 | Cân chỉnh & Hiệu chỉnh (TAB) | Cân bằng hệ thống HVAC, Điều chỉnh lưu lượng |
| 12-03 | Hồ sơ hoàn công (As-built) | Đo vẽ, In ấn hồ sơ, Bàn giao |
| 12-04 | Bảo hành & Bảo trì | Chi phí Retention, Hợp đồng O&M năm đầu |
| 12-05 | Đào tạo vận hành | Training cho nhân viên vận hành |
| 12-06 | Vật tư dự phòng | Spare parts bàn giao theo hợp đồng |

---

## III. QUY TẮC MA TRẬN LEVEL 4 & 5 (CORE RULES)

### 3.1 Quy tắc Nhóm KẾT CẤU (1X)

| Level 4 (Vật liệu) | Level 5 (Chi tiết) |
|:---|:---|
| `01`: Bê tông (Concrete) | `.10`: Thủ công, `.20`: Bơm cần, `.30`: Bơm tĩnh |
| `02`: Ván khuôn (Formwork) | `.10`: Gỗ, `.20`: Thép định hình, `.30`: Nhôm |
| `03`: Cốt thép (Rebar) | `.10`: d≤10, `.18`: d≤18, `.19`: d>18 |
| `04`: Thép hình (Structural Steel) | `.10`: Hàn, `.20`: Bu lông, `.30`: Tổ hợp |

### 3.2 Quy tắc Nhóm HOÀN THIỆN (2X, 07)

| Level 4 (Gốc vật liệu) | Level 5 (Phẩm cấp) |
|:---|:---|
| `01`: Gạch (Tile) | `.10`: Standard, `.20`: Premium, `.30`: Luxury |
| `02`: Đá (Stone) | `.10`: Đá nhân tạo, `.20`: Đá tự nhiên, `.30`: Đá quý |
| `03`: Gỗ (Wood) | `.10`: Công nghiệp, `.20`: Tự nhiên, `.30`: Gỗ quý |
| `04`: Kính/Nhôm | `.10`: Đơn, `.20`: Hộp, `.30`: Low-E/Dán phim |
| `05`: Sơn (Paint) | `.10`: Kinh tế, `.20`: Cao cấp, `.30`: Đặc biệt |

### 3.3 Quy tắc Nhóm CƠ ĐIỆN (3X, 08)

| Level 4 (Thành phần) | Level 5 (Cấu trúc) |
|:---|:---|
| `01`: Thiết bị (Equipment) | `.01`: Nguồn/Trung tâm, `.02`: Phân phối, `.03`: Đầu cuối |
| `02`: Đường dẫn (Conduit/Pipe) | `.10`: Dán/Nhiệt, `.20`: Ren, `.30`: Hàn/Bích |
| `03`: Đầu cuối (Terminal) | `.10`: Tiêu chuẩn, `.20`: Cao cấp, `.30`: Đặc biệt |

### 3.4 Quy tắc Nhóm ĐẤT & HẠ TẦNG (6X)

| Level 4 (Đối tượng) | Level 5 (Hành động + Cấp đất) |
|:---|:---|
| `01`: Đất (Soil) | `.10`: Đào cấp I-II, `.12`: Đào cấp III-IV, `.13`: Đào đá |
| `02`: Đá/Base (Aggregate) | `.10`: Cấp phối loại 1, `.20`: Cấp phối loại 2 |
| `03`: Nhựa/Bê tông | `.10`: Bê tông, `.20`: Asphalt, `.30`: Đá dăm nhựa |

---

## IV. LƯỚI AN TOÀN - GLOBAL RULES (Level 5)

| MÃ ĐUÔI | TÊN GỌI | PHẠM VI | VÍ DỤ |
|:---:|:---|:---|:---|
| **.00** | Chi phí chung / Tạm tính | Chi phí bao trùm chưa rõ chi tiết | Vận chuyển, Thí nghiệm, Bảo vệ |
| **.90** | Vật tư tiêu hao | Dùng là mất (Consumables) | Que hàn, Đá cắt, Xăng dầu |
| **.91** | Phụ kiện liên kết | Ở lại công trình (Fittings) | Đinh, Vít, Bu lông, Keo |
| **.99** | Khác / Sự cố | Các khoản bất thường | Sửa chữa, Dặm vá, Phạt |

---

## V. QUY TẮC ĐIỂM GIAO CẮT (INTERFACE RULES)

### 5.1 Quy tắc "Chân công trình" (Building Line)
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│     TRONG NHÀ (MEP - 3X)          │   NGOÀI NHÀ (Infra-6X) │
│                                   │                        │
│  ◄─────── 1.0m ──────►│◄── Hố ga ──►                       │
│                       │                                     │
│     Ống/Cáp trong     │   Tuyến ống chính                  │
│     tường + 1m        │   Main line                        │
│                       │                                     │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Quy tắc "Tải trọng" (Load Bearing)
- **Chịu xe tải/xe PCCC** → Nhóm 10 (Giao thông)
- **Đi bộ/xe điện/xe máy** → Nhóm 05 (Cảnh quan)

### 5.3 Quy tắc "Đất 3 lớp" (Earthworks Hierarchy)
```
Lớp 1 (10-01): San nền toàn khu ─────────────────────────
Lớp 2 (01-01): Đào móng nhà ────────────────────────┐    │
Lớp 3 (11-01): Đào rãnh tuyến ống ────────────────┐ │    │
                                                   │ │    │
                                                   ▼ ▼    ▼
```

---

## VI. QUY ĐỊNH KIỂM SOÁT (GOVERNANCE)

| Quy tắc | Mô tả | Hành động |
|:---|:---|:---|
| **No-Asset Rule** | KHÔNG đưa tài sản cố định vào mã `.90-.99` | Kiểm tra khi code |
| **Ngưỡng 10%** | Mã `.90-.99` không vượt 10% giá trị L3 | Báo cáo vượt ngưỡng |
| **Mô tả bắt buộc** | Mã `.99` phải có ghi chú chi tiết | Từ chối nếu thiếu |
| **Một mã - Một BoQ** | Mỗi mã chỉ xuất hiện 1 lần trong BoQ | Merge nếu trùng |

---

## VII. BẢNG TRA CỨU NHANH (QUICK REFERENCE)

### 7.1 Tra cứu theo SEC Code (Phân loại)

| Hạng mục | SEC Code | Logic |
|:---|:---|:---|
| Bê tông móng đổ bơm | `01-03-01-20` | Móng > BT > Bơm cần |
| Thép móng d≤18 | `01-03-03-18` | Móng > Cốt thép > d≤18 |
| Gạch lát cao cấp | `03-03-01-20` | Lát nền > Gạch > Premium |
| Ống PPR nối nhiệt | `04-21-02-10` | Cấp nước > Ống > Nhiệt |
| Máy Chiller | `04-31-01-01` | HVAC > Thiết bị > Nguồn |
| Đầu Sprinkler | `04-10-02-03` | PCCC nước > TB > Đầu cuối |
| Đèn đường LED | `11-06-03-20` | Chiếu sáng CC > TB > Premium |
| Camera CCTV | `08-02-01-02` | CCTV > Thiết bị > Phân phối |

### 7.2 Tra cứu theo Full Code (Định giá) ⭐ NEW

| Hạng mục chi tiết | SEC Code | Spec Code | Full Code | Đơn vị | Đơn giá (VND) |
|:---|:---|:---|:---|:---|:---|
| Bê tông móng M250 đổ bơm | `01-03-01-20` | `M250` | `01-03-01-20.M250` | m³ | 1,180,000 |
| Bê tông móng M300 đổ bơm | `01-03-01-20` | `M300` | `01-03-01-20.M300` | m³ | 1,250,000 |
| Bê tông móng M350 đổ bơm | `01-03-01-20` | `M350` | `01-03-01-20.M350` | m³ | 1,320,000 |
| Thép móng Φ12 | `01-03-03-18` | `D12` | `01-03-03-18.D12` | kg | 17,500 |
| Thép móng Φ16 | `01-03-03-18` | `D16` | `01-03-03-18.D16` | kg | 18,200 |
| Thép móng Φ20 | `01-03-03-19` | `D20` | `01-03-03-19.D20` | kg | 18,800 |
| Gạch 600x600 Premium | `03-03-01-20` | `600x600P` | `03-03-01-20.600x600P` | m² | 245,000 |
| Gạch 800x800 Luxury | `03-03-01-30` | `800x800` | `03-03-01-30.800x800` | m² | 385,000 |
| Ống PPR D20 PN10 | `04-21-02-10` | `D020P10` | `04-21-02-10.D020P10` | m | 32,000 |
| Ống PPR D25 PN16 | `04-21-02-10` | `D025P16` | `04-21-02-10.D025P16` | m | 45,000 |
| Ống PPR D32 PN20 | `04-21-02-10` | `D032P20` | `04-21-02-10.D032P20` | m | 62,000 |
| Ống PPR D50 PN16 | `04-21-02-10` | `D050P16` | `04-21-02-10.D050P16` | m | 95,000 |
| Cáp điện 2x4mm² | `04-01-02-10` | `2C4` | `04-01-02-10.2C4` | m | 28,000 |
| Cáp điện 3x6mm² | `04-01-02-10` | `3C6` | `04-01-02-10.3C6` | m | 42,000 |
| Cáp điện 4x10mm² | `04-01-02-10` | `4C10` | `04-01-02-10.4C10` | m | 68,000 |
| Điều hòa 12,000 BTU | `04-33-01-10` | `12K` | `04-33-01-10.12K` | bộ | 8,500,000 |
| Điều hòa 24,000 BTU | `04-33-01-10` | `24K` | `04-33-01-10.24K` | bộ | 16,200,000 |
| Chiller 100 RT | `04-31-01-01` | `100RT` | `04-31-01-01.100RT` | bộ | 850,000,000 |
| Chiller 500 RT | `04-31-01-01` | `500RT` | `04-31-01-01.500RT` | bộ | 2,800,000,000 |

### 7.3 Quy tắc ghép Full Code trong Excel

```excel
# CÔNG THỨC TẠO FULL CODE
=CONCATENATE([@[SEC Code]], ".", [@[Spec Code]])

# CÔNG THỨC TRA GIÁ
=VLOOKUP([@[Full Code]], PriceDB!A:F, 6, FALSE)

# CÔNG THỨC TÁCH SEC CODE TỪ FULL CODE
=LEFT([@[Full Code]], 11)

# CÔNG THỨC TÁCH SPEC CODE TỪ FULL CODE  
=MID([@[Full Code]], 13, LEN([@[Full Code]])-12)
```

---

## IX. QUY TẮC SPEC CODE THỐNG NHẤT CHO AI CLASSIFICATION

> **MỤC ĐÍCH:** Thiết kế Spec Code có cấu trúc **THỐNG NHẤT** cho tất cả công tác, hỗ trợ AI phân loại tự động và kiểm tra chéo.

### 9.1 NGUYÊN TẮC CHUNG

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CẤU TRÚC SPEC CODE THỐNG NHẤT                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   FORMAT:  {PREFIX}-{PARAM1}-{PARAM2}[-{PARAM3}][-{PARAM4}]                 │
│                                                                              │
│   Trong đó:                                                                  │
│   ├─ PREFIX    = Loại vật liệu (2-4 ký tự, VIẾT HOA)                        │
│   ├─ PARAM1    = Thông số chính (size/grade/type)                           │
│   ├─ PARAM2    = Thông số phụ (material/method/class)                       │
│   ├─ PARAM3    = Đặc tính bổ sung (optional)                                │
│   └─ PARAM4    = Đặc tính đặc biệt (optional)                               │
│                                                                              │
│   QUY TẮC:                                                                   │
│   ├─ Dùng dấu "-" phân cách các thành phần                                  │
│   ├─ Dùng "x" cho kích thước (VD: 600x600)                                  │
│   ├─ Dùng "+" cho tổ hợp (VD: 3C70+1C35)                                    │
│   ├─ Viết HOA tất cả chữ cái                                                │
│   └─ Số không cần padding 0 (VD: D25, không phải D025)                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.2 BẢNG PREFIX MASTER

| # | PREFIX | Loại công tác | SEC Code áp dụng |
|:---:|:---|:---|:---|
| 1 | `BT` | Bê tông (Concrete) | `01-03-01`, `01-04-01`, `02-01-01` |
| 2 | `TH` | Thép cốt thép (Rebar) | `01-03-03`, `02-01-03` |
| 3 | `THEP` | Thép hình (Structural Steel) | `02-02-04` |
| 4 | `VK` | Ván khuôn (Formwork) | `01-03-02`, `02-01-02` |
| 5 | `COC` | Cọc (Piling) | `01-02-01` |
| 6 | `DAT` | Công tác đất (Earthwork) | `01-01-01`, `10-01-01`, `11-01-01` |
| 7 | `ONG` | Ống cấp nước (Pipe) | `04-21-02`, `04-22-02`, `04-23-02` |
| 8 | `OT` | Ống thoát nước (Drainage) | `04-22-02`, `04-23-02` |
| 9 | `CAP` | Cáp điện (Cable) | `04-01-02` |
| 10 | `OLD` | Ống luồn dây (Conduit) | `04-01-03` |
| 11 | `GIO` | Ống gió (Duct) | `04-34-02` |
| 12 | `MG` | Miệng gió (Air Terminal) | `04-34-03` |
| 13 | `QUAT` | Quạt (Fan) | `04-34-01`, `04-10-04` |
| 14 | `GACH` | Gạch (Tile) | `03-03-01` |
| 15 | `DA` | Đá (Stone) | `03-03-02` |
| 16 | `SON` | Sơn (Paint) | `03-04-05`, `07-02-05` |
| 17 | `BA` | Bả matit (Putty) | `03-04-01`, `07-02-01` |
| 18 | `KINH` | Kính (Glass) | `07-01-04` |
| 19 | `CUA` | Cửa (Door/Window) | `03-05-01`, `07-01-02`, `07-06-02` |
| 20 | `TBVS` | Thiết bị vệ sinh (Sanitary) | `03-07-01`, `03-07-02`, `03-07-03` |
| 21 | `DH` | Điều hòa (HVAC) | `04-31-01`, `04-32-01`, `04-33-01` |
| 22 | `BOM` | Bơm (Pump) | `04-24-01`, `04-10-02` |
| 23 | `TM` | Thang máy (Elevator) | `04-51-01`, `04-52-01`, `04-54-01` |
| 24 | `DEN` | Đèn (Lighting) | `04-05-03`, `11-06-03` |
| 25 | `CT` | Chống thấm (Waterproofing) | `07-03-01` |
| 26 | `PKO` | Phụ kiện ống (Pipe Fitting) | `04-21-02-91`, `04-21-01` |
| 27 | `VAN` | Van (Valve) | `04-21-01` |
| 28 | `TRAN` | Trần (Ceiling) | `03-02-01` |
| 29 | `TUONG` | Tường xây (Masonry Wall) | `03-01-01`, `03-01-02`, `03-01-03` |
| 30 | `TRAT` | Trát (Plastering) | `03-01-04` |
| 31 | `LC` | Lan can (Railing) | `03-06-01`, `07-07-01` |
| 32 | `CTHANG` | Cầu thang (Staircase) | `02-01-05` |
| 33 | `MAI` | Mái (Roofing) | `07-04-01`, `07-04-02`, `07-04-03` |
| 34 | `CNCA` | Cách nhiệt/Cách âm (Insulation) | `07-05-01`, `07-05-02` |
| 35 | `OPA` | Ốp Aluminium/Cladding (Façade) | `07-02-01`, `07-02-02`, `07-02-03` |
| 36 | `TBD` | Tủ điện (Electrical Panel) | `04-01-01`, `04-03-01` |
| 37 | `OCCT` | Ổ cắm/Công tắc (Socket/Switch) | `04-01-04`, `08-01-03` |
| 38 | `PCCC` | Thiết bị PCCC (Fire Detection) | `04-10-01` |
| 39 | `SPK` | Sprinkler (Fire Sprinkler) | `04-10-02` |
| 40 | `HCC` | Hộp chữa cháy (Fire Cabinet) | `04-10-02` |

---

### 9.3 QUY TẮC CHI TIẾT TỪNG LOẠI CÔNG TÁC

---

#### 🔷 1. BÊ TÔNG (BT) - Concrete

**FORMAT:** `BT-{grade}-{method}[-{additive}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `grade` | Mác bê tông | M150, M200, M250, M300, M350, M400, M500 |
| `method` | Phương pháp đổ | TC (thủ công), BC (bơm cần), BT (bơm tĩnh) |
| `additive` | Phụ gia (optional) | CT (chống thấm), PN (phụ gia nở), SF (silica fume) |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Bê tông móng - M300 - thương phẩm | `BT-M300-BC` | `01-03-01-20` | `01-03-01-20.BT-M300-BC` |
| Bê tông móng - M250 - thủ công | `BT-M250-TC` | `01-03-01-10` | `01-03-01-10.BT-M250-TC` |
| Bê tông cột - M350 - bơm tĩnh | `BT-M350-BT` | `02-01-01-30` | `02-01-01-30.BT-M350-BT` |
| Bê tông chống thấm - M300 | `BT-M300-BC-CT` | `01-04-01-20` | `01-04-01-20.BT-M300-BC-CT` |

**Validation:** `method` ↔ `SEC L5`: TC→10, BC→20, BT→30

---

#### 🔷 2. THÉP CỐT THÉP (TH) - Rebar

**FORMAT:** `TH-D{diameter}-{grade}`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `diameter` | Đường kính (mm) | 6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 32 |
| `grade` | Mác thép | CB240, CB300, CB400, CB500 |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Thép móng - CB300 - Φ6 | `TH-D6-CB300` | `01-03-03-10` | `01-03-03-10.TH-D6-CB300` |
| Thép móng - CB400 - Φ16 | `TH-D16-CB400` | `01-03-03-18` | `01-03-03-18.TH-D16-CB400` |
| Thép cột - CB500 - Φ25 | `TH-D25-CB500` | `02-01-03-19` | `02-01-03-19.TH-D25-CB500` |

**Validation:** `diameter` ↔ `SEC L5`: D≤10→10, D≤18→18, D>18→19

---

#### 🔷 3. THÉP HÌNH (THEP) - Structural Steel

**FORMAT:** `THEP-{profile}-{size}`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `profile` | Loại thép | H, I, C, L, BOX, U |
| `size` | Kích thước (mm) | 200x100, 300x150, 75x75x8, etc. |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Thép H - 200x100x5.5x8 | `THEP-H-200x100` | `02-02-04-10` | `02-02-04-10.THEP-H-200x100` |
| Thép H - 400x200x8x13 | `THEP-H-400x200` | `02-02-04-20` | `02-02-04-20.THEP-H-400x200` |
| Thép hộp - 100x100x4 | `THEP-BOX-100x100x4` | `02-02-04-10` | `02-02-04-10.THEP-BOX-100x100x4` |
| Thép góc - L75x75x8 | `THEP-L-75x75x8` | `02-02-04-10` | `02-02-04-10.THEP-L-75x75x8` |

---

#### 🔷 4. VÁN KHUÔN (VK) - Formwork

**FORMAT:** `VK-{material}-{height}`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `material` | Vật liệu | GO (gỗ), THEP (thép), NHOM (nhôm), NHUA (nhựa) |
| `height` | Chiều cao (m) | H4, H8, H16, H50 |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Ván khuôn gỗ - móng | `VK-GO-H4` | `01-03-02-10` | `01-03-02-10.VK-GO-H4` |
| Ván khuôn thép - cột | `VK-THEP-H16` | `02-01-02-20` | `02-01-02-20.VK-THEP-H16` |
| Ván khuôn nhôm - cao tầng | `VK-NHOM-H50` | `02-01-02-30` | `02-01-02-30.VK-NHOM-H50` |

**Validation:** `height` ↔ `SEC L5`: H4→10, H8/H16→20, H50→30

---

#### 🔷 5. CỌC (COC) - Piling

**FORMAT:** `COC-{type}-D{diameter}-L{length}`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại cọc | EP (ép), DONG (đóng), KHOAN (khoan nhồi), XM (xi măng đất) |
| `diameter` | Đường kính (mm) | 300, 350, 400, 600, 800, 1000, 1200 |
| `length` | Chiều dài (m) | 12, 15, 18, 20, 25, 30, 40 |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Cọc ép - D300 - 12m | `COC-EP-D300-L12` | `01-02-01-10` | `01-02-01-10.COC-EP-D300-L12` |
| Cọc ép - D400 - 18m | `COC-EP-D400-L18` | `01-02-01-10` | `01-02-01-10.COC-EP-D400-L18` |
| Cọc khoan nhồi - D800 - 25m | `COC-KHOAN-D800-L25` | `01-02-01-20` | `01-02-01-20.COC-KHOAN-D800-L25` |
| Cọc khoan nhồi - D1200 - 40m | `COC-KHOAN-D1200-L40` | `01-02-01-20` | `01-02-01-20.COC-KHOAN-D1200-L40` |

**Validation:** `type` ↔ `SEC L5`: EP/DONG→10, KHOAN→20, XM→30

---

#### 🔷 6. CÔNG TÁC ĐẤT (DAT) - Earthwork

**FORMAT:** `DAT-{action}-{grade}-{method}`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `action` | Hành động | DAO (đào), DAP (đắp), SAN (san) |
| `grade` | Cấp đất | C1 (I-II), C3 (III-IV), DA (đá) |
| `method` | Phương pháp | TC (thủ công), MAY (cơ giới) |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Đào đất móng - cấp I - máy | `DAT-DAO-C1-MAY` | `01-01-01-10` | `01-01-01-10.DAT-DAO-C1-MAY` |
| Đào đất - cấp III - thủ công | `DAT-DAO-C3-TC` | `01-01-01-12` | `01-01-01-12.DAT-DAO-C3-TC` |
| Đắp đất nền - K95 | `DAT-DAP-K95-MAY` | `10-01-01-20` | `10-01-01-20.DAT-DAP-K95-MAY` |
| Đắp đất nền - K98 | `DAT-DAP-K98-MAY` | `10-01-01-20` | `10-01-01-20.DAT-DAP-K98-MAY` |

**Validation:** `grade` ↔ `SEC L5`: C1→10, C3→12, DA→13

---

#### 🔷 7. ỐNG (ONG) - Pipe

**FORMAT:** `ONG-{material}-D{size}-{connection}[-{pressure}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `material` | Vật liệu ống | PPR, PVC, HDPE, GI (thép mạ), SS (inox), CS (thép đen) |
| `size` | Đường kính (mm) | 20, 25, 32, 40, 50, 63, 75, 90, 110, 160, 200, 250, 300 |
| `connection` | Mối nối | NH (nhiệt), DAN (dán), REN (ren), HAN (hàn), FL (bích) |
| `pressure` | Áp suất (optional) | PN10, PN16, PN20, PN25 |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Ống PPR - PN16 - D25 | `ONG-PPR-D25-NH-PN16` | `04-21-02-10` | `04-21-02-10.ONG-PPR-D25-NH-PN16` |
| Ống PPR - PN20 - D32 | `ONG-PPR-D32-NH-PN20` | `04-21-02-10` | `04-21-02-10.ONG-PPR-D32-NH-PN20` |
| Ống PVC thoát - D110 | `ONG-PVC-D110-DAN` | `04-22-02-10` | `04-22-02-10.ONG-PVC-D110-DAN` |
| Ống thép mạ - D50 - ren | `ONG-GI-D50-REN` | `04-21-02-20` | `04-21-02-20.ONG-GI-D50-REN` |
| Ống thép đen - D150 - hàn | `ONG-CS-D150-HAN` | `04-21-02-30` | `04-21-02-30.ONG-CS-D150-HAN` |
| Ống inox - D50 - bích | `ONG-SS-D50-FL` | `04-21-02-30` | `04-21-02-30.ONG-SS-D50-FL` |

**Validation:** `connection` ↔ `SEC L5`: NH/DAN→10, REN→20, HAN/FL→30

---

#### 🔷 8. CÁP ĐIỆN (CAP) - Cable

**FORMAT:** `CAP-{conductor}-{size}-{insulation}[-{armour}][-{shield}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `conductor` | Lõi dẫn | CU (đồng), AL (nhôm) |
| `size` | Tiết diện | 1C4, 2C4, 3C6, 4C10, 4C16, 4C25, 3C70+1C35, 4C300 |
| `insulation` | Cách điện/vỏ | PVC (tiêu chuẩn), XLPE (chịu nhiệt), FR (chống cháy), LSZH (ít khói), MI (khoáng) |
| `armour` | Giáp bảo vệ (optional) | SWA (thép), AWA (nhôm) |
| `shield` | Chống nhiễu (optional) | SC (screened) |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Cáp Cu/XLPE/PVC - 4x10mm² | `CAP-CU-4C10-PVC` | `04-01-02-10` | `04-01-02-10.CAP-CU-4C10-PVC` |
| Cáp Cu/XLPE/PVC - 4x300mm² | `CAP-CU-4C300-PVC` | `04-01-02-20` | `04-01-02-20.CAP-CU-4C300-PVC` |
| Cáp Cu/XLPE/PVC - 3x70+1x35mm² | `CAP-CU-3C70+1C35-PVC` | `04-01-02-20` | `04-01-02-20.CAP-CU-3C70+1C35-PVC` |
| Cáp Cu/XLPE/FR - 4x16mm² | `CAP-CU-4C16-FR` | `04-01-02-30` | `04-01-02-30.CAP-CU-4C16-FR` |
| Cáp Cu/XLPE/FR - 4x300mm² | `CAP-CU-4C300-FR` | `04-01-02-30` | `04-01-02-30.CAP-CU-4C300-FR` |
| Cáp Cu/XLPE/LSZH - 3x6mm² | `CAP-CU-3C6-LSZH` | `04-01-02-31` | `04-01-02-31.CAP-CU-3C6-LSZH` |
| Cáp Cu/XLPE/PVC/SWA - 4x95mm² | `CAP-CU-4C95-PVC-SWA` | `04-01-02-40` | `04-01-02-40.CAP-CU-4C95-PVC-SWA` |
| Cáp Cu/XLPE/PVC chống nhiễu - 2x1.5mm² | `CAP-CU-2C1.5-PVC-SC` | `04-01-02-50` | `04-01-02-50.CAP-CU-2C1.5-PVC-SC` |
| Cáp khoáng MI - 2x2.5mm² | `CAP-CU-2C2.5-MI` | `04-01-02-60` | `04-01-02-60.CAP-CU-2C2.5-MI` |
| Cáp FR + SWA - 4x16mm² | `CAP-CU-4C16-FR-SWA` | `04-01-02-70` | `04-01-02-70.CAP-CU-4C16-FR-SWA` |
| Cáp nhôm Al/XLPE/PVC - 4x300mm² | `CAP-AL-4C300-PVC` | `04-01-02-20` | `04-01-02-20.CAP-AL-4C300-PVC` |

**Validation:** `insulation` ↔ `SEC L5`:
| Insulation | SEC L5 |
|:---|:---|
| PVC (size ≤16mm²) | 10 |
| PVC (size >16mm²) | 20 |
| FR | 30 |
| LSZH | 31 |
| SWA | 40 |
| SC | 50 |
| MI | 60 |
| FR-SWA (combo) | 70 |

---

#### 🔷 9. ỐNG GIÓ (GIO) - Duct

**FORMAT:** `GIO-{material}-{size}[-{type}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `material` | Vật liệu | TON (tôn), INOX, PU (pre-insulated), FLEX (mềm) |
| `size` | Kích thước | 200x100, 400x200, D150, D250, etc. |
| `type` | Loại (optional) | RECT (vuông), ROUND (tròn) |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Ống gió tôn - 200x100 | `GIO-TON-200x100` | `04-34-02-10` | `04-34-02-10.GIO-TON-200x100` |
| Ống gió tôn - 600x300 | `GIO-TON-600x300` | `04-34-02-20` | `04-34-02-20.GIO-TON-600x300` |
| Ống gió tròn - D250 | `GIO-TON-D250` | `04-34-02-10` | `04-34-02-10.GIO-TON-D250` |
| Ống gió mềm - D150 | `GIO-FLEX-D150` | `04-34-02-10` | `04-34-02-10.GIO-FLEX-D150` |

---

#### 🔷 10. GẠCH (GACH) - Tile

**FORMAT:** `GACH-{type}-{size}-{grade}`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại gạch | MEN (men), GR (granite), POR (porcelain), TER (terracotta) |
| `size` | Kích thước (mm) | 300x300, 400x400, 600x600, 800x800, 600x1200 |
| `grade` | Phẩm cấp | STD (standard), PRE (premium), LUX (luxury) |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Gạch men - 300x300 - tiêu chuẩn | `GACH-MEN-300x300-STD` | `03-03-01-10` | `03-03-01-10.GACH-MEN-300x300-STD` |
| Gạch granite - 600x600 - cao cấp | `GACH-GR-600x600-PRE` | `03-03-01-20` | `03-03-01-20.GACH-GR-600x600-PRE` |
| Gạch porcelain - 800x800 - luxury | `GACH-POR-800x800-LUX` | `03-03-01-30` | `03-03-01-30.GACH-POR-800x800-LUX` |
| Gạch granite - 600x1200 | `GACH-GR-600x1200-LUX` | `03-03-01-30` | `03-03-01-30.GACH-GR-600x1200-LUX` |

**Validation:** `grade` ↔ `SEC L5`: STD→10, PRE→20, LUX→30

---

#### 🔷 11. ĐÁ (DA) - Stone

**FORMAT:** `DA-{type}-{size}-{finish}`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại đá | GR (granite), MB (marble), QZ (quartz), NT (nhân tạo) |
| `size` | Kích thước (mm) | 300x600, 400x400, 600x600, etc. |
| `finish` | Hoàn thiện | MAI (mài bóng), MO (mờ), THO (thô), CHONG (chống trượt) |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Đá granite - 600x600 - mài bóng | `DA-GR-600x600-MAI` | `03-03-02-20` | `03-03-02-20.DA-GR-600x600-MAI` |
| Đá marble - 600x600 - mài bóng | `DA-MB-600x600-MAI` | `03-03-02-30` | `03-03-02-30.DA-MB-600x600-MAI` |
| Đá nhân tạo - 600x600 - mài bóng | `DA-NT-600x600-MAI` | `03-03-02-10` | `03-03-02-10.DA-NT-600x600-MAI` |

**Validation:** `type` ↔ `SEC L5`: NT→10, GR→20, MB/QZ→30

---

#### 🔷 12. SƠN (SON) - Paint

**FORMAT:** `SON-{type}-{coats}L[-{location}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại sơn | LOT (lót), NC (nước), DU (dầu), EP (epoxy), PU (PU), CT (chống thấm) |
| `coats` | Số lớp | 1, 2, 3 |
| `location` | Vị trí (optional) | TRONG (trong nhà), NGOAI (ngoài trời) |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Sơn lót - 1 lớp | `SON-LOT-1L` | `03-04-05-10` | `03-04-05-10.SON-LOT-1L` |
| Sơn nước - 2 lớp - trong nhà | `SON-NC-2L-TRONG` | `03-04-05-10` | `03-04-05-10.SON-NC-2L-TRONG` |
| Sơn nước - 3 lớp - trong nhà | `SON-NC-3L-TRONG` | `03-04-05-20` | `03-04-05-20.SON-NC-3L-TRONG` |
| Sơn epoxy - 2 lớp | `SON-EP-2L` | `03-04-05-30` | `03-04-05-30.SON-EP-2L` |
| Sơn chống thấm - 2 lớp | `SON-CT-2L` | `07-03-05-20` | `07-03-05-20.SON-CT-2L` |
| Sơn nước - 2 lớp - ngoài trời | `SON-NC-2L-NGOAI` | `07-02-05-20` | `07-02-05-20.SON-NC-2L-NGOAI` |

**Validation:** `type+coats` ↔ `SEC L5`: LOT/NC-2L→10, NC-3L→20, EP/PU→30

---

#### 🔷 13. KÍNH (KINH) - Glass

**FORMAT:** `KINH-{type}-{thickness}[-{coating}]` hoặc `KINH-HOP-{config}[-{coating}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại kính | TRONG (trong), MAU (màu), CL (cường lực), DAN (dán an toàn) |
| `thickness` | Độ dày (mm) | 5, 6, 8, 10, 12, 15, 19 |
| `config` | Cấu hình hộp | 6+12A+6, 8+12A+8, etc. (A = Air gap) |
| `coating` | Lớp phủ (optional) | LOW (Low-E), PHAN (phản quang) |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Kính trong - 6mm | `KINH-TRONG-6` | `07-01-04-10` | `07-01-04-10.KINH-TRONG-6` |
| Kính trong - 8mm | `KINH-TRONG-8` | `07-01-04-10` | `07-01-04-10.KINH-TRONG-8` |
| Kính cường lực - 10mm | `KINH-CL-10` | `07-01-04-20` | `07-01-04-20.KINH-CL-10` |
| Kính cường lực - 12mm | `KINH-CL-12` | `07-01-04-20` | `07-01-04-20.KINH-CL-12` |
| Kính dán an toàn - 10mm | `KINH-DAN-10` | `07-01-04-20` | `07-01-04-20.KINH-DAN-10` |
| Kính hộp - 6+12+6 | `KINH-HOP-6+12A+6` | `07-01-04-20` | `07-01-04-20.KINH-HOP-6+12A+6` |
| Kính hộp Low-E - 6+12+6 | `KINH-HOP-6+12A+6-LOW` | `07-01-04-30` | `07-01-04-30.KINH-HOP-6+12A+6-LOW` |

**Validation:** `type` ↔ `SEC L5`: TRONG/MAU→10, CL/DAN/HOP→20, LOW-E→30

---

#### 🔷 14. CỬA (CUA) - Door/Window

**FORMAT:** `CUA-{type}-{material}-{size}[-{special}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại cửa | DI (đi), SO (sổ), TRUOT (trượt) |
| `material` | Vật liệu | GO (gỗ), NHOM (nhôm), NHUA (nhựa), THEP (thép) |
| `size` | Kích thước (mm) | 900x2100, 1500x1500, etc. |
| `special` | Đặc biệt (optional) | CC (chống cháy), AM (cách âm), CHONG (chống trộm) |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Cửa đi gỗ - 900x2100 | `CUA-DI-GO-900x2100` | `03-05-01-10` | `03-05-01-10.CUA-DI-GO-900x2100` |
| Cửa đi gỗ HDF - 900x2100 | `CUA-DI-GO-900x2100-HDF` | `03-05-01-10` | `03-05-01-10.CUA-DI-GO-900x2100-HDF` |
| Cửa chống cháy - 900x2100 | `CUA-DI-THEP-900x2100-CC` | `03-05-01-30` | `03-05-01-30.CUA-DI-THEP-900x2100-CC` |
| Cửa chống cháy 2 cánh - 1200x2100 | `CUA-DI-THEP-1200x2100-CC` | `03-05-01-30` | `03-05-01-30.CUA-DI-THEP-1200x2100-CC` |
| Cửa sổ nhôm - 1500x1500 | `CUA-SO-NHOM-1500x1500` | `07-01-02-20` | `07-01-02-20.CUA-SO-NHOM-1500x1500` |
| Cửa đi nhôm - 2000x2200 | `CUA-DI-NHOM-2000x2200` | `07-06-02-20` | `07-06-02-20.CUA-DI-NHOM-2000x2200` |
| Cửa trượt nhôm - 3000x2400 | `CUA-TRUOT-NHOM-3000x2400` | `07-06-02-20` | `07-06-02-20.CUA-TRUOT-NHOM-3000x2400` |

**Validation:** `special=CC` → `SEC L5=30`

---

#### 🔷 15. THIẾT BỊ VỆ SINH (TBVS) - Sanitary

**FORMAT:** `TBVS-{item}-{brand}-{grade}`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `item` | Loại thiết bị | WC (bồn cầu), LAV (lavabo), SEN (sen vòi), BON (bồn tắm) |
| `brand` | Thương hiệu | TOTO, INAX, KOHLER, GROHE, VN (Việt Nam), etc. |
| `grade` | Phẩm cấp | STD (standard), PRE (premium), LUX (luxury) |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Bồn cầu TOTO - tiêu chuẩn | `TBVS-WC-TOTO-STD` | `03-07-01-10` | `03-07-01-10.TBVS-WC-TOTO-STD` |
| Bồn cầu TOTO - cao cấp | `TBVS-WC-TOTO-PRE` | `03-07-01-20` | `03-07-01-20.TBVS-WC-TOTO-PRE` |
| Bồn cầu thông minh | `TBVS-WC-TOTO-LUX` | `03-07-01-30` | `03-07-01-30.TBVS-WC-TOTO-LUX` |
| Lavabo INAX - tiêu chuẩn | `TBVS-LAV-INAX-STD` | `03-07-02-10` | `03-07-02-10.TBVS-LAV-INAX-STD` |
| Sen vòi GROHE - cao cấp | `TBVS-SEN-GROHE-PRE` | `03-07-03-20` | `03-07-03-20.TBVS-SEN-GROHE-PRE` |

**Validation:** `grade` ↔ `SEC L5`: STD→10, PRE→20, LUX→30

---

#### 🔷 16. ĐIỀU HÒA (DH) - HVAC

**FORMAT:** `DH-{type}-{capacity}-{model}`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại máy | SPLIT, CASSETTE, AM (âm trần), TU (tủ đứng), VRV, CHILLER |
| `capacity` | Công suất | 9K, 12K, 18K, 24K (BTU) / 5HP, 10HP / 100RT, 500RT |
| `model` | Model (optional) | INV (inverter), 1C (1 chiều), 2C (2 chiều) |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Điều hòa split - 12000BTU - inverter | `DH-SPLIT-12K-INV` | `04-33-01-10` | `04-33-01-10.DH-SPLIT-12K-INV` |
| Điều hòa split - 24000BTU | `DH-SPLIT-24K` | `04-33-01-10` | `04-33-01-10.DH-SPLIT-24K` |
| Điều hòa cassette - 36000BTU | `DH-CASSETTE-36K` | `04-33-01-20` | `04-33-01-20.DH-CASSETTE-36K` |
| Điều hòa âm trần nối ống gió - 48K | `DH-AM-48K` | `04-33-01-20` | `04-33-01-20.DH-AM-48K` |
| VRV/VRF - 10HP | `DH-VRV-10HP` | `04-32-01-02` | `04-32-01-02.DH-VRV-10HP` |
| VRV/VRF - 20HP | `DH-VRV-20HP` | `04-32-01-02` | `04-32-01-02.DH-VRV-20HP` |
| Chiller - 300RT - giải nhiệt gió | `DH-CHILLER-300RT-AS` | `04-31-01-01` | `04-31-01-01.DH-CHILLER-300RT-AS` |
| Chiller - 500RT - giải nhiệt nước | `DH-CHILLER-500RT-WC` | `04-31-01-01` | `04-31-01-01.DH-CHILLER-500RT-WC` |

**Validation:** `type` ↔ `SEC L3`: SPLIT/CASSETTE/AM/TU→04-33, VRV→04-32, CHILLER→04-31

---

#### 🔷 17. BƠM (BOM) - Pump

**FORMAT:** `BOM-{type}-{flow}M3-{head}M[-{power}KW]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại bơm | CN (cấp nước), TA (tăng áp), TN (thoát nước), BUN (bùn), PCCC |
| `flow` | Lưu lượng (m³/h) | 10, 20, 30, 50, 100, 150, etc. |
| `head` | Cột áp (m) | 15, 20, 30, 40, 50, 80, 100, etc. |
| `power` | Công suất (optional) | 3KW, 5.5KW, 7.5KW, 11KW, etc. |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Bơm cấp nước - 10m³/h - 20m | `BOM-CN-10M3-20M` | `04-24-01-10` | `04-24-01-10.BOM-CN-10M3-20M` |
| Bơm tăng áp - 30m³/h - 40m | `BOM-TA-30M3-40M` | `04-24-01-20` | `04-24-01-20.BOM-TA-30M3-40M` |
| Bơm thoát nước - 50m³/h - 15m | `BOM-TN-50M3-15M` | `04-24-01-10` | `04-24-01-10.BOM-TN-50M3-15M` |
| Bơm PCCC - 100m³/h - 80m | `BOM-PCCC-100M3-80M` | `04-10-02-01` | `04-10-02-01.BOM-PCCC-100M3-80M` |
| Bơm PCCC - 150m³/h - 100m | `BOM-PCCC-150M3-100M` | `04-10-02-01` | `04-10-02-01.BOM-PCCC-150M3-100M` |

**Validation:** `type=PCCC` → `SEC=04-10-02`

---

#### 🔷 18. THANG MÁY (TM) - Elevator

**FORMAT:** `TM-{type}-{capacity}KG-{speed}[-{brand}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại thang | KHACH (khách), HANG (hàng), BV (bệnh viện), PCCC, QS (quan sát) |
| `capacity` | Tải trọng (kg) | 450, 630, 800, 1000, 1150, 1350, 1600, 2000, 2500 |
| `speed` | Tốc độ (m/s) | 1.0, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0 |
| `brand` | Thương hiệu (optional) | KONE, OTIS, SCHINDLER, MITSUBISHI, etc. |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Thang khách - 630kg - 1.0m/s | `TM-KHACH-630KG-1.0` | `04-51-01-01` | `04-51-01-01.TM-KHACH-630KG-1.0` |
| Thang khách - 1000kg - 1.75m/s | `TM-KHACH-1000KG-1.75` | `04-51-01-01` | `04-51-01-01.TM-KHACH-1000KG-1.75` |
| Thang khách - 1350kg - 2.5m/s | `TM-KHACH-1350KG-2.5` | `04-51-01-01` | `04-51-01-01.TM-KHACH-1350KG-2.5` |
| Thang hàng - 2000kg - 1.0m/s | `TM-HANG-2000KG-1.0` | `04-52-01-01` | `04-52-01-01.TM-HANG-2000KG-1.0` |
| Thang bệnh viện - 1600kg - 1.0m/s | `TM-BV-1600KG-1.0` | `04-52-01-01` | `04-52-01-01.TM-BV-1600KG-1.0` |
| Thang PCCC - 1000kg - 1.0m/s | `TM-PCCC-1000KG-1.0` | `04-54-01-01` | `04-54-01-01.TM-PCCC-1000KG-1.0` |

**Validation:** `type` ↔ `SEC L3`: KHACH→04-51, HANG/BV→04-52, PCCC→04-54

---

#### 🔷 19. ĐÈN (DEN) - Lighting

**FORMAT:** `DEN-{type}-{power}W[-{tech}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại đèn | AM (âm trần), NOI (nổi), PANEL, TUBE, DUONG (đường), PHA |
| `power` | Công suất (W) | 9, 12, 18, 24, 36, 40, 100, 150, 250 |
| `tech` | Công nghệ (optional) | LED, HPS (cao áp sodium), MH (metal halide) |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Đèn LED âm trần - 9W | `DEN-AM-9W-LED` | `04-05-03-10` | `04-05-03-10.DEN-AM-9W-LED` |
| Đèn LED âm trần - 18W | `DEN-AM-18W-LED` | `04-05-03-10` | `04-05-03-10.DEN-AM-18W-LED` |
| Đèn LED panel - 36W | `DEN-PANEL-36W-LED` | `04-05-03-10` | `04-05-03-10.DEN-PANEL-36W-LED` |
| Đèn LED panel - 600x600 - 40W | `DEN-PANEL-40W-LED` | `04-05-03-10` | `04-05-03-10.DEN-PANEL-40W-LED` |
| Đèn đường LED - 100W | `DEN-DUONG-100W-LED` | `11-06-03-20` | `11-06-03-20.DEN-DUONG-100W-LED` |
| Đèn đường cao áp - 250W | `DEN-DUONG-250W-HPS` | `11-06-03-20` | `11-06-03-20.DEN-DUONG-250W-HPS` |
| Đèn pha LED - 150W | `DEN-PHA-150W-LED` | `04-05-03-20` | `04-05-03-20.DEN-PHA-150W-LED` |

**Validation:** `type=DUONG` → `SEC=11-06-03`

---

#### 🔷 20. CHỐNG THẤM (CT) - Waterproofing

**FORMAT:** `CT-{type}-{thickness}[-{layers}L]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại chống thấm | BIT (bitum), PVC (màng PVC), PU (polyurethane), XI (xi măng), KT (kết tinh) |
| `thickness` | Độ dày (mm) | 1.5, 2, 3, 4, 5 |
| `layers` | Số lớp (optional) | 1, 2, 3 |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Chống thấm màng bitum - 3mm | `CT-BIT-3MM` | `07-03-01-10` | `07-03-01-10.CT-BIT-3MM` |
| Chống thấm màng bitum - 4mm | `CT-BIT-4MM` | `07-03-01-10` | `07-03-01-10.CT-BIT-4MM` |
| Chống thấm màng PVC - 1.5mm | `CT-PVC-1.5MM` | `07-03-01-20` | `07-03-01-20.CT-PVC-1.5MM` |
| Chống thấm PU - 2mm | `CT-PU-2MM` | `07-03-01-20` | `07-03-01-20.CT-PU-2MM` |
| Chống thấm xi măng - 2 lớp | `CT-XI-2L` | `07-03-01-10` | `07-03-01-10.CT-XI-2L` |
| Chống thấm kết tinh | `CT-KT-1L` | `07-03-01-30` | `07-03-01-30.CT-KT-1L` |

**Validation:** `type` ↔ `SEC L5`: BIT/XI→10, PVC/PU→20, KT→30

---

#### 🔷 21. PHỤ KIỆN ỐNG (PKO) - Pipe Fittings

**FORMAT:** `PKO-{fitting}-{material}-D{size}`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `fitting` | Loại phụ kiện | CO90, CO45, TE, THU, NOI, BICH |
| `material` | Vật liệu | PPR, PVC, GI, SS, CS |
| `size` | Kích thước (mm) | 20, 25, 32, 40, 50, 63, 75, 90, 100, etc. |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Co 90° PPR - D25 | `PKO-CO90-PPR-D25` | `04-21-02-91` | `04-21-02-91.PKO-CO90-PPR-D25` |
| Co 45° PPR - D32 | `PKO-CO45-PPR-D32` | `04-21-02-91` | `04-21-02-91.PKO-CO45-PPR-D32` |
| Tê PPR - D25 | `PKO-TE-PPR-D25` | `04-21-02-91` | `04-21-02-91.PKO-TE-PPR-D25` |
| Thu PPR - D32xD25 | `PKO-THU-PPR-D32xD25` | `04-21-02-91` | `04-21-02-91.PKO-THU-PPR-D32xD25` |
| Mặt bích thép - D100 | `PKO-BICH-CS-D100` | `04-21-02-91` | `04-21-02-91.PKO-BICH-CS-D100` |

---

#### 🔷 22. VAN (VAN) - Valve

**FORMAT:** `VAN-{type}-{material}-D{size}[-{pressure}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại van | CONG (cổng), BI, BUOM, MOT (1 chiều), GIAM (giảm áp), AN (an toàn) |
| `material` | Vật liệu | GANG, DONG, INOX, PVC |
| `size` | Kích thước (mm) | 25, 32, 40, 50, 65, 80, 100, 150, 200 |
| `pressure` | Áp suất (optional) | PN10, PN16, PN25 |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Van cổng gang - D50 - PN16 | `VAN-CONG-GANG-D50-PN16` | `04-21-01-10` | `04-21-01-10.VAN-CONG-GANG-D50-PN16` |
| Van bi đồng - D25 | `VAN-BI-DONG-D25` | `04-21-01-10` | `04-21-01-10.VAN-BI-DONG-D25` |
| Van bướm - D150 - PN16 | `VAN-BUOM-GANG-D150-PN16` | `04-21-01-20` | `04-21-01-20.VAN-BUOM-GANG-D150-PN16` |
| Van 1 chiều - D80 | `VAN-MOT-GANG-D80` | `04-21-01-10` | `04-21-01-10.VAN-MOT-GANG-D80` |

---

#### 🔷 23. TRẦN (TRAN) - Ceiling

**FORMAT:** `TRAN-{type}-{material}[-{thickness}][-{finish}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại trần | CHIM (chìm), NOI (nổi), TREO, TAM (tấm) |
| `material` | Vật liệu | TC (thạch cao), NHOM (nhôm), GO (gỗ), NHUA (nhựa), KHOANG (khoáng) |
| `thickness` | Độ dày (optional) | 9MM, 12MM, 15MM |
| `finish` | Hoàn thiện (optional) | SON (sơn), TRANG (trắng), MAU (màu) |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Trần thạch cao chìm - 9mm | `TRAN-CHIM-TC-9MM` | `03-02-01-10` | `03-02-01-10.TRAN-CHIM-TC-9MM` |
| Trần thạch cao chìm - 12mm | `TRAN-CHIM-TC-12MM` | `03-02-01-10` | `03-02-01-10.TRAN-CHIM-TC-12MM` |
| Trần thạch cao nổi (hoa văn) | `TRAN-NOI-TC-12MM` | `03-02-01-20` | `03-02-01-20.TRAN-NOI-TC-12MM` |
| Trần nhôm tấm 600x600 | `TRAN-TAM-NHOM-600x600` | `03-02-01-20` | `03-02-01-20.TRAN-TAM-NHOM-600x600` |
| Trần nhôm thanh lam C84 | `TRAN-TAM-NHOM-C84` | `03-02-01-20` | `03-02-01-20.TRAN-TAM-NHOM-C84` |
| Trần sợi khoáng 600x600 | `TRAN-TAM-KHOANG-600x600` | `03-02-01-10` | `03-02-01-10.TRAN-TAM-KHOANG-600x600` |
| Trần gỗ công nghiệp | `TRAN-TAM-GO-CNGHIEP` | `03-02-01-20` | `03-02-01-20.TRAN-TAM-GO-CNGHIEP` |
| Trần gỗ tự nhiên | `TRAN-TAM-GO-TNHIEN` | `03-02-01-30` | `03-02-01-30.TRAN-TAM-GO-TNHIEN` |
| Trần nhựa PVC | `TRAN-TAM-NHUA-PVC` | `03-02-01-10` | `03-02-01-10.TRAN-TAM-NHUA-PVC` |

**Validation:** `material+type` ↔ `SEC L5`: TC-CHIM/KHOANG/NHUA→10, NHOM/GO-CN/NOI→20, GO-TN→30

---

#### 🔷 24. TƯỜNG XÂY (TUONG) - Masonry Wall

**FORMAT:** `TUONG-{type}-{material}-{thickness}[-{method}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại tường | XAY (xây), VACH (vách ngăn), PANEL |
| `material` | Vật liệu | GDAT (gạch đất), GONG (gạch ống), GBLOCK (gạch block), GAAC (gạch AAC/bê tông khí), TC (thạch cao), KINH (kính) |
| `thickness` | Độ dày (mm) | 100, 150, 200, 220, 75, 100 |
| `method` | Phương pháp (optional) | VM (vữa mác), KEO (keo dán) |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Tường gạch ống - 100mm | `TUONG-XAY-GONG-100` | `03-01-01-10` | `03-01-01-10.TUONG-XAY-GONG-100` |
| Tường gạch ống - 200mm | `TUONG-XAY-GONG-200` | `03-01-01-10` | `03-01-01-10.TUONG-XAY-GONG-200` |
| Tường gạch block - 150mm | `TUONG-XAY-GBLOCK-150` | `03-01-01-10` | `03-01-01-10.TUONG-XAY-GBLOCK-150` |
| Tường gạch AAC - 100mm - keo | `TUONG-XAY-GAAC-100-KEO` | `03-01-01-20` | `03-01-01-20.TUONG-XAY-GAAC-100-KEO` |
| Tường gạch AAC - 150mm - keo | `TUONG-XAY-GAAC-150-KEO` | `03-01-01-20` | `03-01-01-20.TUONG-XAY-GAAC-150-KEO` |
| Tường gạch AAC - 200mm - keo | `TUONG-XAY-GAAC-200-KEO` | `03-01-01-20` | `03-01-01-20.TUONG-XAY-GAAC-200-KEO` |
| Vách thạch cao 1 mặt - 75mm | `TUONG-VACH-TC-75-1M` | `03-01-02-10` | `03-01-02-10.TUONG-VACH-TC-75-1M` |
| Vách thạch cao 2 mặt - 100mm | `TUONG-VACH-TC-100-2M` | `03-01-02-10` | `03-01-02-10.TUONG-VACH-TC-100-2M` |
| Vách thạch cao chống cháy | `TUONG-VACH-TC-100-CC` | `03-01-02-30` | `03-01-02-30.TUONG-VACH-TC-100-CC` |
| Vách thạch cao chống ẩm | `TUONG-VACH-TC-100-CA` | `03-01-02-20` | `03-01-02-20.TUONG-VACH-TC-100-CA` |
| Vách kính văn phòng | `TUONG-VACH-KINH-10MM` | `03-01-03-20` | `03-01-03-20.TUONG-VACH-KINH-10MM` |
| Vách kính khung nhôm | `TUONG-VACH-KINH-KHUNG` | `03-01-03-20` | `03-01-03-20.TUONG-VACH-KINH-KHUNG` |

**Validation:** `material` ↔ `SEC L5`: GONG/GBLOCK/TC-STD→10, GAAC/TC-CA→20, TC-CC→30

---

#### 🔷 25. TRÁT (TRAT) - Plastering

**FORMAT:** `TRAT-{location}-{mortar}[-{thickness}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `location` | Vị trí | TUONG (tường), TRAN (trần), COT (cột), DAM (dầm) |
| `mortar` | Loại vữa | M50, M75, M100 (vữa xi măng), TP (trát phẳng), KH (kẻ hèm) |
| `thickness` | Độ dày (optional) | 10MM, 15MM, 20MM |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Trát tường trong - vữa M75 | `TRAT-TUONG-M75-15MM` | `03-01-04-10` | `03-01-04-10.TRAT-TUONG-M75-15MM` |
| Trát tường ngoài - vữa M100 | `TRAT-TUONG-M100-20MM` | `03-01-04-10` | `03-01-04-10.TRAT-TUONG-M100-20MM` |
| Trát trần - vữa M75 | `TRAT-TRAN-M75-10MM` | `03-01-04-10` | `03-01-04-10.TRAT-TRAN-M75-10MM` |
| Trát cột - vữa M75 | `TRAT-COT-M75-15MM` | `03-01-04-10` | `03-01-04-10.TRAT-COT-M75-15MM` |
| Trát granitô | `TRAT-TUONG-GRANITO` | `03-01-04-30` | `03-01-04-30.TRAT-TUONG-GRANITO` |

**Validation:** `mortar` ↔ `SEC L5`: M50/M75/M100→10, TP→20, GRANITO→30

---

#### 🔷 26. BẢ MATIT (BA) - Putty/Skim Coat

**FORMAT:** `BA-{location}-{type}-{coats}L`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `location` | Vị trí | TUONG (tường), TRAN (trần) |
| `type` | Loại bả | TRONG (trong nhà), NGOAI (ngoài trời), CC (chống cháy) |
| `coats` | Số lớp | 1, 2, 3 |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Bả matit tường trong - 2 lớp | `BA-TUONG-TRONG-2L` | `03-04-01-10` | `03-04-01-10.BA-TUONG-TRONG-2L` |
| Bả matit tường trong - 3 lớp | `BA-TUONG-TRONG-3L` | `03-04-01-20` | `03-04-01-20.BA-TUONG-TRONG-3L` |
| Bả matit trần - 2 lớp | `BA-TRAN-TRONG-2L` | `03-04-01-10` | `03-04-01-10.BA-TRAN-TRONG-2L` |
| Bả matit ngoài trời - 2 lớp | `BA-TUONG-NGOAI-2L` | `07-02-01-20` | `07-02-01-20.BA-TUONG-NGOAI-2L` |

**Validation:** `coats+location` ↔ `SEC L5`: 2L-TRONG→10, 3L→20, NGOAI→07-02

---

#### 🔷 27. LAN CAN (LC) - Railing/Balustrade

**FORMAT:** `LC-{location}-{material}-{height}[-{type}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `location` | Vị trí | CT (cầu thang), BC (ban công), MAI (mái) |
| `material` | Vật liệu | INOX, SAT (sắt), NHOM (nhôm), KINH (kính), GO (gỗ) |
| `height` | Chiều cao (mm) | 900, 1000, 1100, 1200 |
| `type` | Kiểu dáng (optional) | DOC (dọc), NGANG, CK (cắt khắc) |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Lan can cầu thang inox - 900mm | `LC-CT-INOX-900` | `03-06-01-10` | `03-06-01-10.LC-CT-INOX-900` |
| Lan can cầu thang inox kính | `LC-CT-INOX-900-KINH` | `03-06-01-20` | `03-06-01-20.LC-CT-INOX-900-KINH` |
| Lan can cầu thang gỗ tự nhiên | `LC-CT-GO-900-TNHIEN` | `03-06-01-30` | `03-06-01-30.LC-CT-GO-900-TNHIEN` |
| Lan can ban công inox | `LC-BC-INOX-1100` | `07-07-01-10` | `07-07-01-10.LC-BC-INOX-1100` |
| Lan can ban công kính cường lực | `LC-BC-KINH-1100-CL` | `07-07-01-20` | `07-07-01-20.LC-BC-KINH-1100-CL` |
| Lan can ban công nhôm đúc | `LC-BC-NHOM-1100-DUC` | `07-07-01-30` | `07-07-01-30.LC-BC-NHOM-1100-DUC` |

**Validation:** `location` ↔ `SEC L3`: CT→03-06, BC/MAI→07-07

---

#### 🔷 28. CẦU THANG (CTHANG) - Staircase

**FORMAT:** `CTHANG-{type}-{material}[-{finish}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại cầu thang | BO (bộ), XOAY, CAN (cantilevered) |
| `material` | Vật liệu bậc | BTCT, THEP, DAOP (đá ốp), GO (gỗ), KINH (kính) |
| `finish` | Hoàn thiện bậc (optional) | GR (granite), MB (marble), GO (gỗ), GACH (gạch) |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Cầu thang BTCT hoàn thiện đá granite | `CTHANG-BO-BTCT-GR` | `02-01-05-10` | `02-01-05-10.CTHANG-BO-BTCT-GR` |
| Cầu thang BTCT hoàn thiện đá marble | `CTHANG-BO-BTCT-MB` | `02-01-05-20` | `02-01-05-20.CTHANG-BO-BTCT-MB` |
| Cầu thang thép bậc gỗ | `CTHANG-BO-THEP-GO` | `02-01-05-20` | `02-01-05-20.CTHANG-BO-THEP-GO` |
| Cầu thang xoay thép | `CTHANG-XOAY-THEP` | `02-01-05-30` | `02-01-05-30.CTHANG-XOAY-THEP` |
| Cầu thang kính không khung | `CTHANG-CAN-KINH` | `02-01-05-30` | `02-01-05-30.CTHANG-CAN-KINH` |

**Validation:** `type+material` ↔ `SEC L5`: BTCT-GR/GACH→10, BTCT-MB/THEP-GO→20, XOAY/CAN→30

---

#### 🔷 29. MÁI (MAI) - Roofing

**FORMAT:** `MAI-{type}-{material}[-{slope}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại mái | DOC (dốc), BANG (bằng), MAI (mái hắt) |
| `material` | Vật liệu | TON (tôn), NGOI (ngói), BTCT, KINH (kính), POLY (polycarbonate) |
| `slope` | Độ dốc (optional) | 15, 30, 45 (độ) |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Mái tôn kẽm - dày 0.45mm | `MAI-DOC-TON-0.45` | `07-04-01-10` | `07-04-01-10.MAI-DOC-TON-0.45` |
| Mái tôn kẽm - dày 0.5mm | `MAI-DOC-TON-0.5` | `07-04-01-10` | `07-04-01-10.MAI-DOC-TON-0.5` |
| Mái tôn mạ màu - 0.45mm | `MAI-DOC-TON-MAU-0.45` | `07-04-01-10` | `07-04-01-10.MAI-DOC-TON-MAU-0.45` |
| Mái ngói xi măng | `MAI-DOC-NGOI-XM` | `07-04-02-10` | `07-04-02-10.MAI-DOC-NGOI-XM` |
| Mái ngói đất nung | `MAI-DOC-NGOI-DAT` | `07-04-02-20` | `07-04-02-20.MAI-DOC-NGOI-DAT` |
| Mái ngói men | `MAI-DOC-NGOI-MEN` | `07-04-02-30` | `07-04-02-30.MAI-DOC-NGOI-MEN` |
| Mái kính cường lực | `MAI-BANG-KINH-CL` | `07-04-03-30` | `07-04-03-30.MAI-BANG-KINH-CL` |
| Mái polycarbonate rỗng | `MAI-DOC-POLY-RONG` | `07-04-03-10` | `07-04-03-10.MAI-DOC-POLY-RONG` |

**Validation:** `material` ↔ `SEC L5`: TON/POLY-RONG→10, NGOI-XM→10, NGOI-DAT→20, NGOI-MEN/KINH→30

---

#### 🔷 30. CÁCH NHIỆT / CÁCH ÂM (CNCA) - Insulation

**FORMAT:** `CNCA-{purpose}-{material}-{thickness}`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `purpose` | Mục đích | CN (cách nhiệt), CA (cách âm), CNCA (cả hai) |
| `material` | Vật liệu | BONG (bông thủy tinh), XPS, EPS, PU, ROCKWOOL |
| `thickness` | Độ dày (mm) | 25, 50, 75, 100, 150 |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Cách nhiệt bông thủy tinh - 50mm | `CNCA-CN-BONG-50` | `07-05-01-10` | `07-05-01-10.CNCA-CN-BONG-50` |
| Cách nhiệt bông thủy tinh - 100mm | `CNCA-CN-BONG-100` | `07-05-01-10` | `07-05-01-10.CNCA-CN-BONG-100` |
| Cách nhiệt XPS - 50mm | `CNCA-CN-XPS-50` | `07-05-01-20` | `07-05-01-20.CNCA-CN-XPS-50` |
| Cách nhiệt PU phun - 30mm | `CNCA-CN-PU-30` | `07-05-01-30` | `07-05-01-30.CNCA-CN-PU-30` |
| Cách âm Rockwool - 50mm | `CNCA-CA-ROCKWOOL-50` | `07-05-02-20` | `07-05-02-20.CNCA-CA-ROCKWOOL-50` |
| Cách âm sàn - 25mm | `CNCA-CA-XPS-25` | `07-05-02-10` | `07-05-02-10.CNCA-CA-XPS-25` |

**Validation:** `material` ↔ `SEC L5`: BONG→10, XPS/EPS/ROCKWOOL→20, PU→30

---

#### 🔷 31. ỐP ALUMINIUM / CLADDING (OPA) - Façade Cladding

**FORMAT:** `OPA-{type}-{thickness}[-{finish}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại ốp | ACP (aluminium composite), NHOM (nhôm tấm), DA (đá treo), GOM (gốm), GACH |
| `thickness` | Độ dày (mm) | 3, 4, 5 (ACP); 20, 30 (đá) |
| `finish` | Bề mặt (optional) | BONG (bóng), MO (mờ), VAN (vân gỗ) |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Ốp ACP - 4mm - bóng | `OPA-ACP-4-BONG` | `07-02-01-10` | `07-02-01-10.OPA-ACP-4-BONG` |
| Ốp ACP - 4mm - vân gỗ | `OPA-ACP-4-VAN` | `07-02-01-20` | `07-02-01-20.OPA-ACP-4-VAN` |
| Ốp đá granite treo - 30mm | `OPA-DA-GR-30` | `07-02-02-20` | `07-02-02-20.OPA-DA-GR-30` |
| Ốp đá marble treo - 20mm | `OPA-DA-MB-20` | `07-02-02-30` | `07-02-02-30.OPA-DA-MB-20` |
| Ốp gốm Terracotta | `OPA-GOM-TER` | `07-02-03-20` | `07-02-03-20.OPA-GOM-TER` |
| Lam chắn nắng nhôm | `OPA-NHOM-LAM` | `07-02-04-20` | `07-02-04-20.OPA-NHOM-LAM` |

**Validation:** `type` ↔ `SEC L4`: ACP→07-02-01, DA→07-02-02, GOM→07-02-03, LAM→07-02-04

---

#### 🔷 32. ỐNG THOÁT (OT) - Drainage Pipe

**FORMAT:** `OT-{type}-{material}-D{size}`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại ống | THAI (thải), MUA (mưa), THONGHOI (thông hơi) |
| `material` | Vật liệu | PVC, HDPE, GANG (gang dẻo) |
| `size` | Đường kính (mm) | 49, 60, 75, 90, 110, 160, 200, 250, 315 |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Ống PVC thoát thải - D60 | `OT-THAI-PVC-D60` | `04-22-02-10` | `04-22-02-10.OT-THAI-PVC-D60` |
| Ống PVC thoát thải - D110 | `OT-THAI-PVC-D110` | `04-22-02-10` | `04-22-02-10.OT-THAI-PVC-D110` |
| Ống PVC thoát thải - D160 | `OT-THAI-PVC-D160` | `04-22-02-10` | `04-22-02-10.OT-THAI-PVC-D160` |
| Ống PVC thoát mưa - D110 | `OT-MUA-PVC-D110` | `04-23-02-10` | `04-23-02-10.OT-MUA-PVC-D110` |
| Ống PVC thoát mưa - D200 | `OT-MUA-PVC-D200` | `04-23-02-10` | `04-23-02-10.OT-MUA-PVC-D200` |
| Ống HDPE thoát thải - D160 | `OT-THAI-HDPE-D160` | `04-22-02-20` | `04-22-02-20.OT-THAI-HDPE-D160` |
| Ống gang dẻo thoát - D100 | `OT-THAI-GANG-D100` | `04-22-02-30` | `04-22-02-30.OT-THAI-GANG-D100` |
| Ống thông hơi PVC - D49 | `OT-THONGHOI-PVC-D49` | `04-22-02-10` | `04-22-02-10.OT-THONGHOI-PVC-D49` |

**Validation:** `material` ↔ `SEC L5`: PVC→10, HDPE→20, GANG→30

---

#### 🔷 33. ỐNG LUỒN DÂY (OLD) - Conduit

**FORMAT:** `OLD-{type}-{material}-D{size}`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại ống | AM (âm), NOI (nổi), SAN (sàn) |
| `material` | Vật liệu | PVC, THEP (thép), INOX, FLEX (ruột gà) |
| `size` | Đường kính (mm) | 16, 20, 25, 32, 40, 50 |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Ống luồn PVC âm tường - D20 | `OLD-AM-PVC-D20` | `04-01-03-10` | `04-01-03-10.OLD-AM-PVC-D20` |
| Ống luồn PVC âm sàn - D25 | `OLD-SAN-PVC-D25` | `04-01-03-10` | `04-01-03-10.OLD-SAN-PVC-D25` |
| Ống luồn thép nổi - D20 | `OLD-NOI-THEP-D20` | `04-01-03-20` | `04-01-03-20.OLD-NOI-THEP-D20` |
| Ống ruột gà - D20 | `OLD-AM-FLEX-D20` | `04-01-03-10` | `04-01-03-10.OLD-AM-FLEX-D20` |
| Ống luồn inox - D25 | `OLD-NOI-INOX-D25` | `04-01-03-30` | `04-01-03-30.OLD-NOI-INOX-D25` |

**Validation:** `material` ↔ `SEC L5`: PVC/FLEX→10, THEP→20, INOX→30

---

#### 🔷 34. TỦ ĐIỆN (TBD) - Electrical Panel

**FORMAT:** `TBD-{type}-{size}[-{material}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại tủ | MSB (tủ chính), DB (tủ phân phối), MCC (tủ điều khiển), ATS, CAPEX (capacitor) |
| `size` | Công suất/Số lộ | 100A, 200A, 400A, 800A, 1600A, 2500A / 12LO, 24LO, 36LO |
| `material` | Vỏ tủ (optional) | THEP (thép sơn tĩnh điện), INOX, NHUA (nhựa) |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Tủ MSB - 800A | `TBD-MSB-800A-THEP` | `04-01-01-01` | `04-01-01-01.TBD-MSB-800A-THEP` |
| Tủ MSB - 1600A | `TBD-MSB-1600A-THEP` | `04-01-01-01` | `04-01-01-01.TBD-MSB-1600A-THEP` |
| Tủ MSB - 2500A | `TBD-MSB-2500A-THEP` | `04-01-01-01` | `04-01-01-01.TBD-MSB-2500A-THEP` |
| Tủ DB - 24 lộ | `TBD-DB-24LO-THEP` | `04-01-01-02` | `04-01-01-02.TBD-DB-24LO-THEP` |
| Tủ DB nhựa - 12 lộ | `TBD-DB-12LO-NHUA` | `04-01-01-02` | `04-01-01-02.TBD-DB-12LO-NHUA` |
| Tủ ATS - 400A | `TBD-ATS-400A` | `04-03-01-02` | `04-03-01-02.TBD-ATS-400A` |
| Tủ MCC - 200A | `TBD-MCC-200A` | `04-01-01-02` | `04-01-01-02.TBD-MCC-200A` |
| Tủ tụ bù - 100kVAr | `TBD-CAPEX-100KVAR` | `04-01-01-03` | `04-01-01-03.TBD-CAPEX-100KVAR` |

**Validation:** `type` ↔ `SEC L5`: MSB→01, DB/MCC→02, CAPEX→03

---

#### 🔷 35. Ổ CẮM / CÔNG TẮC (OCCT) - Socket/Switch

**FORMAT:** `OCCT-{type}-{config}[-{brand}][-{grade}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại | OC (ổ cắm), CT (công tắc), COM (combo) |
| `config` | Cấu hình | 1, 2, 3, 4 (số ổ/công tắc), USB, LAN, TEL |
| `brand` | Thương hiệu (optional) | PANASONIC, SCHNEIDER, LEGRAND, SINO, VN |
| `grade` | Phẩm cấp (optional) | STD, PRE, LUX |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Ổ cắm đôi - Panasonic | `OCCT-OC-2-PANASONIC-STD` | `04-01-04-10` | `04-01-04-10.OCCT-OC-2-PANASONIC-STD` |
| Ổ cắm đôi có USB | `OCCT-OC-2USB-PANASONIC-PRE` | `04-01-04-20` | `04-01-04-20.OCCT-OC-2USB-PANASONIC-PRE` |
| Công tắc 1 chiều | `OCCT-CT-1-PANASONIC-STD` | `04-01-04-10` | `04-01-04-10.OCCT-CT-1-PANASONIC-STD` |
| Công tắc 2 chiều | `OCCT-CT-2WAY-PANASONIC-STD` | `04-01-04-10` | `04-01-04-10.OCCT-CT-2WAY-PANASONIC-STD` |
| Công tắc cảm ứng | `OCCT-CT-SENSOR-SCHNEIDER-LUX` | `04-01-04-30` | `04-01-04-30.OCCT-CT-SENSOR-SCHNEIDER-LUX` |
| Ổ mạng LAN Cat6 | `OCCT-OC-LAN-CAT6` | `08-01-03-10` | `08-01-03-10.OCCT-OC-LAN-CAT6` |
| Ổ điện thoại | `OCCT-OC-TEL` | `08-01-03-10` | `08-01-03-10.OCCT-OC-TEL` |

**Validation:** `grade` ↔ `SEC L5`: STD→10, PRE→20, LUX/SENSOR→30; LAN/TEL→08-01

---

#### 🔷 36. MIỆNG GIÓ (MG) - Air Terminal

**FORMAT:** `MG-{type}-{size}[-{material}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại miệng gió | CAP (cấp), HOI (hồi), TRAN (trần), TUONG (tường), JET |
| `size` | Kích thước (mm) | 150x150, 300x150, 450x450, 600x600, D150, D250 |
| `material` | Vật liệu (optional) | NHOM (nhôm), THEP (thép), ABS |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Miệng gió cấp 4 hướng - 300x300 | `MG-CAP-300x300-NHOM` | `04-34-03-10` | `04-34-03-10.MG-CAP-300x300-NHOM` |
| Miệng gió cấp 4 hướng - 600x600 | `MG-CAP-600x600-NHOM` | `04-34-03-10` | `04-34-03-10.MG-CAP-600x600-NHOM` |
| Miệng gió hồi trần - 450x450 | `MG-HOI-450x450-NHOM` | `04-34-03-10` | `04-34-03-10.MG-HOI-450x450-NHOM` |
| Miệng gió tuyến tính - 1200x100 | `MG-CAP-1200x100-NHOM` | `04-34-03-20` | `04-34-03-20.MG-CAP-1200x100-NHOM` |
| Miệng gió jet - D250 | `MG-JET-D250-THEP` | `04-34-03-30` | `04-34-03-30.MG-JET-D250-THEP` |
| Louver chắn mưa - 600x600 | `MG-TUONG-600x600-NHOM` | `04-34-03-10` | `04-34-03-10.MG-TUONG-600x600-NHOM` |

**Validation:** `type` ↔ `SEC L5`: CAP/HOI/TUONG→10, LINEAR→20, JET→30

---

#### 🔷 37. QUẠT (QUAT) - Fan

**FORMAT:** `QUAT-{type}-{flow}[-{pressure}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại quạt | HUT (hút), THOI (thổi), HK (hút khói), TA (tăng áp), LT (ly tâm), TRAN (trần) |
| `flow` | Lưu lượng (m³/h) | 500, 1000, 2000, 5000, 10000, 20000 |
| `pressure` | Cột áp (Pa, optional) | 100, 200, 500, 800, 1000 |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Quạt hút toilet - 100m³/h | `QUAT-HUT-100` | `04-34-01-10` | `04-34-01-10.QUAT-HUT-100` |
| Quạt thông gió - 2000m³/h | `QUAT-THOI-2000` | `04-34-01-10` | `04-34-01-10.QUAT-THOI-2000` |
| Quạt ly tâm - 5000m³/h - 500Pa | `QUAT-LT-5000-500PA` | `04-34-01-20` | `04-34-01-20.QUAT-LT-5000-500PA` |
| Quạt hút khói - 15000m³/h | `QUAT-HK-15000` | `04-10-04-01` | `04-10-04-01.QUAT-HK-15000` |
| Quạt hút khói - 30000m³/h | `QUAT-HK-30000` | `04-10-04-01` | `04-10-04-01.QUAT-HK-30000` |
| Quạt tăng áp cầu thang - 10000m³/h | `QUAT-TA-10000` | `04-10-04-01` | `04-10-04-01.QUAT-TA-10000` |
| Quạt trần - 1400mm | `QUAT-TRAN-1400` | `04-34-01-10` | `04-34-01-10.QUAT-TRAN-1400` |

**Validation:** `type` ↔ `SEC Code`: HK/TA→04-10-04, HUT/THOI/LT/TRAN→04-34-01

---

#### 🔷 38. ĐẦU BÁO / THIẾT BỊ PCCC (PCCC) - Fire Detection

**FORMAT:** `PCCC-{type}-{detector}[-{brand}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại | DBKHOI (đầu báo khói), DBNHIET (đầu báo nhiệt), NUTNHAN, COIDEN, TUTT (tủ trung tâm) |
| `detector` | Phân loại | QUANG (quang điện), ION, DK (địa chỉ), TT (thường) |
| `brand` | Thương hiệu (optional) | HOCHIKI, NOTIFIER, BOSCH, GST, VN |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Đầu báo khói quang điện | `PCCC-DBKHOI-QUANG-TT` | `04-10-01-03` | `04-10-01-03.PCCC-DBKHOI-QUANG-TT` |
| Đầu báo khói địa chỉ | `PCCC-DBKHOI-QUANG-DK` | `04-10-01-03` | `04-10-01-03.PCCC-DBKHOI-QUANG-DK` |
| Đầu báo nhiệt cố định | `PCCC-DBNHIET-CD-TT` | `04-10-01-03` | `04-10-01-03.PCCC-DBNHIET-CD-TT` |
| Đầu báo nhiệt gia tăng | `PCCC-DBNHIET-GT-TT` | `04-10-01-03` | `04-10-01-03.PCCC-DBNHIET-GT-TT` |
| Nút nhấn báo cháy | `PCCC-NUTNHAN-TT` | `04-10-01-03` | `04-10-01-03.PCCC-NUTNHAN-TT` |
| Còi đèn báo cháy | `PCCC-COIDEN-TT` | `04-10-01-03` | `04-10-01-03.PCCC-COIDEN-TT` |
| Tủ trung tâm báo cháy - 4 loop | `PCCC-TUTT-4LOOP` | `04-10-01-01` | `04-10-01-01.PCCC-TUTT-4LOOP` |
| Tủ trung tâm báo cháy - 8 loop | `PCCC-TUTT-8LOOP` | `04-10-01-01` | `04-10-01-01.PCCC-TUTT-8LOOP` |

**Validation:** `type` ↔ `SEC L5`: TUTT→01, DB/NUT/COI→03

---

#### 🔷 39. SPRINKLER (SPK) - Fire Sprinkler

**FORMAT:** `SPK-{type}-{temp}[-{orientation}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại | TT (tiêu chuẩn), PHUR (phun sương), DRENCHER |
| `temp` | Nhiệt độ (°C) | 57, 68, 79, 93, 141 |
| `orientation` | Hướng phun (optional) | UP (thẳng đứng), PEND (treo ngược), SW (ngang) |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Sprinkler 68°C - treo ngược | `SPK-TT-68-PEND` | `04-10-02-03` | `04-10-02-03.SPK-TT-68-PEND` |
| Sprinkler 68°C - thẳng đứng | `SPK-TT-68-UP` | `04-10-02-03` | `04-10-02-03.SPK-TT-68-UP` |
| Sprinkler 79°C | `SPK-TT-79-PEND` | `04-10-02-03` | `04-10-02-03.SPK-TT-79-PEND` |
| Sprinkler 93°C (khu nấu) | `SPK-TT-93-PEND` | `04-10-02-03` | `04-10-02-03.SPK-TT-93-PEND` |
| Sprinkler phun sương | `SPK-PHUR-68` | `04-10-02-03` | `04-10-02-03.SPK-PHUR-68` |

**Validation:** All → `SEC=04-10-02-03`

---

#### 🔷 40. HỘP CHỮA CHÁY (HCC) - Fire Cabinet

**FORMAT:** `HCC-{type}-{size}[-{equipment}]`

| Param | Ý nghĩa | Giá trị |
|:---|:---|:---|
| `type` | Loại | VT (vách tường), CUON (cuộn vòi), TRU (trụ nước) |
| `size` | Kích thước | 500x600, 600x650, 600x700, D65, D100, D150 |
| `equipment` | Trang bị (optional) | 1VOI (1 vòi), 2VOI (2 vòi), BINH (bình chữa cháy) |

| Tên Normalized | Spec Code | SEC Code | Full Code |
|:---|:---|:---|:---|
| Hộp chữa cháy vách tường - D50 | `HCC-VT-D50-1VOI` | `04-10-02-03` | `04-10-02-03.HCC-VT-D50-1VOI` |
| Hộp chữa cháy vách tường - D65 | `HCC-VT-D65-1VOI` | `04-10-02-03` | `04-10-02-03.HCC-VT-D65-1VOI` |
| Hộp chữa cháy 2 vòi - D50+D65 | `HCC-VT-D50D65-2VOI` | `04-10-02-03` | `04-10-02-03.HCC-VT-D50D65-2VOI` |
| Cuộn vòi chữa cháy - D25 | `HCC-CUON-D25` | `04-10-02-03` | `04-10-02-03.HCC-CUON-D25` |
| Trụ nước ngoài nhà - D100 | `HCC-TRU-D100` | `04-10-02-03` | `04-10-02-03.HCC-TRU-D100` |
| Trụ nước 2 họng - D100+D65 | `HCC-TRU-D100D65` | `04-10-02-03` | `04-10-02-03.HCC-TRU-D100D65` |

---

### 9.4 BẢNG TÓM TẮT VALIDATION RULES

| # | PREFIX | Format | SEC Code | L5 Mapping |
|:---:|:---|:---|:---|:---|
| 1 | `BT` | `BT-{grade}-{method}[-{add}]` | `01-03-01`, `02-01-01` | TC→10, BC→20, BT→30 |
| 2 | `TH` | `TH-D{dia}-{grade}` | `01-03-03`, `02-01-03` | D≤10→10, D≤18→18, D>18→19 |
| 3 | `THEP` | `THEP-{profile}-{size}` | `02-02-04` | - |
| 4 | `VK` | `VK-{mat}-{height}` | `01-03-02`, `02-01-02` | H4→10, H8/H16→20, H50→30 |
| 5 | `COC` | `COC-{type}-D{dia}-L{len}` | `01-02-01` | EP/DONG→10, KHOAN→20 |
| 6 | `DAT` | `DAT-{act}-{grade}-{method}` | `01-01-01`, `10-01-01` | C1→10, C3→12, DA→13 |
| 7 | `ONG` | `ONG-{mat}-D{size}-{conn}[-{PN}]` | `04-21-02` | NH/DAN→10, REN→20, HAN/FL→30 |
| 8 | `OT` | `OT-{type}-{mat}-D{size}` | `04-22-02`, `04-23-02` | PVC→10, HDPE→20, GANG→30 |
| 9 | `CAP` | `CAP-{cond}-{size}-{ins}[-{arm}][-{shd}]` | `04-01-02` | PVC→10/20, FR→30, LSZH→31, SWA→40, SC→50, MI→60 |
| 10 | `OLD` | `OLD-{type}-{mat}-D{size}` | `04-01-03` | PVC/FLEX→10, THEP→20, INOX→30 |
| 11 | `GIO` | `GIO-{mat}-{size}` | `04-34-02` | - |
| 12 | `MG` | `MG-{type}-{size}[-{mat}]` | `04-34-03` | CAP/HOI→10, LINEAR→20, JET→30 |
| 13 | `QUAT` | `QUAT-{type}-{flow}[-{pressure}]` | `04-34-01`, `04-10-04` | HK/TA→04-10-04 |
| 14 | `GACH` | `GACH-{type}-{size}-{grade}` | `03-03-01` | STD→10, PRE→20, LUX→30 |
| 15 | `DA` | `DA-{type}-{size}-{finish}` | `03-03-02` | NT→10, GR→20, MB→30 |
| 16 | `SON` | `SON-{type}-{coats}L[-{loc}]` | `03-04-05`, `07-02-05` | 2L→10, 3L→20, EP/PU→30 |
| 17 | `BA` | `BA-{loc}-{type}-{coats}L` | `03-04-01`, `07-02-01` | 2L-TRONG→10, 3L→20 |
| 18 | `KINH` | `KINH-{type}-{thick}` / `KINH-HOP-{cfg}` | `07-01-04` | TRONG→10, CL/HOP→20, LOW→30 |
| 19 | `CUA` | `CUA-{type}-{mat}-{size}[-{spec}]` | `03-05-01`, `07-01-02`, `07-06-02` | CC→30 |
| 20 | `TBVS` | `TBVS-{item}-{brand}-{grade}` | `03-07-01~03` | STD→10, PRE→20, LUX→30 |
| 21 | `DH` | `DH-{type}-{cap}[-{model}]` | `04-31~33` | SPLIT→33, VRV→32, CHILLER→31 |
| 22 | `BOM` | `BOM-{type}-{flow}M3-{head}M` | `04-24-01`, `04-10-02` | PCCC→04-10-02 |
| 23 | `TM` | `TM-{type}-{cap}KG-{speed}` | `04-51~54` | KHACH→51, HANG/BV→52, PCCC→54 |
| 24 | `DEN` | `DEN-{type}-{power}W[-{tech}]` | `04-05-03`, `11-06-03` | DUONG→11-06 |
| 25 | `CT` | `CT-{type}-{thick}[-{layers}L]` | `07-03-01` | BIT/XI→10, PVC/PU→20, KT→30 |
| 26 | `PKO` | `PKO-{fitting}-{mat}-D{size}` | `04-21-02-91` | - |
| 27 | `VAN` | `VAN-{type}-{mat}-D{size}[-{PN}]` | `04-21-01` | - |
| 28 | `TRAN` | `TRAN-{type}-{mat}[-{thick}][-{fin}]` | `03-02-01` | TC/KHOANG→10, NHOM/GO-CN→20, GO-TN→30 |
| 29 | `TUONG` | `TUONG-{type}-{mat}-{thick}[-{meth}]` | `03-01-01~03` | GONG/GBLOCK→10, GAAC→20, TC-CC→30 |
| 30 | `TRAT` | `TRAT-{loc}-{mortar}[-{thick}]` | `03-01-04` | M50~M100→10, GRANITO→30 |
| 31 | `LC` | `LC-{loc}-{mat}-{height}[-{type}]` | `03-06-01`, `07-07-01` | CT→03-06, BC→07-07 |
| 32 | `CTHANG` | `CTHANG-{type}-{mat}[-{finish}]` | `02-01-05` | BTCT-GR→10, MB/THEP→20, XOAY→30 |
| 33 | `MAI` | `MAI-{type}-{mat}[-{slope}]` | `07-04-01~03` | TON→10, NGOI-XM→10, NGOI-DAT→20, KINH→30 |
| 34 | `CNCA` | `CNCA-{purpose}-{mat}-{thick}` | `07-05-01~02` | BONG→10, XPS/ROCKWOOL→20, PU→30 |
| 35 | `OPA` | `OPA-{type}-{thick}[-{finish}]` | `07-02-01~04` | ACP→01, DA→02, GOM→03, LAM→04 |
| 36 | `TBD` | `TBD-{type}-{size}[-{mat}]` | `04-01-01`, `04-03-01` | MSB→01, DB/MCC→02, CAPEX→03 |
| 37 | `OCCT` | `OCCT-{type}-{cfg}[-{brand}][-{grade}]` | `04-01-04`, `08-01-03` | STD→10, PRE→20, SENSOR→30 |
| 38 | `PCCC` | `PCCC-{type}-{detector}[-{brand}]` | `04-10-01` | TUTT→01, DB/NUT/COI→03 |
| 39 | `SPK` | `SPK-{type}-{temp}[-{orient}]` | `04-10-02-03` | All→03 |
| 40 | `HCC` | `HCC-{type}-{size}[-{equip}]` | `04-10-02-03` | All→03 |

---

### 9.5 VÍ DỤ ÁP DỤNG

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  VÍ DỤ 1: "Bê tông móng - M300 - thương phẩm"                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  Tên Normalized:  Bê tông móng - M300 - thương phẩm                         │
│  → PREFIX:        BT                                                         │
│  → grade:         M300                                                       │
│  → method:        BC (bơm cần = thương phẩm)                                │
│  → Spec Code:     BT-M300-BC                                                │
│  → SEC Code:      01-03-01-20 (method=BC → L5=20)                           │
│  → Full Code:     01-03-01-20.BT-M300-BC                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  VÍ DỤ 2: "Lắp đặt Cáp - Cu/XLPE/PVC - 4x300mm2"                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  Tên Normalized:  Lắp đặt Cáp - Cu/XLPE/PVC - 4x300mm2                      │
│  → PREFIX:        CAP                                                        │
│  → conductor:     CU                                                         │
│  → size:          4C300                                                      │
│  → insulation:    PVC                                                        │
│  → Spec Code:     CAP-CU-4C300-PVC                                          │
│  → SEC Code:      04-01-02-20 (size>16 + PVC → L5=20)                       │
│  → Full Code:     04-01-02-20.CAP-CU-4C300-PVC                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  VÍ DỤ 3: "Lắp đặt Cáp - Cu/XLPE/PVC/FR - 4x300mm2"                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  Tên Normalized:  Lắp đặt Cáp - Cu/XLPE/PVC/FR - 4x300mm2                   │
│  → PREFIX:        CAP                                                        │
│  → conductor:     CU                                                         │
│  → size:          4C300                                                      │
│  → insulation:    FR (chống cháy)                                           │
│  → Spec Code:     CAP-CU-4C300-FR                                           │
│  → SEC Code:      04-01-02-30 (FR → L5=30)                                  │
│  → Full Code:     04-01-02-30.CAP-CU-4C300-FR                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## X. NORMALIZED NAME FORMAT - CHUẨN HÓA TÊN CÔNG TÁC

### 10.1 Cấu trúc tên chuẩn hóa

```
FORMAT: [Công tác] - [Vật liệu/Loại] - [Quy cách chi tiết]
```

### 10.2 Bảng Mapping hoàn chỉnh

#### A. NHÓM KẾT CẤU (STRUCTURAL)

| Tên Normalized | SEC Code | Spec Code | Full Code |
|:---|:---|:---|:---|
| Bê tông móng - M200 - thủ công | `01-03-01-10` | `BT-M200-TC` | `01-03-01-10.BT-M200-TC` |
| Bê tông móng - M300 - thương phẩm | `01-03-01-20` | `BT-M300-BC` | `01-03-01-20.BT-M300-BC` |
| Bê tông cột - M350 - bơm tĩnh | `02-01-01-30` | `BT-M350-BT` | `02-01-01-30.BT-M350-BT` |
| Thép móng - CB400 - Φ16 | `01-03-03-18` | `TH-D16-CB400` | `01-03-03-18.TH-D16-CB400` |
| Thép cột - CB500 - Φ25 | `02-01-03-19` | `TH-D25-CB500` | `02-01-03-19.TH-D25-CB500` |
| Ván khuôn gỗ - móng | `01-03-02-10` | `VK-GO-H4` | `01-03-02-10.VK-GO-H4` |
| Ván khuôn thép - cột cao tầng | `02-01-02-20` | `VK-THEP-H16` | `02-01-02-20.VK-THEP-H16` |
| Cọc ép - D350 - 15m | `01-02-01-10` | `COC-EP-D350-L15` | `01-02-01-10.COC-EP-D350-L15` |
| Cọc khoan nhồi - D800 - 25m | `01-02-01-20` | `COC-KHOAN-D800-L25` | `01-02-01-20.COC-KHOAN-D800-L25` |
| Cầu thang BTCT - đá granite | `02-01-05-10` | `CTHANG-BO-BTCT-GR` | `02-01-05-10.CTHANG-BO-BTCT-GR` |
| Cầu thang thép - bậc gỗ | `02-01-05-20` | `CTHANG-BO-THEP-GO` | `02-01-05-20.CTHANG-BO-THEP-GO` |

#### B. NHÓM HOÀN THIỆN (FINISHING)

| Tên Normalized | SEC Code | Spec Code | Full Code |
|:---|:---|:---|:---|
| Tường gạch ống - 100mm | `03-01-01-10` | `TUONG-XAY-GONG-100` | `03-01-01-10.TUONG-XAY-GONG-100` |
| Tường gạch AAC - 150mm - keo | `03-01-01-20` | `TUONG-XAY-GAAC-150-KEO` | `03-01-01-20.TUONG-XAY-GAAC-150-KEO` |
| Vách thạch cao - 100mm - 2 mặt | `03-01-02-10` | `TUONG-VACH-TC-100-2M` | `03-01-02-10.TUONG-VACH-TC-100-2M` |
| Vách thạch cao - chống cháy | `03-01-02-30` | `TUONG-VACH-TC-100-CC` | `03-01-02-30.TUONG-VACH-TC-100-CC` |
| Trát tường - vữa M75 - 15mm | `03-01-04-10` | `TRAT-TUONG-M75-15MM` | `03-01-04-10.TRAT-TUONG-M75-15MM` |
| Trần thạch cao chìm - 9mm | `03-02-01-10` | `TRAN-CHIM-TC-9MM` | `03-02-01-10.TRAN-CHIM-TC-9MM` |
| Trần nhôm tấm - 600x600 | `03-02-01-20` | `TRAN-TAM-NHOM-600x600` | `03-02-01-20.TRAN-TAM-NHOM-600x600` |
| Gạch granite - 600x600 - Premium | `03-03-01-20` | `GACH-GR-600x600-PRE` | `03-03-01-20.GACH-GR-600x600-PRE` |
| Đá granite - 600x600 - mài bóng | `03-03-02-20` | `DA-GR-600x600-MAI` | `03-03-02-20.DA-GR-600x600-MAI` |
| Bả matit tường - 2 lớp | `03-04-01-10` | `BA-TUONG-TRONG-2L` | `03-04-01-10.BA-TUONG-TRONG-2L` |
| Sơn nước tường - 2 lớp | `03-04-05-10` | `SON-NC-2L-TRONG` | `03-04-05-10.SON-NC-2L-TRONG` |
| Sơn epoxy sàn - 2 lớp | `03-04-05-30` | `SON-EP-2L` | `03-04-05-30.SON-EP-2L` |
| Cửa gỗ HDF - 900x2100 | `03-05-01-10` | `CUA-DI-GO-900x2100-HDF` | `03-05-01-10.CUA-DI-GO-900x2100-HDF` |
| Cửa chống cháy - 900x2100 | `03-05-01-30` | `CUA-DI-THEP-900x2100-CC` | `03-05-01-30.CUA-DI-THEP-900x2100-CC` |
| Lan can cầu thang - inox | `03-06-01-10` | `LC-CT-INOX-900` | `03-06-01-10.LC-CT-INOX-900` |
| Bồn cầu TOTO - cao cấp | `03-07-01-20` | `TBVS-WC-TOTO-PRE` | `03-07-01-20.TBVS-WC-TOTO-PRE` |

#### C. NHÓM MẶT DỰNG & VỎ BAO (ENVELOPE)

| Tên Normalized | SEC Code | Spec Code | Full Code |
|:---|:---|:---|:---|
| Kính cường lực - 10mm | `07-01-04-20` | `KINH-CL-10` | `07-01-04-20.KINH-CL-10` |
| Kính hộp Low-E - 6+12+6 | `07-01-04-30` | `KINH-HOP-6+12A+6-LOW` | `07-01-04-30.KINH-HOP-6+12A+6-LOW` |
| Cửa sổ nhôm - 1500x1500 | `07-01-02-20` | `CUA-SO-NHOM-1500x1500` | `07-01-02-20.CUA-SO-NHOM-1500x1500` |
| Ốp ACP - 4mm - bóng | `07-02-01-10` | `OPA-ACP-4-BONG` | `07-02-01-10.OPA-ACP-4-BONG` |
| Ốp đá granite treo - 30mm | `07-02-02-20` | `OPA-DA-GR-30` | `07-02-02-20.OPA-DA-GR-30` |
| Chống thấm màng bitum - 3mm | `07-03-01-10` | `CT-BIT-3MM` | `07-03-01-10.CT-BIT-3MM` |
| Chống thấm PU - 2mm | `07-03-01-20` | `CT-PU-2MM` | `07-03-01-20.CT-PU-2MM` |
| Mái tôn mạ màu - 0.45mm | `07-04-01-10` | `MAI-DOC-TON-MAU-0.45` | `07-04-01-10.MAI-DOC-TON-MAU-0.45` |
| Mái ngói đất nung | `07-04-02-20` | `MAI-DOC-NGOI-DAT` | `07-04-02-20.MAI-DOC-NGOI-DAT` |
| Cách nhiệt XPS - 50mm | `07-05-01-20` | `CNCA-CN-XPS-50` | `07-05-01-20.CNCA-CN-XPS-50` |
| Lan can ban công - kính cường lực | `07-07-01-20` | `LC-BC-KINH-1100-CL` | `07-07-01-20.LC-BC-KINH-1100-CL` |

#### D. NHÓM CƠ ĐIỆN (MEP)

| Tên Normalized | SEC Code | Spec Code | Full Code |
|:---|:---|:---|:---|
| Tủ MSB - 800A | `04-01-01-01` | `TBD-MSB-800A-THEP` | `04-01-01-01.TBD-MSB-800A-THEP` |
| Tủ DB - 24 lộ | `04-01-01-02` | `TBD-DB-24LO-THEP` | `04-01-01-02.TBD-DB-24LO-THEP` |
| Cáp Cu/XLPE/PVC - 4x10mm² | `04-01-02-10` | `CAP-CU-4C10-PVC` | `04-01-02-10.CAP-CU-4C10-PVC` |
| Cáp Cu/XLPE/PVC - 4x300mm² | `04-01-02-20` | `CAP-CU-4C300-PVC` | `04-01-02-20.CAP-CU-4C300-PVC` |
| Cáp Cu/XLPE/FR - 4x16mm² | `04-01-02-30` | `CAP-CU-4C16-FR` | `04-01-02-30.CAP-CU-4C16-FR` |
| Cáp Cu/XLPE/LSZH - 3x6mm² | `04-01-02-31` | `CAP-CU-3C6-LSZH` | `04-01-02-31.CAP-CU-3C6-LSZH` |
| Ống luồn PVC - D20 | `04-01-03-10` | `OLD-AM-PVC-D20` | `04-01-03-10.OLD-AM-PVC-D20` |
| Ống luồn thép - D20 | `04-01-03-20` | `OLD-NOI-THEP-D20` | `04-01-03-20.OLD-NOI-THEP-D20` |
| Ổ cắm đôi - Panasonic | `04-01-04-10` | `OCCT-OC-2-PANASONIC-STD` | `04-01-04-10.OCCT-OC-2-PANASONIC-STD` |
| Công tắc cảm ứng | `04-01-04-30` | `OCCT-CT-SENSOR-SCHNEIDER-LUX` | `04-01-04-30.OCCT-CT-SENSOR-SCHNEIDER-LUX` |
| Đèn LED âm trần - 18W | `04-05-03-10` | `DEN-AM-18W-LED` | `04-05-03-10.DEN-AM-18W-LED` |
| Đèn LED panel - 40W | `04-05-03-10` | `DEN-PANEL-40W-LED` | `04-05-03-10.DEN-PANEL-40W-LED` |

#### E. NHÓM PCCC (FIRE PROTECTION)

| Tên Normalized | SEC Code | Spec Code | Full Code |
|:---|:---|:---|:---|
| Tủ trung tâm báo cháy - 4 loop | `04-10-01-01` | `PCCC-TUTT-4LOOP` | `04-10-01-01.PCCC-TUTT-4LOOP` |
| Đầu báo khói quang điện | `04-10-01-03` | `PCCC-DBKHOI-QUANG-TT` | `04-10-01-03.PCCC-DBKHOI-QUANG-TT` |
| Nút nhấn báo cháy | `04-10-01-03` | `PCCC-NUTNHAN-TT` | `04-10-01-03.PCCC-NUTNHAN-TT` |
| Bơm PCCC - 100m³/h - 80m | `04-10-02-01` | `BOM-PCCC-100M3-80M` | `04-10-02-01.BOM-PCCC-100M3-80M` |
| Sprinkler 68°C - treo ngược | `04-10-02-03` | `SPK-TT-68-PEND` | `04-10-02-03.SPK-TT-68-PEND` |
| Hộp chữa cháy - D65 | `04-10-02-03` | `HCC-VT-D65-1VOI` | `04-10-02-03.HCC-VT-D65-1VOI` |
| Quạt hút khói - 15000m³/h | `04-10-04-01` | `QUAT-HK-15000` | `04-10-04-01.QUAT-HK-15000` |
| Quạt tăng áp cầu thang | `04-10-04-01` | `QUAT-TA-10000` | `04-10-04-01.QUAT-TA-10000` |

#### F. NHÓM CẤP THOÁT NƯỚC (PLUMBING)

| Tên Normalized | SEC Code | Spec Code | Full Code |
|:---|:---|:---|:---|
| Ống PPR - PN16 - D25 | `04-21-02-10` | `ONG-PPR-D25-NH-PN16` | `04-21-02-10.ONG-PPR-D25-NH-PN16` |
| Ống thép mạ - ren - D50 | `04-21-02-20` | `ONG-GI-D50-REN` | `04-21-02-20.ONG-GI-D50-REN` |
| Ống inox - bích - D100 | `04-21-02-30` | `ONG-SS-D100-FL` | `04-21-02-30.ONG-SS-D100-FL` |
| Van cổng gang - D50 - PN16 | `04-21-01-10` | `VAN-CONG-GANG-D50-PN16` | `04-21-01-10.VAN-CONG-GANG-D50-PN16` |
| Co 90° PPR - D25 | `04-21-02-91` | `PKO-CO90-PPR-D25` | `04-21-02-91.PKO-CO90-PPR-D25` |
| Ống PVC thoát thải - D110 | `04-22-02-10` | `OT-THAI-PVC-D110` | `04-22-02-10.OT-THAI-PVC-D110` |
| Ống HDPE thoát - D160 | `04-22-02-20` | `OT-THAI-HDPE-D160` | `04-22-02-20.OT-THAI-HDPE-D160` |
| Ống PVC thoát mưa - D200 | `04-23-02-10` | `OT-MUA-PVC-D200` | `04-23-02-10.OT-MUA-PVC-D200` |
| Bơm cấp nước - 20m³/h - 30m | `04-24-01-10` | `BOM-CN-20M3-30M` | `04-24-01-10.BOM-CN-20M3-30M` |

#### G. NHÓM HVAC & THÔNG GIÓ

| Tên Normalized | SEC Code | Spec Code | Full Code |
|:---|:---|:---|:---|
| Chiller - 300RT - giải nhiệt gió | `04-31-01-01` | `DH-CHILLER-300RT-AS` | `04-31-01-01.DH-CHILLER-300RT-AS` |
| VRV/VRF - 10HP | `04-32-01-02` | `DH-VRV-10HP` | `04-32-01-02.DH-VRV-10HP` |
| Điều hòa Split - 24000BTU | `04-33-01-10` | `DH-SPLIT-24K` | `04-33-01-10.DH-SPLIT-24K` |
| Điều hòa Cassette - 36000BTU | `04-33-01-20` | `DH-CASSETTE-36K` | `04-33-01-20.DH-CASSETTE-36K` |
| Quạt thông gió - 2000m³/h | `04-34-01-10` | `QUAT-THOI-2000` | `04-34-01-10.QUAT-THOI-2000` |
| Quạt ly tâm - 5000m³/h - 500Pa | `04-34-01-20` | `QUAT-LT-5000-500PA` | `04-34-01-20.QUAT-LT-5000-500PA` |
| Ống gió tôn - 400x200 | `04-34-02-10` | `GIO-TON-400x200` | `04-34-02-10.GIO-TON-400x200` |
| Miệng gió cấp - 600x600 | `04-34-03-10` | `MG-CAP-600x600-NHOM` | `04-34-03-10.MG-CAP-600x600-NHOM` |
| Miệng gió jet - D250 | `04-34-03-30` | `MG-JET-D250-THEP` | `04-34-03-30.MG-JET-D250-THEP` |

#### H. NHÓM THANG MÁY & HẠ TẦNG

| Tên Normalized | SEC Code | Spec Code | Full Code |
|:---|:---|:---|:---|
| Thang máy khách - 1000kg - 1.75m/s | `04-51-01-01` | `TM-KHACH-1000KG-1.75` | `04-51-01-01.TM-KHACH-1000KG-1.75` |
| Thang hàng - 2000kg - 1.0m/s | `04-52-01-01` | `TM-HANG-2000KG-1.0` | `04-52-01-01.TM-HANG-2000KG-1.0` |
| Thang PCCC - 1000kg | `04-54-01-01` | `TM-PCCC-1000KG-1.0` | `04-54-01-01.TM-PCCC-1000KG-1.0` |
| Đèn đường LED - 100W | `11-06-03-20` | `DEN-DUONG-100W-LED` | `11-06-03-20.DEN-DUONG-100W-LED` |
| Đào đất móng - cấp I - máy | `01-01-01-10` | `DAT-DAO-C1-MAY` | `01-01-01-10.DAT-DAO-C1-MAY` |
| Đắp đất nền - K95 | `10-01-01-20` | `DAT-DAP-K95-MAY` | `10-01-01-20.DAT-DAP-K95-MAY` |

---

**END OF SECTION IX & X**
