"""
Migration Script: Chuyển đổi hệ thống sang Multi-Code Architecture
Thêm Legal Codes và ISO Codes vào master_work_items
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.master_work_item import MasterWorkItem
from app.services.work_code_generator import WorkCodeGenerator
from app.services.legal_code_service import LegalCodeService
from app.services.iso_classification_service import ISOClassificationService


class MultiCodeMigration:
    """
    Migration để thêm Legal Code và ISO Code vào existing work items
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.work_code_gen = WorkCodeGenerator(db)
        self.legal_service = LegalCodeService(db)
        self.iso_service = ISOClassificationService(db)
    
    def add_columns_to_master_work_items(self):
        """
        Thêm columns: legal_code, iso_code vào master_work_items
        """
        print("Step 1: Adding new columns to master_work_items...")
        
        sql_statements = [
            """
            ALTER TABLE master_work_items 
            ADD COLUMN IF NOT EXISTS legal_code VARCHAR(30) 
            COMMENT 'Mã định mức theo Thông tư 12/2021 (AA.1234a)'
            """,
            """
            ALTER TABLE master_work_items 
            ADD COLUMN IF NOT EXISTS iso_code VARCHAR(50)
            COMMENT 'Mã ISO 12006-2 (Pr_21_31_13)'
            """,
            """
            ALTER TABLE master_work_items 
            ADD COLUMN IF NOT EXISTS name_natural VARCHAR(500)
            COMMENT 'Tên tự nhiên đề xuất theo chuẩn mới'
            """,
            """
            ALTER TABLE master_work_items 
            ADD COLUMN IF NOT EXISTS material_grade VARCHAR(20)
            COMMENT 'Mác vật liệu (M200, CB300, etc.)'
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_legal_code ON master_work_items(legal_code)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_iso_code ON master_work_items(iso_code)
            """,
        ]
        
        try:
            for sql in sql_statements:
                self.db.execute(sql)
            self.db.commit()
            print("✓ Columns added successfully")
        except Exception as e:
            print(f"✗ Error: {e}")
            self.db.rollback()
    
    def generate_missing_codes(self, dry_run: bool = True):
        """
        Tạo Legal Code và ISO Code cho các work items chưa có
        """
        print(f"\nStep 2: Generating missing codes (dry_run={dry_run})...")
        
        items = self.db.query(MasterWorkItem).filter(
            MasterWorkItem.is_active == True
        ).all()
        
        stats = {
            'total': len(items),
            'legal_generated': 0,
            'iso_generated': 0,
            'natural_name_generated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        print(f"Processing {stats['total']} work items...\n")
        
        for idx, item in enumerate(items, 1):
            try:
                updated = False
                
                # Extract material grade if not exist
                if not item.material_grade:
                    grade = self.work_code_gen.extract_material_grade(item.description)
                    if grade:
                        if not dry_run:
                            item.material_grade = grade
                        updated = True
                
                # Generate Legal Code if missing
                if not hasattr(item, 'legal_code') or not item.legal_code:
                    legal_code = self.legal_service.generate_legal_code_from_description(
                        item.description,
                        item.sec_code
                    )
                    if not dry_run:
                        item.legal_code = legal_code
                    stats['legal_generated'] += 1
                    updated = True
                    
                    print(f"[{idx:4d}] Legal: {legal_code:15} ← {item.description[:50]}")
                
                # Generate ISO Code if missing
                if not hasattr(item, 'iso_code') or not item.iso_code:
                    iso_code = self.iso_service.generate_iso_code(
                        item.description,
                        item.sec_code,
                        getattr(item, 'legal_code', None),
                        item.material_grade
                    )
                    if not dry_run:
                        item.iso_code = iso_code
                    stats['iso_generated'] += 1
                    updated = True
                    
                    print(f"[{idx:4d}] ISO:   {iso_code:15} ← {item.description[:50]}")
                
                # Generate natural name if missing
                if not hasattr(item, 'name_natural') or not item.name_natural:
                    # Use description as base, can improve later
                    natural_name = item.description  # Simplified
                    if not dry_run:
                        item.name_natural = natural_name
                    stats['natural_name_generated'] += 1
                    updated = True
                
                if not updated:
                    stats['skipped'] += 1
                
            except Exception as e:
                print(f"✗ Error processing item {item.master_id}: {e}")
                stats['errors'] += 1
        
        if not dry_run:
            self.db.commit()
            print("\n✓ Changes committed to database")
        else:
            print("\n⚠ DRY RUN - No changes made")
        
        print("\n=== MIGRATION STATISTICS ===")
        print(f"Total items:              {stats['total']}")
        print(f"Legal codes generated:    {stats['legal_generated']}")
        print(f"ISO codes generated:      {stats['iso_generated']}")
        print(f"Natural names generated:  {stats['natural_name_generated']}")
        print(f"Skipped (already done):   {stats['skipped']}")
        print(f"Errors:                   {stats['errors']}")
        
        return stats
    
    def create_mapping_table_data(self, dry_run: bool = True):
        """
        Tạo dữ liệu cho work_code_mapping table
        """
        print(f"\nStep 3: Creating mapping table data (dry_run={dry_run})...")
        
        # This would insert into work_code_mapping table
        # Simplified for now
        
        items = self.db.query(MasterWorkItem).filter(
            MasterWorkItem.is_active == True
        ).all()
        
        mappings = []
        
        for item in items:
            if hasattr(item, 'legal_code') and hasattr(item, 'iso_code'):
                mapping = {
                    'work_code': item.work_code,
                    'legal_code': item.legal_code if item.legal_code else None,
                    'iso_code': item.iso_code if item.iso_code else None,
                    'sec_code': item.sec_code,
                    'description': item.description,
                    'unit': item.unit_standard,
                    'material_grade': item.material_grade if hasattr(item, 'material_grade') else None,
                    'mapping_type': 'auto',
                    'confidence_score': 75.0
                }
                mappings.append(mapping)
        
        print(f"✓ Generated {len(mappings)} mapping records")
        
        if not dry_run:
            # Would insert into work_code_mapping
            print("⚠ Mapping table insertion not implemented yet")
        
        return mappings
    
    def run_full_migration(self, dry_run: bool = True):
        """
        Chạy toàn bộ migration
        """
        print("="*60)
        print("MULTI-CODE SYSTEM MIGRATION")
        print("="*60)
        print(f"Mode: {'DRY RUN (Preview only)' if dry_run else 'LIVE (Will modify DB)'}")
        print("="*60 + "\n")
        
        # Step 1: Add columns (only if needed)
        # self.add_columns_to_master_work_items()
        
        # Step 2: Generate codes
        self.generate_missing_codes(dry_run=dry_run)
        
        # Step 3: Create mappings
        # self.create_mapping_table_data(dry_run=dry_run)
        
        print("\n" + "="*60)
        print("MIGRATION COMPLETED")
        print("="*60)


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate to Multi-Code System')
    parser.add_argument(
        '--live',
        action='store_true',
        help='Run in LIVE mode (will modify database)'
    )
    parser.add_argument(
        '--step',
        type=int,
        choices=[1, 2, 3],
        help='Run specific step only (1=add columns, 2=generate codes, 3=create mappings)'
    )
    
    args = parser.parse_args()
    
    dry_run = not args.live
    
    db = SessionLocal()
    migration = MultiCodeMigration(db)
    
    try:
        if args.step:
            if args.step == 1:
                migration.add_columns_to_master_work_items()
            elif args.step == 2:
                migration.generate_missing_codes(dry_run=dry_run)
            elif args.step == 3:
                migration.create_mapping_table_data(dry_run=dry_run)
        else:
            migration.run_full_migration(dry_run=dry_run)
    
    except KeyboardInterrupt:
        print("\n\n⚠ Migration interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
