"""
Test automatic classification feature
Creates sample line items and classifies them
"""
from app.core.database import SessionLocal
from app.models.line_item import LineItem, ClassificationMethod
from app.models.boq_file import BOQFile, FileStatus
from app.services.rule_based_classifier import get_rule_based_classifier
from app.core.config import settings

# Sample BOQ items from different categories
SAMPLE_ITEMS = [
    # SEC-00: Preliminaries
    "Chi phí quản lý dự án",
    "Bảo hiểm công trình",
    "An toàn lao động",
    "Văn phòng công trường",

    # SEC-01-01: Earthworks
    "Đào đất móng sâu 2.5m",
    "San lấp mặt bằng",
    "Đắp đất nền móng",
    "Đào hố móng M1",

    # SEC-01-02: Piling
    "Đóng cọc BTCT D400 L=18m",
    "Khoan cọc nhồi D600",
    "Ép cọc vuông 250x250",
    "Cắt ngắn đầu cọc",

    # SEC-01-03: Foundation
    "Móng băng MBG1 bê tông B25",
    "Đài móng cọc MĐ1",
    "Bệ móng máy",
    "Dầm móng liên kết",

    # SEC-02: Superstructure
    "Cột bê tông cốt thép C1 400x400",
    "Dầm chính BTCT D1 300x600",
    "Sàn BTCT dày 120mm",
    "Tường chịu lực bê tông 200mm",
    "Khung thép kết cấu",

    # SEC-03: Architecture & Finishes
    "Tường gạch xây 200mm",
    "Trần thạch cao chống ẩm",
    "Sơn nước nội thất",
    "Lát gạch granite 60x60",
    "Cửa gỗ công nghiệp",
    "Cửa sổ nhôm kính",
    "Lan can inox 304",
    "Ốp tường gạch ceramic",

    # SEC-04: MEP
    "Hệ thống điện chiếu sáng",
    "Điều hòa trung tâm VRV",
    "Hệ thống cấp nước sinh hoạt",
    "Thoát nước thải",
    "PCCC sprinkler",
    "Thang máy 8 người",
    "Hệ thống báo cháy",

    # SEC-05: Landscape
    "Cây xanh công viên",
    "Vỉa hè lát gạch",
    "Đường nội bộ bê tông",
    "Hàng rào bảo vệ",
    "Cổng chính",
    "Bãi đỗ xe ô tô",
]

def create_test_data():
    """Create test BOQ file and line items"""
    db = SessionLocal()

    try:
        print("Creating test BOQ file...")

        # Create BOQ file
        boq_file = BOQFile(
            project_id=1,
            file_name="test_classification.xlsx",
            file_path="/tmp/test_classification.xlsx",
            file_hash="test123",
            total_rows=len(SAMPLE_ITEMS),
            status=FileStatus.draft,
            uploaded_by=1
        )
        db.add(boq_file)
        db.flush()

        print(f"✓ Created BOQ file with ID: {boq_file.file_id}\n")

        # Initialize classifier
        print("Initializing classifier...")
        classifier = get_rule_based_classifier(db)
        print("✓ Classifier ready\n")

        # Confidence threshold
        confidence_threshold = settings.CLASSIFICATION_THRESHOLD * 100

        # Process each item
        print(f"{'Item Description':<50} {'SEC Code':<12} {'Confidence':<12} {'Review?'}")
        print("=" * 90)

        classified_count = 0
        needs_review_count = 0

        for idx, description in enumerate(SAMPLE_ITEMS, 1):
            # Classify
            results = classifier.classify(description, top_k=3)

            # Create line item
            item_data = {
                'file_id': boq_file.file_id,
                'project_id': 1,
                'row_number': idx,
                'description': description,
                'unit': 'pcs',
                'quantity': 10.0,
                'unit_price': 1000000.0,
                'amount': 10000000.0,
                'classification_method': ClassificationMethod.auto,
            }

            if results:
                sec_code, confidence = results[0]
                item_data['sec_code'] = sec_code
                item_data['confidence_score'] = confidence

                # Flag for review if low confidence
                if confidence < confidence_threshold:
                    item_data['needs_review'] = True
                    item_data['validation_issues'] = f'Low confidence ({confidence:.1f}%)'
                    needs_review_count += 1
                else:
                    item_data['needs_review'] = False

                classified_count += 1

                # Print result
                review_flag = '⚠️ YES' if item_data.get('needs_review') else '✓ NO'
                print(f"{description:<50} {sec_code:<12} {confidence:>6.1f}%      {review_flag}")

            else:
                # No classification found
                item_data['sec_code'] = None
                item_data['confidence_score'] = 0
                item_data['needs_review'] = True
                item_data['validation_issues'] = 'No classification match'
                needs_review_count += 1

                print(f"{description:<50} {'N/A':<12} {'0.0':>6}%      ⚠️ YES")

            # Save to database
            line_item = LineItem(**item_data)
            db.add(line_item)

        # Commit all
        db.commit()

        # Print summary
        print("=" * 90)
        print(f"\n📊 Classification Summary:")
        print(f"  Total items:          {len(SAMPLE_ITEMS)}")
        print(f"  Successfully classified: {classified_count} ({classified_count/len(SAMPLE_ITEMS)*100:.1f}%)")
        print(f"  Needs review:         {needs_review_count} ({needs_review_count/len(SAMPLE_ITEMS)*100:.1f}%)")
        print(f"  Confidence threshold: {confidence_threshold}%")

        # Show distribution by SEC code
        print(f"\n📈 Distribution by SEC Code:")
        from collections import Counter
        items = db.query(LineItem).filter(LineItem.file_id == boq_file.file_id).all()
        sec_counts = Counter(item.sec_code for item in items if item.sec_code)

        for sec_code, count in sorted(sec_counts.items()):
            sec = db.execute(
                "SELECT sec_name_vi FROM sec_codes WHERE sec_code = :code",
                {"code": sec_code}
            ).fetchone()
            sec_name = sec[0] if sec else "Unknown"
            print(f"  {sec_code}: {count:2d} items - {sec_name}")

        print(f"\n✅ Test completed! File ID: {boq_file.file_id}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()
