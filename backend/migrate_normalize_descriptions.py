"""
Migration script: Làm sạch và chuẩn hóa tất cả descriptions trong database
Áp dụng Phương án 5 - Natural Syntax

Usage:
    python -m backend.migrate_normalize_descriptions --dry-run    # Preview only
    python -m backend.migrate_normalize_descriptions --execute    # Apply changes
"""
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.master_work_item import MasterWorkItem
from app.models.line_item import LineItem
from app.services.description_normalizer import DescriptionNormalizer


def print_header(title: str):
    """Print section header"""
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)


def migrate_master_work_items(dry_run: bool = True):
    """
    Chuẩn hóa descriptions trong master_work_items table
    """
    print_header(f"MIGRATE MASTER WORK ITEMS {'(DRY RUN)' if dry_run else '(EXECUTING)'}")

    db = SessionLocal()
    normalizer = DescriptionNormalizer()

    try:
        # Get all active master work items
        items = db.query(MasterWorkItem).filter(
            MasterWorkItem.is_active == True
        ).order_by(MasterWorkItem.master_id).all()

        print(f"\nTotal master items to process: {len(items)}")

        stats = {
            'total': len(items),
            'changed': 0,
            'unchanged': 0,
            'errors': 0,
            'changes': []
        }

        for idx, item in enumerate(items, 1):
            try:
                original = item.description
                normalized = normalizer.normalize(original)

                if original != normalized:
                    stats['changed'] += 1

                    # Store change for preview
                    if len(stats['changes']) < 20:  # Limit preview to 20 items
                        stats['changes'].append({
                            'id': item.master_id,
                            'work_code': item.work_code,
                            'sec_code': item.sec_code,
                            'original': original,
                            'normalized': normalized,
                            'reduction': len(original) - len(normalized)
                        })

                    # Apply change if not dry run
                    if not dry_run:
                        item.description = normalized
                        # Also update normalized version for search
                        item.description_normalized = normalized.lower()

                else:
                    stats['unchanged'] += 1

                # Progress indicator
                if idx % 100 == 0:
                    print(f"  Processed {idx}/{len(items)} items...")

            except Exception as e:
                print(f"  ❌ Error processing item {item.master_id}: {e}")
                stats['errors'] += 1
                continue

        # Commit changes if not dry run
        if not dry_run:
            db.commit()
            print(f"\n✅ Changes committed to database")
        else:
            print(f"\n🔍 Preview mode - no changes committed")

        # Print statistics
        print(f"\nStatistics:")
        print(f"  Total items:      {stats['total']}")
        print(f"  Changed:          {stats['changed']} ({stats['changed']/stats['total']*100:.1f}%)")
        print(f"  Unchanged:        {stats['unchanged']} ({stats['unchanged']/stats['total']*100:.1f}%)")
        print(f"  Errors:           {stats['errors']}")

        # Print sample changes
        if stats['changes']:
            print(f"\n📋 Sample Changes (showing first {len(stats['changes'])}):")
            print(f"\n{'ID':<6} | {'Code':<20} | {'SEC':<10} | {'Original':<40} | {'Normalized':<40} | {'Δ':<5}")
            print("-" * 130)

            for change in stats['changes']:
                print(f"{change['id']:<6} | "
                      f"{change['work_code']:<20} | "
                      f"{change['sec_code']:<10} | "
                      f"{change['original'][:40]:<40} | "
                      f"{change['normalized'][:40]:<40} | "
                      f"{change['reduction']:>4}")

        return stats

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def migrate_line_items(dry_run: bool = True, limit: int = None):
    """
    Chuẩn hóa descriptions trong line_items table
    Populates normalized_description field (không overwrite description)

    Args:
        dry_run: Preview mode
        limit: Giới hạn số items (để test)
    """
    print_header(f"MIGRATE LINE ITEMS {'(DRY RUN)' if dry_run else '(EXECUTING)'}")

    db = SessionLocal()
    normalizer = DescriptionNormalizer()

    try:
        # Get line items that have not been normalized yet
        query = db.query(LineItem).filter(
            LineItem.description.isnot(None),
            LineItem.description != '',
            LineItem.normalized_description.is_(None)  # Only process items without normalized_description
        ).order_by(LineItem.line_item_id)

        if limit:
            query = query.limit(limit)
            print(f"\n⚠️ LIMIT MODE: Processing only {limit} items")

        items = query.all()

        print(f"\nTotal line items to process: {len(items)}")

        stats = {
            'total': len(items),
            'changed': 0,
            'unchanged': 0,
            'errors': 0,
            'changes': []
        }

        batch_size = 500
        for idx, item in enumerate(items, 1):
            try:
                original = item.description
                normalized = normalizer.normalize(original)
                work_category = normalizer.identify_work_category(original)

                # Calculate confidence
                components = normalizer.parse_description(original)
                confidence = 100.0
                if not components.get('verb'):
                    confidence -= 30
                if not components.get('material'):
                    confidence -= 20
                if not components.get('position'):
                    confidence -= 15
                if not components.get('grade') and not components.get('specs'):
                    confidence -= 15
                confidence = max(0, confidence)

                if original != normalized:
                    stats['changed'] += 1

                    # Store change for preview
                    if len(stats['changes']) < 20:  # Limit preview to 20 items
                        stats['changes'].append({
                            'id': item.line_item_id,
                            'original': original,
                            'normalized': normalized,
                            'work_category': work_category,
                            'confidence': confidence,
                            'reduction': len(original) - len(normalized)
                        })

                    # Apply change if not dry run
                    if not dry_run:
                        item.normalized_description = normalized
                        item.work_category = work_category
                        item.normalization_confidence = confidence

                else:
                    stats['unchanged'] += 1
                    # Even if unchanged, populate the normalized fields
                    if not dry_run:
                        item.normalized_description = normalized
                        item.work_category = work_category
                        item.normalization_confidence = confidence

                # Progress indicator and batch commit
                if idx % batch_size == 0:
                    print(f"  Processed {idx}/{len(items)} items...")
                    if not dry_run:
                        db.commit()

            except Exception as e:
                print(f"  ❌ Error processing item {item.line_item_id}: {e}")
                stats['errors'] += 1
                continue

        # Commit remaining changes if not dry run
        if not dry_run:
            db.commit()
            print(f"\n✅ Changes committed to database")
        else:
            print(f"\n🔍 Preview mode - no changes committed")

        # Print statistics
        print(f"\nStatistics:")
        print(f"  Total items:      {stats['total']}")
        if stats['total'] > 0:
            print(f"  Changed:          {stats['changed']} ({stats['changed']/stats['total']*100:.1f}%)")
            print(f"  Unchanged:        {stats['unchanged']} ({stats['unchanged']/stats['total']*100:.1f}%)")
        print(f"  Errors:           {stats['errors']}")

        # Print sample changes
        if stats['changes']:
            print(f"\n📋 Sample Changes (showing first {len(stats['changes'])}):")
            print(f"\n{'ID':<8} | {'Work Category':<20} | {'Conf':<5} | {'Original':<35} | {'Normalized':<35}")
            print("-" * 120)

            for change in stats['changes']:
                print(f"{change['id']:<8} | "
                      f"{(change['work_category'] or 'N/A'):<20} | "
                      f"{change['confidence']:<5.0f} | "
                      f"{change['original'][:35]:<35} | "
                      f"{change['normalized'][:35]:<35}")

        return stats

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def export_migration_report(master_stats: dict, line_stats: dict, filename: str = None):
    """
    Export migration report to file
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"migration_report_{timestamp}.txt"

    print(f"\n📄 Exporting report to: {filename}")

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write("  DESCRIPTION NORMALIZATION MIGRATION REPORT\n")
        f.write("  Phương án 5 - Natural Syntax\n")
        f.write("=" * 100 + "\n\n")

        f.write(f"Migration Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Master Work Items
        f.write("MASTER WORK ITEMS\n")
        f.write("-" * 100 + "\n")
        f.write(f"Total items:      {master_stats['total']}\n")
        f.write(f"Changed:          {master_stats['changed']} ({master_stats['changed']/master_stats['total']*100:.1f}%)\n")
        f.write(f"Unchanged:        {master_stats['unchanged']} ({master_stats['unchanged']/master_stats['total']*100:.1f}%)\n")
        f.write(f"Errors:           {master_stats['errors']}\n\n")

        if master_stats.get('changes'):
            f.write("Sample Changes:\n")
            for change in master_stats['changes']:
                f.write(f"\nID: {change['id']} | Code: {change['work_code']}\n")
                f.write(f"  Before: {change['original']}\n")
                f.write(f"  After:  {change['normalized']}\n")
                f.write(f"  Reduction: {change['reduction']} chars\n")

        # Line Items
        f.write("\n\nLINE ITEMS\n")
        f.write("-" * 100 + "\n")
        f.write(f"Total items:      {line_stats['total']}\n")
        f.write(f"Changed:          {line_stats['changed']} ({line_stats['changed']/line_stats['total']*100:.1f}%)\n")
        f.write(f"Unchanged:        {line_stats['unchanged']} ({line_stats['unchanged']/line_stats['total']*100:.1f}%)\n")
        f.write(f"Errors:           {line_stats['errors']}\n")

    print(f"✅ Report exported successfully")


def main():
    """Main migration function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate descriptions to Natural Syntax (Phương án 5)"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying them'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute migration and apply changes to database'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of line items (for testing)'
    )
    parser.add_argument(
        '--skip-master',
        action='store_true',
        help='Skip master_work_items migration'
    )
    parser.add_argument(
        '--skip-line-items',
        action='store_true',
        help='Skip line_items migration'
    )
    parser.add_argument(
        '--export-report',
        action='store_true',
        help='Export migration report to file'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.dry_run and not args.execute:
        print("❌ Error: Must specify either --dry-run or --execute")
        parser.print_help()
        sys.exit(1)

    if args.dry_run and args.execute:
        print("❌ Error: Cannot specify both --dry-run and --execute")
        sys.exit(1)

    # Print banner
    print("\n")
    print("╔" + "═" * 98 + "╗")
    print("║" + " " * 98 + "║")
    print("║" + "  DESCRIPTION NORMALIZATION MIGRATION".center(98) + "║")
    print("║" + "  Phương án 5 - Natural Syntax".center(98) + "║")
    print("║" + " " * 98 + "║")
    print("╚" + "═" * 98 + "╝")

    is_dry_run = args.dry_run

    if is_dry_run:
        print("\n🔍 PREVIEW MODE - No changes will be saved")
    else:
        print("\n⚠️  EXECUTION MODE - Changes will be saved to database")
        confirm = input("\nAre you sure you want to continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Migration cancelled")
            sys.exit(0)

    try:
        master_stats = None
        line_stats = None

        # Migrate master work items
        if not args.skip_master:
            master_stats = migrate_master_work_items(dry_run=is_dry_run)

        # Migrate line items
        if not args.skip_line_items:
            line_stats = migrate_line_items(dry_run=is_dry_run, limit=args.limit)

        # Export report
        if args.export_report and master_stats and line_stats:
            export_migration_report(master_stats, line_stats)

        print_header("✓ MIGRATION COMPLETED SUCCESSFULLY")

        if is_dry_run:
            print("\n💡 To apply changes, run with --execute flag")

    except Exception as e:
        print_header("❌ MIGRATION FAILED")
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
