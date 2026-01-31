"""
Update SEC codes with proper keywords for classification
"""
import json
from app.core.database import SessionLocal
from app.models.sec_code import SECCode

# Keywords for each SEC code (Vietnamese and English)
SEC_KEYWORDS = {
    "SEC-00": [
        "chuẩn bị", "chi phí chung", "preliminaries", "general",
        "quản lý", "bảo hiểm", "an toàn", "tạm", "văn phòng"
    ],
    "SEC-01": [
        "ngầm", "substructure", "foundation", "phần ngầm"
    ],
    "SEC-01-01": [
        "đào đất", "đắp đất", "earthwork", "excavation",
        "san lấp", "đào móng", "đất", "nền đất"
    ],
    "SEC-01-02": [
        "cọc", "pile", "piling", "đóng cọc",
        "khoan cọc", "ép cọc", "cọc khoan", "cọc nhồi"
    ],
    "SEC-01-03": [
        "móng", "foundation", "bệ móng", "đài móng",
        "móng băng", "móng đơn", "cột móng"
    ],
    "SEC-02": [
        "thân", "superstructure", "structure", "phần thân",
        "kết cấu", "cột", "dầm", "sàn", "bê tông", "thép",
        "khung", "tường chịu lực"
    ],
    "SEC-03": [
        "kiến trúc", "hoàn thiện", "architecture", "finishes",
        "tường xây", "vách", "trần", "sơn", "gạch lát",
        "cửa", "cửa sổ", "lan can", "ốp lát", "trang trí"
    ],
    "SEC-04": [
        "MEP", "cơ điện", "mechanical", "electrical", "plumbing",
        "điện", "nước", "điều hòa", "thông gió", "PCCC",
        "cấp thoát nước", "chiếu sáng", "điện lạnh", "thang máy",
        "hệ thống điện", "hệ thống nước", "HVAC"
    ],
    "SEC-05": [
        "cảnh quan", "landscape", "external", "ngoại thất",
        "sân vườn", "cây xanh", "vỉa hè", "đường nội bộ",
        "hàng rào", "cổng", "bãi đỗ xe", "thoát nước mưa"
    ]
}

def update_keywords():
    db = SessionLocal()

    try:
        print("Updating SEC codes keywords...\n")

        for sec_code, keywords in SEC_KEYWORDS.items():
            sec = db.query(SECCode).filter(SECCode.sec_code == sec_code).first()

            if sec:
                # Convert keywords list to JSON string
                keywords_json = json.dumps(keywords, ensure_ascii=False)
                sec.keywords = keywords_json

                print(f"✓ Updated {sec_code}: {sec.sec_name_vi}")
                print(f"  Keywords: {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}")
                print()
            else:
                print(f"✗ SEC code not found: {sec_code}")

        db.commit()
        print("\n✓ All keywords updated successfully!")

    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_keywords()
