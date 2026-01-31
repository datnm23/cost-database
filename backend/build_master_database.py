"""
Script để build Master Database từ uploaded BOQ files
"""
from app.core.database import SessionLocal, engine
from app.models.master_work_item import MasterWorkItem
from app.models.boq_file import BOQFile
from app.services.master_data_service import MasterDataService

# Create master_work_items table
print("Creating master_work_items table...")
MasterWorkItem.__table__.create(engine, checkfirst=True)
print("✓ Table created\n")

def build_master_database():
    """
    Build master database từ tất cả BOQ files đã upload
    """
    db = SessionLocal()
    service = MasterDataService(db)

    try:
        # Get all processed BOQ files
        files = db.query(BOQFile).filter(
            BOQFile.status == 'draft'  # Chỉ lấy files đã process xong
        ).all()

        print(f"=== Building Master Database from {len(files)} BOQ files ===\n")

        total_stats = {
            'files_processed': 0,
            'total_added': 0,
            'total_updated': 0,
            'total_skipped': 0
        }

        for boq_file in files:
            print(f"\nProcessing: {boq_file.file_name} (ID: {boq_file.file_id})")
            print(f"  Total rows: {boq_file.total_rows}")

            stats = service.build_master_from_file(
                file_id=boq_file.file_id,
                min_confidence=60.0,  # Chỉ lấy items có confidence >= 60%
                skip_unclassified=False  # Vẫn lấy cả items chưa phân loại
            )

            print(f"  ✓ Added: {stats['added']}")
            print(f"  ✓ Updated: {stats['updated']}")
            print(f"  ✗ Skipped: {stats['skipped']}")
            print(f"\n  Distribution by SEC Code:")
            for sec_code, count in sorted(stats['by_sec_code'].items()):
                print(f"    {sec_code}: {count} items")

            total_stats['files_processed'] += 1
            total_stats['total_added'] += stats['added']
            total_stats['total_updated'] += stats['updated']
            total_stats['total_skipped'] += stats['skipped']

        # Get final statistics
        print("\n" + "="*60)
        print("=== MASTER DATABASE STATISTICS ===")
        print("="*60)

        db_stats = service.get_statistics()
        print(f"\nTotal Master Items: {db_stats['total_master_items']}")
        print(f"  - Verified: {db_stats['verified_items']}")
        print(f"  - Unverified: {db_stats['unverified_items']}")

        print(f"\nDistribution by SEC Code:")
        for sec_code, count in sorted(db_stats['by_sec_code'].items()):
            print(f"  {sec_code}: {count} items")

        print(f"\nBuild Summary:")
        print(f"  Files processed: {total_stats['files_processed']}")
        print(f"  New items added: {total_stats['total_added']}")
        print(f"  Items updated: {total_stats['total_updated']}")
        print(f"  Items skipped: {total_stats['total_skipped']}")

        # Export to CSV
        output_path = '/app/master_work_items.csv'
        service.export_master_csv(output_path)
        print(f"\n✓ Master data exported to: {output_path}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    build_master_database()
