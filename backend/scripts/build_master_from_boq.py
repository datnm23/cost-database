#!/usr/bin/env python3
"""
Build Master Database from BOQ files in ~/Downloads/boq-2026/boq/

Pipeline:
1. Create project "BOQ-2026-MASTER"
2. Upload and parse all Excel files -> line_items
3. Run MasterDatabaseBuilder (3-step pipeline) with clear_existing=True
4. Report statistics

Usage:
    cd backend && python3 scripts/build_master_from_boq.py
"""
import hashlib
import logging
import os
import sys
import time
from pathlib import Path

# Disable AI normalizer during batch build (rule-based is sufficient and much faster)
os.environ["AI_NORMALIZATION_ENABLED"] = "false"
os.environ["AI_CONTEXT_ANALYSIS_ENABLED"] = "false"
os.environ["AI_DOMAIN_VALIDATION_ENABLED"] = "false"

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.core.database import SessionLocal, engine
from app.models.project import Project, ProjectType, ProjectStatus
from app.models.boq_file import BOQFile, FileStatus
from app.models.line_item import LineItem
from app.utils.excel_processor import ExcelProcessor
from app.services.file_service import FileService
from app.services.master_database_builder import (
    get_master_database_builder,
    BuildConfig,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("build_master")

# Suppress noisy loggers
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("app.services.normalization_orchestrator").setLevel(logging.WARNING)
logging.getLogger("app.services.description_normalizer").setLevel(logging.WARNING)
logging.getLogger("app.services.mep_equipment_normalizer").setLevel(logging.WARNING)
logging.getLogger("app.utils.excel_processor").setLevel(logging.WARNING)
logging.getLogger("app.services.ai_normalizer").setLevel(logging.WARNING)
logging.getLogger("app.services.file_context_analyzer").setLevel(logging.WARNING)
logging.getLogger("app.services.domain_validator").setLevel(logging.WARNING)

# ==============================
# Configuration
# ==============================
BOQ_DIR = Path.home() / "Downloads" / "boq-2026" / "boq"
PROJECT_CODE = "BOQ-2026-MASTER"
PROJECT_NAME = "Master Database Build - BOQ 2026"
EXCEL_EXTENSIONS = {".xlsx", ".xls"}


def create_project(db) -> Project:
    """Create or get the build project."""
    existing = db.query(Project).filter(Project.project_code == PROJECT_CODE).first()
    if existing:
        logger.info(f"Project already exists: {existing.project_code} (ID: {existing.project_id})")
        return existing

    project = Project(
        project_code=PROJECT_CODE,
        project_name=PROJECT_NAME,
        project_type=ProjectType.infrastructure,
        location="Vietnam",
        status=ProjectStatus.active,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    logger.info(f"Created project: {project.project_code} (ID: {project.project_id})")
    return project


def upload_and_process_file(db, project_id: int, file_path: Path, user_id: int = 1) -> int:
    """
    Upload and process a single BOQ file.
    Returns file_id or 0 on failure.
    """
    filename = file_path.name

    # Calculate hash
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    # Check for duplicates
    existing = db.query(BOQFile).filter(BOQFile.file_hash == file_hash).first()
    if existing:
        logger.info(f"  [SKIP] Already uploaded: {filename} (file_id={existing.file_id})")
        return existing.file_id

    # Create FileService (handles normalization, classification)
    service = FileService(db)

    # Save file to uploads dir
    with open(file_path, "rb") as f:
        saved_path = service.save_uploaded_file(f, filename, project_id)

    # Create BOQ file record
    boq_file = BOQFile(
        project_id=project_id,
        file_name=filename,
        file_hash=file_hash,
        file_path=saved_path,
        total_rows=0,
        uploaded_by=user_id,
    )
    db.add(boq_file)
    db.commit()
    db.refresh(boq_file)

    # Analyze structure to check if description column detectable
    try:
        structure = service.analyze_file_structure(saved_path)
        column_mapping = structure.get("column_mapping", {})

        if "description" not in column_mapping.values():
            logger.warning(f"  [WARN] No 'description' column detected in {filename}, trying all sheets...")
            # Try other sheets
            import pandas as pd
            xl = pd.ExcelFile(saved_path)
            found = False
            for sheet in xl.sheet_names:
                try:
                    proc = ExcelProcessor()
                    df = proc.read_excel(saved_path, sheet_name=sheet)
                    header_row = proc.detect_header_row(df)
                    df.columns = df.iloc[header_row]
                    mapping = proc.detect_columns(df.columns.tolist())
                    if "description" in mapping.values():
                        logger.info(f"  Found 'description' in sheet: {sheet}")
                        found = True
                        break
                except Exception:
                    continue

            if not found:
                logger.error(f"  [FAIL] Cannot find description column in {filename}")
                return 0

        # Process file — pass column_mapping=None to let FileService auto-detect
        # (FileService.detect_columns returns {excel_col: standard_col} format
        #  but process_file inverts provided mappings, so None triggers correct auto-detect)
        result = service.process_file(
            file_id=boq_file.file_id,
            file_path=saved_path,
            column_mapping=None,
            user_id=user_id,
        )
        items_count = result.get("processed_items", 0)
        logger.info(f"  [OK] {filename}: {items_count} line items")
        return boq_file.file_id

    except Exception as e:
        logger.error(f"  [FAIL] {filename}: {e}")
        db.rollback()
        # Still keep the BOQ file record for debugging
        return 0


def build_master(db, file_ids: list):
    """Run the 3-step master database build pipeline."""
    builder = get_master_database_builder(db)

    config = BuildConfig(
        pareto_threshold=0.80,
        clustering_threshold=0.85,
        min_frequency=1,
        auto_approve=True,  # Auto-approve for batch build
        clear_existing=True,  # Fresh rebuild
        include_only_pareto=False,  # Process all items
    )

    def progress(step, current, total):
        logger.info(f"  Pipeline step: {step} ({current}/{total})")

    result = builder.build(file_ids=file_ids, config=config, progress_callback=progress)

    return result


def print_report(result, file_ids, total_line_items, elapsed):
    """Print build report."""
    print("\n" + "=" * 70)
    print("  MASTER DATABASE BUILD REPORT")
    print("=" * 70)
    print(f"  Files processed:      {len(file_ids)}")
    print(f"  Total line items:     {total_line_items}")
    print(f"  Build time:           {elapsed:.1f}s")
    print()
    print("  Step 1 - Aggregation:")
    print(f"    Input files:        {result.step1_stats.input_count}")
    print(f"    Unique descriptions:{result.step1_stats.output_count}")
    d = result.step1_stats.details
    print(f"    Total scanned:      {d.get('total_line_items_scanned', 'N/A')}")
    print()
    print("  Step 2 - Standardization:")
    print(f"    Input items:        {result.step2_stats.input_count}")
    print(f"    After clustering:   {result.step2_stats.output_count}")
    d2 = result.step2_stats.details
    print(f"    Clusters formed:    {d2.get('clusters_formed', 'N/A')}")
    print(f"    Pareto top:         {d2.get('pareto_top_count', 'N/A')}")
    print(f"    Below Pareto:       {d2.get('below_pareto_count', 'N/A')}")
    print(f"    Total synonyms:     {d2.get('total_synonyms', 'N/A')}")
    print()
    print("  Step 3 - Coding & Tagging:")
    print(f"    Input items:        {result.step3_stats.input_count}")
    d3 = result.step3_stats.details
    print(f"    Approved (master):  {d3.get('approved', 0)}")
    print(f"    Pending review:     {d3.get('pending', 0)}")
    print(f"    Rejected:           {d3.get('rejected', 0)}")
    print(f"    Updated existing:   {d3.get('updated', 0)}")
    by_sec = d3.get("by_sec_code", {})
    if by_sec:
        print(f"    By SEC code:")
        for sec, count in sorted(by_sec.items()):
            print(f"      {sec}: {count}")
    print()
    print("  Totals:")
    print(f"    Master items added: {result.total_master_added}")
    print(f"    Pending items:      {result.total_pending}")
    print(f"    Quarantined:        {result.total_quarantined}")
    print(f"    Updated:            {result.total_updated}")
    print(f"    Synonyms added:     {result.total_synonyms_added}")
    print("=" * 70)


def main():
    if not BOQ_DIR.exists():
        logger.error(f"BOQ directory not found: {BOQ_DIR}")
        sys.exit(1)

    # List Excel files
    excel_files = sorted(
        f for f in BOQ_DIR.iterdir()
        if f.suffix.lower() in EXCEL_EXTENSIONS
    )
    logger.info(f"Found {len(excel_files)} Excel files in {BOQ_DIR}")

    if not excel_files:
        logger.error("No Excel files found")
        sys.exit(1)

    db = SessionLocal()
    try:
        # Step 1: Create project
        project = create_project(db)

        # Step 2: Upload and process each file
        logger.info(f"\n{'='*70}")
        logger.info(f"  PHASE 1: Upload and parse {len(excel_files)} BOQ files")
        logger.info(f"{'='*70}")

        file_ids = []
        failed_files = []
        t0 = time.time()

        for i, file_path in enumerate(excel_files, 1):
            logger.info(f"[{i}/{len(excel_files)}] {file_path.name}")
            fid = upload_and_process_file(db, project.project_id, file_path)
            if fid:
                file_ids.append(fid)
            else:
                failed_files.append(file_path.name)

        t_upload = time.time() - t0
        logger.info(f"\nUpload phase complete: {len(file_ids)} ok, {len(failed_files)} failed ({t_upload:.1f}s)")
        if failed_files:
            logger.warning(f"Failed files: {failed_files}")

        # Count total line items
        total_li = db.query(LineItem).filter(
            LineItem.file_id.in_(file_ids)
        ).count() if file_ids else 0
        logger.info(f"Total line items created: {total_li}")

        if not file_ids:
            logger.error("No files processed successfully. Aborting master build.")
            sys.exit(1)

        # Step 3: Build master database
        logger.info(f"\n{'='*70}")
        logger.info(f"  PHASE 2: Build Master Database (3-step pipeline)")
        logger.info(f"{'='*70}")

        t1 = time.time()
        result = build_master(db, file_ids)
        t_build = time.time() - t1

        # Report
        print_report(result, file_ids, total_li, t_build)

        # Final DB stats
        with engine.connect() as conn:
            master_count = conn.execute(text("SELECT COUNT(*) FROM master_work_items WHERE is_active=1")).scalar()
            pending_count = conn.execute(text("SELECT COUNT(*) FROM pending_master_items")).scalar()
            synonym_count = conn.execute(text("SELECT COUNT(*) FROM master_synonyms WHERE is_active=1")).scalar()

        print(f"\n  Database state:")
        print(f"    Active master items:  {master_count}")
        print(f"    Pending items:        {pending_count}")
        print(f"    Active synonyms:      {synonym_count}")
        print(f"    Total elapsed:        {t_upload + t_build:.1f}s")
        print()

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        db.rollback()
    except Exception as e:
        logger.error(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
