#!/usr/bin/env python3
"""
Database Migration Runner

Runs SQL migrations in order. Supports both apply and rollback operations.

Usage:
    python run_migrations.py apply          # Apply all pending migrations
    python run_migrations.py rollback       # Rollback last migration
    python run_migrations.py status         # Show migration status
    python run_migrations.py apply <name>   # Apply specific migration
"""
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

import pymysql
from pymysql import Error

# Migration order (apply these in sequence)
MIGRATIONS = [
    "add_normalized_description.sql",
    "add_separated_specs.sql",
    "add_master_synonyms.sql",
    "add_approval_workflow_tables.sql",
]

# Rollback files (paired with migrations)
ROLLBACKS = {
    "add_separated_specs.sql": "rollback_separated_specs.sql",
    "add_master_synonyms.sql": "rollback_master_synonyms.sql",
    "add_approval_workflow_tables.sql": "rollback_approval_workflow_tables.sql",
}


def get_db_connection():
    """Create database connection from environment."""
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "boq_system"),
        cursorclass=pymysql.cursors.DictCursor,
    )


def ensure_migrations_table(cursor):
    """Create migrations tracking table if not exists."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            checksum VARCHAR(64)
        )
    """)


def get_applied_migrations(cursor):
    """Get list of already applied migrations."""
    cursor.execute("SELECT name FROM _migrations ORDER BY id")
    return [row[0] for row in cursor.fetchall()]


def get_migration_path():
    """Get path to migrations directory."""
    return Path(__file__).parent


def run_migration_file(cursor, filepath: Path):
    """Execute a SQL migration file."""
    sql = filepath.read_text(encoding='utf-8')

    # Split by semicolons for multi-statement execution
    statements = [s.strip() for s in sql.split(';') if s.strip()]

    for statement in statements:
        if statement and not statement.startswith('--'):
            try:
                cursor.execute(statement)
                # Consume any results
                try:
                    cursor.fetchall()
                except:
                    pass
            except Error as e:
                # Ignore "already exists" errors for idempotent migrations
                if "already exists" in str(e).lower():
                    print(f"  (skipped: already exists)")
                    continue
                elif "duplicate" in str(e).lower():
                    print(f"  (skipped: duplicate)")
                    continue
                else:
                    raise


def apply_migration(conn, cursor, name: str, migrations_path: Path):
    """Apply a single migration."""
    filepath = migrations_path / name

    if not filepath.exists():
        print(f"ERROR: Migration file not found: {filepath}")
        return False

    print(f"Applying: {name}")

    try:
        run_migration_file(cursor, filepath)
        cursor.execute(
            "INSERT INTO _migrations (name) VALUES (%s)",
            (name,)
        )
        conn.commit()
        print(f"  SUCCESS")
        return True
    except Error as e:
        conn.rollback()
        print(f"  FAILED: {e}")
        return False


def rollback_migration(conn, cursor, name: str, migrations_path: Path):
    """Rollback a single migration."""
    rollback_file = ROLLBACKS.get(name)

    if not rollback_file:
        print(f"ERROR: No rollback file for {name}")
        return False

    filepath = migrations_path / rollback_file

    if not filepath.exists():
        print(f"ERROR: Rollback file not found: {filepath}")
        return False

    print(f"Rolling back: {name}")

    try:
        run_migration_file(cursor, filepath)
        cursor.execute(
            "DELETE FROM _migrations WHERE name = %s",
            (name,)
        )
        conn.commit()
        print(f"  SUCCESS")
        return True
    except Error as e:
        conn.rollback()
        print(f"  FAILED: {e}")
        return False


def cmd_apply(args):
    """Apply pending migrations."""
    migrations_path = get_migration_path()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        ensure_migrations_table(cursor)
        applied = get_applied_migrations(cursor)

        if args.name:
            # Apply specific migration
            if args.name in applied:
                print(f"Migration {args.name} already applied")
                return
            apply_migration(conn, cursor, args.name, migrations_path)
        else:
            # Apply all pending
            pending = [m for m in MIGRATIONS if m not in applied]

            if not pending:
                print("All migrations are up to date")
                return

            print(f"Applying {len(pending)} migrations...")
            for name in pending:
                if not apply_migration(conn, cursor, name, migrations_path):
                    print("Migration failed. Stopping.")
                    break

    except Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals() and conn.open:
            cursor.close()
            conn.close()


def cmd_rollback(args):
    """Rollback last migration."""
    migrations_path = get_migration_path()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        ensure_migrations_table(cursor)
        applied = get_applied_migrations(cursor)

        if not applied:
            print("No migrations to rollback")
            return

        if args.name:
            if args.name not in applied:
                print(f"Migration {args.name} is not applied")
                return
            rollback_migration(conn, cursor, args.name, migrations_path)
        else:
            # Rollback last applied
            last = applied[-1]
            rollback_migration(conn, cursor, last, migrations_path)

    except Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals() and conn.open:
            cursor.close()
            conn.close()


def cmd_status(args):
    """Show migration status."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        ensure_migrations_table(cursor)
        applied = get_applied_migrations(cursor)

        print("\nMigration Status")
        print("=" * 50)

        for name in MIGRATIONS:
            status = "APPLIED" if name in applied else "PENDING"
            icon = "✓" if status == "APPLIED" else "○"
            print(f"  {icon} {name:40} [{status}]")

        print()
        print(f"Applied: {len(applied)} / {len(MIGRATIONS)}")

    except Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals() and conn.open:
            cursor.close()
            conn.close()


def main():
    parser = argparse.ArgumentParser(description="Database Migration Runner")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Apply command
    apply_parser = subparsers.add_parser("apply", help="Apply migrations")
    apply_parser.add_argument("name", nargs="?", help="Specific migration to apply")

    # Rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Rollback migrations")
    rollback_parser.add_argument("name", nargs="?", help="Specific migration to rollback")

    # Status command
    subparsers.add_parser("status", help="Show migration status")

    args = parser.parse_args()

    if args.command == "apply":
        cmd_apply(args)
    elif args.command == "rollback":
        cmd_rollback(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
