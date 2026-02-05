#!/usr/bin/env python3
"""
Backfill separated specs for existing master items.

Usage:
    python scripts/backfill_specs.py
    python scripts/backfill_specs.py --with-embeddings  # Also generate embeddings
    python scripts/backfill_specs.py --limit 100        # Process only 100 items
    python scripts/backfill_specs.py --dry-run          # Preview without saving

Requirements:
    Run from backend directory:
    cd backend && python scripts/backfill_specs.py
"""
import argparse
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.master_work_item import MasterWorkItem
from app.services.spec_extractor import SpecExtractor


def backfill_specs(
    db: Session,
    with_embeddings: bool = False,
    limit: int = 0,
    dry_run: bool = False,
    verbose: bool = False
) -> dict:
    """
    Backfill specs for all master items.

    Args:
        db: Database session
        with_embeddings: Also generate and store embeddings
        limit: Limit number of items to process (0 = all)
        dry_run: Preview changes without saving
        verbose: Print detailed progress

    Returns:
        Dict with statistics
    """
    extractor = SpecExtractor()
    embedding_service = None

    if with_embeddings:
        try:
            from app.services.hybrid_matcher.embedding_service import EmbeddingService
            embedding_service = EmbeddingService()
            print("Embedding service loaded successfully")
        except Exception as e:
            print(f"Warning: Could not load embedding service: {e}")
            print("Proceeding without embeddings...")

    # Query items that need backfill
    query = db.query(MasterWorkItem).filter(
        MasterWorkItem.is_active == True,
        MasterWorkItem.matching_key == None  # Only unfilled
    )

    if limit > 0:
        query = query.limit(limit)

    items = query.all()

    print(f"Found {len(items)} items to backfill")

    if dry_run:
        print("\n=== DRY RUN MODE - No changes will be saved ===\n")

    stats = {
        'total': len(items),
        'with_category': 0,
        'with_material': 0,
        'with_grade': 0,
        'with_dimension': 0,
        'with_matching_key': 0,
        'with_embedding': 0,
        'errors': 0
    }

    for i, item in enumerate(items):
        try:
            # Get description to extract from
            desc = item.description_normalized or item.description or ''

            # Extract specs
            specs = extractor.extract(desc)

            item.spec_category = specs.category
            item.spec_material = specs.material
            item.spec_grade = specs.grade
            item.spec_dimension = specs.dimension
            item.matching_key = specs.to_matching_key()

            # Update stats
            if specs.category:
                stats['with_category'] += 1
            if specs.material:
                stats['with_material'] += 1
            if specs.grade:
                stats['with_grade'] += 1
            if specs.dimension:
                stats['with_dimension'] += 1
            if item.matching_key and item.matching_key != 'x|x|x|x':
                stats['with_matching_key'] += 1

            # Optional: Generate embedding
            if embedding_service and not item.embedding_vector:
                try:
                    embedding = embedding_service.encode_single(desc)
                    item.embedding_vector = embedding.tobytes()
                    item.embedding_version = "vietnamese-sbert-v1"
                    stats['with_embedding'] += 1
                except Exception as e:
                    if verbose:
                        print(f"  Warning: Failed to generate embedding: {e}")

            if verbose:
                print(f"  [{i+1}/{len(items)}] {item.work_code}: "
                      f"cat={specs.category}, mat={specs.material}, "
                      f"grade={specs.grade}, dim={specs.dimension}")

            # Commit periodically
            if not dry_run and (i + 1) % 100 == 0:
                db.commit()
                print(f"  Committed batch at {i + 1}/{len(items)}")

        except Exception as e:
            stats['errors'] += 1
            print(f"  Error processing item {item.master_id}: {e}")
            continue

    # Final commit
    if not dry_run:
        db.commit()
        print(f"\nCommitted all changes")

    return stats


def print_stats(stats: dict):
    """Print formatted statistics."""
    print("\n" + "=" * 50)
    print("BACKFILL STATISTICS")
    print("=" * 50)
    print(f"Total items processed: {stats['total']}")
    print(f"  With category:       {stats['with_category']} ({100*stats['with_category']/max(stats['total'],1):.1f}%)")
    print(f"  With material:       {stats['with_material']} ({100*stats['with_material']/max(stats['total'],1):.1f}%)")
    print(f"  With grade:          {stats['with_grade']} ({100*stats['with_grade']/max(stats['total'],1):.1f}%)")
    print(f"  With dimension:      {stats['with_dimension']} ({100*stats['with_dimension']/max(stats['total'],1):.1f}%)")
    print(f"  With matching key:   {stats['with_matching_key']} ({100*stats['with_matching_key']/max(stats['total'],1):.1f}%)")
    print(f"  With embedding:      {stats['with_embedding']} ({100*stats['with_embedding']/max(stats['total'],1):.1f}%)")
    print(f"  Errors:              {stats['errors']}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Backfill separated specs for existing master items"
    )
    parser.add_argument(
        "--with-embeddings",
        action="store_true",
        help="Also generate and store SBERT embeddings"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of items to process (0 = all)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without saving to database"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed progress"
    )

    args = parser.parse_args()

    print("=" * 50)
    print("SPEC BACKFILL SCRIPT")
    print("=" * 50)
    print(f"Options:")
    print(f"  With embeddings: {args.with_embeddings}")
    print(f"  Limit: {args.limit if args.limit > 0 else 'None'}")
    print(f"  Dry run: {args.dry_run}")
    print(f"  Verbose: {args.verbose}")
    print()

    db = SessionLocal()
    try:
        stats = backfill_specs(
            db,
            with_embeddings=args.with_embeddings,
            limit=args.limit,
            dry_run=args.dry_run,
            verbose=args.verbose
        )
        print_stats(stats)
    finally:
        db.close()


if __name__ == "__main__":
    main()
