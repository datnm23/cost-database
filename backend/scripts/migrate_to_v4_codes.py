"""
Migrate existing MasterWorkItems to v4.0 code format.

Usage:
    cd backend
    python scripts/migrate_to_v4_codes.py --dry-run    # Preview only
    python scripts/migrate_to_v4_codes.py               # Apply changes
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse

from app.core.database import SessionLocal
from app.models.master_work_item import MasterWorkItem
from app.services.v4_code_generator import V4CodeGenerator


def migrate_to_v4(dry_run: bool = True) -> dict:
    """
    Migrate all active MasterWorkItems to v4.0 codes.

    1. Load all items
    2. For each: generate v4.0 reference code
    3. Save old work_code to work_code_legacy
    4. Set sec_code_v4 = reference code (non-unique, 1:N)
    5. Generate unique instance_code = ref_code + '-NNN'
    6. Detect item_table_type from description
    """
    db = SessionLocal()
    generator = V4CodeGenerator()

    items = db.query(MasterWorkItem).filter(
        MasterWorkItem.is_active == True
    ).order_by(
        MasterWorkItem.sec_code,
        MasterWorkItem.description,
    ).all()

    stats = {
        'total': len(items),
        'migrated': 0,
        'already_migrated': 0,
        'errors': 0,
        'previews': [],
    }

    for item in items:
        try:
            # Skip if already has instance code
            if item.instance_code:
                stats['already_migrated'] += 1
                continue

            # Build specs dict from existing fields
            specs = {
                'category': item.spec_category,
                'material': item.spec_material,
                'grade': item.spec_grade,
                'dimension': item.spec_dimension,
            }

            # Detect item type from description
            from app.services.master_database_builder import MasterDatabaseBuilder
            builder = MasterDatabaseBuilder.__new__(MasterDatabaseBuilder)
            detected_type = builder._detect_item_type(item.description)

            # Generate v4 reference code
            v4_code, v4_discipline, v4_location = generator.generate(
                description=item.description,
                sec_code=item.sec_code,
                specs=specs,
                table_type=detected_type,
            )

            # Generate unique instance code
            instance_code = generator.generate_instance_code(
                ref_code=v4_code,
                db=db,
            )

            preview = {
                'master_id': item.master_id,
                'old_work_code': item.work_code,
                'new_v4_code': v4_code,
                'discipline': v4_discipline,
                'location': v4_location,
                'instance_code': instance_code,
                'item_type': detected_type,
                'description': item.description[:60],
            }
            stats['previews'].append(preview)

            if not dry_run:
                # Save legacy code
                if not item.work_code_legacy:
                    item.work_code_legacy = item.work_code

                # Set v4 reference code and instance code
                item.sec_code_v4 = v4_code
                item.instance_code = instance_code
                item.item_table_type = detected_type
                item.discipline = v4_discipline
                item.location = v4_location

                # Compute completeness
                item.spec_completeness = item.compute_spec_completeness()

                stats['migrated'] += 1

        except Exception as e:
            stats['errors'] += 1
            print(f"  ERROR item {item.master_id}: {e}")

    if not dry_run:
        db.commit()

    db.close()
    return stats


def main():
    parser = argparse.ArgumentParser(description='Migrate work codes to v4.0 format')
    parser.add_argument('--dry-run', action='store_true', default=False,
                        help='Preview changes without applying')
    args = parser.parse_args()

    print(f"\n{'=' * 60}")
    print(f"  MIGRATE TO v4.0 CODES {'(DRY RUN)' if args.dry_run else '(LIVE)'}")
    print(f"{'=' * 60}\n")

    stats = migrate_to_v4(dry_run=args.dry_run)

    print(f"Total items:        {stats['total']}")
    print(f"Migrated:           {stats['migrated']}")
    print(f"Already migrated:   {stats['already_migrated']}")
    print(f"Errors:             {stats['errors']}")

    # Show first 20 previews
    print(f"\nPreview (first 20):")
    print(f"{'ID':>6} | {'Old Code':<25} | {'V4 Ref':<20} | {'Disc':<4} | {'Loc':<5} | {'Instance':<30} | {'T':1} | Description")
    print(f"{'-' * 130}")
    for p in stats['previews'][:20]:
        v4 = p['new_v4_code'] or '(none)'
        disc = p.get('discipline', '') or ''
        loc = p.get('location', '') or ''
        inst = p.get('instance_code', '(none)') or '(none)'
        itype = p.get('item_type', '?')
        print(f"{p['master_id']:>6} | {p['old_work_code']:<25} | {v4:<20} | {disc:<4} | {loc:<5} | {inst:<30} | {itype:1} | {p['description']}")

    if args.dry_run:
        print(f"\n  DRY RUN — no changes applied. Run without --dry-run to apply.\n")


if __name__ == '__main__':
    main()
