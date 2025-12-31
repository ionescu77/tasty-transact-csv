#!/usr/bin/env python3
"""Recreate database with updated schema."""

import os
from app.database import engine, create_db_and_tables
from sqlmodel import SQLModel

def recreate_database():
    """Drop and recreate all tables."""
    # Remove existing database
    db_path = "tastytrade.db"
    if os.path.exists(db_path):
        print(f"Removing existing database: {db_path}")
        os.remove(db_path)
    
    # Create new database with updated schema
    print("Creating new database with updated schema...")
    create_db_and_tables()
    print("✓ Database created successfully!")
    print("\nNew tables:")
    print("  - symbols (new)")
    print("  - accounts (updated: added description, updated_at)")
    print("  - spreads (updated: added status, closed_at, comment, comment_updated_at, tags, updated_at)")
    print("  - transactions (updated: removed industry_tag, sector_tag)")
    print("  - positions (updated: added status, tags, opened_at, closed_at)")
    print("  - trade_metrics")

if __name__ == "__main__":
    recreate_database()
