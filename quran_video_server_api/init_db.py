#!/usr/bin/env python3
# init_db.py
"""
Database initialization script for the Quran Video Generator API.

This script creates the database and all required tables.
Run this before starting the API server for the first time.

Usage:
    python init_db.py [--db-url DATABASE_URL]

Examples:
    # Create default SQLite database
    python init_db.py

    # Create SQLite database at custom location
    python init_db.py --db-url "sqlite:///custom_path.db"

    # Create PostgreSQL database
    python init_db.py --db-url "postgresql://user:pass@localhost:5432/quranvideo"
"""
import argparse
import sys
from pathlib import Path

try:
    from models import (
        create_database_engine,
        init_database,
        get_database_url
    )
    from config_new import config
except ImportError as e:
    print(f"Error: Failed to import required modules: {e}")
    print("Make sure you have installed all dependencies:")
    print("  pip install -r requirements.txt")
    sys.exit(1)


def main():
    """Initialize the database."""
    parser = argparse.ArgumentParser(
        description="Initialize the Quran Video Generator database"
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="Database URL (e.g., sqlite:///path.db or postgresql://user:pass@host/db)"
    )
    parser.add_argument(
        "--echo",
        action="store_true",
        help="Echo SQL statements to console"
    )

    args = parser.parse_args()

    # Determine database URL
    if args.db_url:
        database_url = args.db_url
    else:
        database_url = config.database_url

    print(f"Initializing database: {database_url}")

    try:
        # Create engine
        engine = create_database_engine(database_url, echo=args.echo)

        # Create all tables
        init_database(engine)

        print("✓ Database initialized successfully!")
        print(f"✓ Location: {database_url}")
        print("\nYou can now start the API server:")
        print("  uvicorn main:app --reload")

        return 0

    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
