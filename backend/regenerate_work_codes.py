"""
Script để regenerate tất cả work codes với hệ thống đặt tên mới
"""
from app.core.database import SessionLocal
from app.services.work_code_generator import WorkCodeGenerator
from app.models.master_work_item import MasterWorkItem
import sys


def preview_changes():
    """Preview những thay đổi sẽ xảy ra"""
    db = SessionLocal()
    generator = WorkCodeGenerator(db)

    print("=" * 80)
    print("PREVIEW: Work Code Changes")
    print("=" * 80)
    print()

    stats = generator.regenerate_all_codes(dry_run=True)

    print(f"Total items: {stats['total']}")
    print(f"Will update: {stats['updated']}")
    print(f"Unchanged: {stats['skipped']}")
    print()

    if stats['previews']:
        print("\nChanges Preview (first 20):")
        print("-" * 80)
        print(f"{'Old Code':<25} {'New Code':<25} {'Description':<30}")
        print("-" * 80)

        for preview in stats['previews'][:20]:
            print(f"{preview['old']:<25} {preview['new']:<25} {preview['description']:<30}")

        if len(stats['previews']) > 20:
            print(f"\n... and {len(stats['previews']) - 20} more changes")

    db.close()
    return stats


def apply_changes():
    """Apply changes to database"""
    db = SessionLocal()
    generator = WorkCodeGenerator(db)

    print("\n" + "=" * 80)
    print("APPLYING CHANGES")
    print("=" * 80)
    print()

    stats = generator.regenerate_all_codes(dry_run=False)

    print(f"✓ Updated {stats['updated']} work codes")
    print(f"✓ Skipped {stats['skipped']} unchanged codes")
    print()

    # Show sample of new codes by SEC
    print("\nSample of new codes by SEC:")
    print("-" * 80)

    items = db.query(MasterWorkItem).filter(
        MasterWorkItem.is_active == True
    ).order_by(
        MasterWorkItem.sec_code,
        MasterWorkItem.work_code
    ).limit(30).all()

    current_sec = None
    for item in items:
        if item.sec_code != current_sec:
            current_sec = item.sec_code
            print(f"\n{current_sec}:")

        print(f"  {item.work_code:<25} {item.description[:50]}")

    db.close()


def main():
    """Main function"""
    print("\n" + "=" * 80)
    print("WORK CODE REGENERATION TOOL")
    print("=" * 80)
    print()
    print("This tool will regenerate all work codes using the new naming system.")
    print()

    # Preview changes
    stats = preview_changes()

    if stats['updated'] == 0:
        print("\n✓ All codes are already up to date!")
        return

    # Ask for confirmation
    print("\n" + "=" * 80)
    response = input("\nDo you want to apply these changes? (yes/no): ").strip().lower()

    if response in ['yes', 'y']:
        apply_changes()
        print("\n✓ Work codes regenerated successfully!")
    else:
        print("\n✗ Changes cancelled.")


if __name__ == "__main__":
    main()
