"""
Batch Update Script: Apply Enhanced Naming to Existing Data
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.master_work_item import MasterWorkItem
from app.services.enhanced_naming_service import EnhancedNamingService
import json


class NamingBatchUpdater:
    """
    Batch update natural names and material specs
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.service = EnhancedNamingService(db)
    
    def update_natural_names(self, dry_run: bool = True):
        """
        Update all natural names using enhanced service
        """
        print("="*60)
        print("BATCH UPDATE: Natural Names")
        print("="*60)
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}\n")
        
        items = self.db.query(MasterWorkItem).filter(
            MasterWorkItem.is_active == True
        ).all()
        
        stats = {
            'total': len(items),
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'improved': 0
        }
        
        for idx, item in enumerate(items, 1):
            try:
                # Generate new natural name
                new_natural = self.service.generate_natural_name(
                    item.description,
                    item.sec_code or 'SEC-99',
                    getattr(item, 'material_grade', None)
                )
                
                # Validate new name
                validation = self.service.validate_natural_name(new_natural)
                
                # Compare with existing
                old_natural = getattr(item, 'name_natural', None)
                
                if old_natural != new_natural:
                    # Check if improved
                    is_improved = validation['is_valid'] or (
                        old_natural and len(new_natural) > len(old_natural)
                    )
                    
                    if is_improved:
                        stats['improved'] += 1
                    
                    print(f"[{idx:4d}] {'✓' if validation['is_valid'] else '⚠'}")
                    print(f"  Old: {old_natural or '(none)')}")
                    print(f"  New: {new_natural}")
                    print(f"  Valid: {validation['is_valid']}, Parts: {validation['parts_count']}")
                    
                    if not dry_run:
                        # Update database
                        if not hasattr(item, 'name_natural'):
                            # Need to add column first
                            print("  ⚠ Column 'name_natural' not exists, skipping update")
                        else:
                            item.name_natural = new_natural
                    
                    stats['updated'] += 1
                else:
                    stats['skipped'] += 1
                
            except Exception as e:
                print(f"✗ Error processing item {item.master_id}: {e}")
                stats['errors'] += 1
        
        if not dry_run:
            self.db.commit()
            print("\n✓ Changes committed to database")
        else:
            print("\n⚠ DRY RUN - No changes made")
        
        print("\n" + "="*60)
        print("STATISTICS")
        print("="*60)
        print(f"Total items:        {stats['total']}")
        print(f"Updated:            {stats['updated']}")
        print(f"  - Improved:       {stats['improved']}")
        print(f"Skipped (same):     {stats['skipped']}")
        print(f"Errors:             {stats['errors']}")
        
        return stats
    
    def update_material_specs(self, dry_run: bool = True):
        """
        Update material_spec JSON for MEP items
        """
        print("\n" + "="*60)
        print("BATCH UPDATE: Material Specs")
        print("="*60)
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}\n")
        
        items = self.db.query(MasterWorkItem).filter(
            MasterWorkItem.is_active == True,
            MasterWorkItem.sec_code.in_(['SEC-04', 'SEC-08'])
        ).all()
        
        stats = {
            'total': len(items),
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        for idx, item in enumerate(items, 1):
            try:
                # Extract MEP specs
                mep_specs = self.service.extract_mep_specs(item.description)
                
                if mep_specs:
                    # Build JSON
                    spec_json = self.service.build_material_spec_json(**mep_specs)
                    
                    print(f"[{idx:4d}] {item.description[:60]}")
                    print(f"  Specs: {json.dumps(spec_json, ensure_ascii=False)}")
                    
                    if not dry_run:
                        # Update database
                        if not hasattr(item, 'material_spec'):
                            print("  ⚠ Column 'material_spec' not exists, skipping update")
                        else:
                            # Convert to JSON string for MySQL
                            item.material_spec = json.dumps(spec_json)
                    
                    stats['updated'] += 1
                else:
                    stats['skipped'] += 1
                
            except Exception as e:
                print(f"✗ Error processing item {item.master_id}: {e}")
                stats['errors'] += 1
        
        if not dry_run:
            self.db.commit()
            print("\n✓ Changes committed to database")
        else:
            print("\n⚠ DRY RUN - No changes made")
        
        print("\n" + "="*60)
        print("STATISTICS")
        print("="*60)
        print(f"Total MEP items:    {stats['total']}")
        print(f"Updated:            {stats['updated']}")
        print(f"Skipped (no specs): {stats['skipped']}")
        print(f"Errors:             {stats['errors']}")
        
        return stats
    
    def validate_all(self):
        """
        Validate all natural names
        """
        print("\n" + "="*60)
        print("VALIDATION REPORT")
        print("="*60 + "\n")
        
        items = self.db.query(MasterWorkItem).filter(
            MasterWorkItem.is_active == True
        ).all()
        
        stats = {
            'total': len(items),
            'valid': 0,
            'invalid': 0,
            'missing_verb': 0,
            'missing_specs': 0,
            'too_short': 0,
            'too_long': 0
        }
        
        for item in items:
            name = getattr(item, 'name_natural', item.description)
            
            if not name:
                continue
            
            validation = self.service.validate_natural_name(name)
            
            if validation['is_valid']:
                stats['valid'] += 1
            else:
                stats['invalid'] += 1
            
            if not validation['has_verb']:
                stats['missing_verb'] += 1
            
            if not validation['has_specs']:
                stats['missing_specs'] += 1
            
            if validation['length'] < 20:
                stats['too_short'] += 1
            elif validation['length'] > 100:
                stats['too_long'] += 1
        
        print(f"Total items:            {stats['total']}")
        print(f"Valid:                  {stats['valid']} ({stats['valid']/stats['total']*100:.1f}%)")
        print(f"Invalid:                {stats['invalid']} ({stats['invalid']/stats['total']*100:.1f}%)")
        print(f"\nIssue breakdown:")
        print(f"  Missing verb:         {stats['missing_verb']}")
        print(f"  Missing specs:        {stats['missing_specs']}")
        print(f"  Too short (<20):      {stats['too_short']}")
        print(f"  Too long (>100):      {stats['too_long']}")
        
        return stats


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch update natural names and material specs')
    parser.add_argument(
        '--action',
        choices=['natural-names', 'material-specs', 'validate', 'all'],
        default='all',
        help='Action to perform'
    )
    parser.add_argument(
        '--live',
        action='store_true',
        help='Run in LIVE mode (will modify database)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of items to process'
    )
    
    args = parser.parse_args()
    
    dry_run = not args.live
    
    db = SessionLocal()
    updater = NamingBatchUpdater(db)
    
    try:
        if args.action in ['natural-names', 'all']:
            updater.update_natural_names(dry_run=dry_run)
        
        if args.action in ['material-specs', 'all']:
            updater.update_material_specs(dry_run=dry_run)
        
        if args.action in ['validate', 'all']:
            updater.validate_all()
    
    except KeyboardInterrupt:
        print("\n\n⚠ Update interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Update failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
