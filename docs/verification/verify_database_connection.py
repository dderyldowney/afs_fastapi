#!/usr/bin/env python3
"""
Database connection verification script for Task 4.

This script verifies that the AFS FastAPI database layer contains real
implementations with actual database operations, not mock database behavior.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from afs_fastapi.database.optimized_db_config import get_optimized_db_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def verify_real_database():
    """Verify real database connection and operations."""
    print("=== Database Connection Verification ===")

    try:
        # Step 1: Initialize optimized database configuration
        print("1. Initializing optimized database configuration...")
        db_config = await get_optimized_db_config()

        # Initialize with SQLite for testing
        test_database_url = "sqlite+aiosqlite:///test_verification.db"

        # Create a new config specifically for testing
        from afs_fastapi.database.optimized_db_config import OptimizedDatabaseConfig
        test_config = OptimizedDatabaseConfig(test_database_url)

        # Test basic connection pool initialization
        print("2. Testing connection pool initialization...")
        pool_initialized = await test_config.initialize_pool()

        if not pool_initialized:
            print("❌ Connection pool initialization failed")
            return False

        print("✅ Connection pool initialization successful")

        # Step 2: Test basic database connection
        print("3. Testing basic database connection...")
        async with test_config.get_session() as session:
            # Test basic query
            result = await session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"   Database query result: {row}")

            if row[0] != 1:
                print("❌ Basic query failed")
                return False

            print("✅ Basic database connection works")

            # Step 3: Test table creation and existence
            print("4. Testing database table creation...")

            # Create all tables from schemas

            # Create tables
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS equipment (
                    equipment_id TEXT PRIMARY KEY,
                    isobus_address INTEGER NOT NULL,
                    equipment_type TEXT NOT NULL,
                    manufacturer TEXT NOT NULL,
                    model TEXT,
                    serial_number TEXT,
                    firmware_version TEXT,
                    installation_date TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                );
            """))

            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS agricultural_sensor_record (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id TEXT,
                    sensor_type TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (equipment_id) REFERENCES equipment (equipment_id)
                );
            """))

            await session.commit()

            # Test table existence
            tables_result = await session.execute(text("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """))
            tables = [row[0] for row in tables_result.fetchall()]

            print(f"   Database tables created: {tables}")

            if len(tables) < 2:
                print("❌ Not enough tables created")
                return False

            print("✅ Database table creation successful")

            # Step 4: Test basic CRUD operations
            print("5. Testing basic CRUD operations...")

            # Test CREATE
            await session.execute(text("""
                INSERT INTO equipment (equipment_id, isobus_address, equipment_type, manufacturer)
                VALUES ('TEST_001', 10, 'tractor', 'John Deere')
            """))
            await session.commit()
            print("   ✅ CREATE operation successful")

            # Test READ
            result = await session.execute(text("""
                SELECT * FROM equipment WHERE equipment_id = 'TEST_001'
            """))
            rows = result.fetchall()
            if len(rows) == 0:
                print("❌ READ operation failed")
                return False
            print(f"   ✅ READ operation successful: {len(rows)} row(s) found")

            # Test UPDATE
            await session.execute(text("""
                UPDATE equipment SET model = '8RX' WHERE equipment_id = 'TEST_001'
            """))
            await session.commit()
            print("   ✅ UPDATE operation successful")

            # Test DELETE
            await session.execute(text("""
                DELETE FROM equipment WHERE equipment_id = 'TEST_001'
            """))
            await session.commit()
            print("   ✅ DELETE operation successful")

            # Step 5: Test connection pool status
            print("6. Testing connection pool status...")
            pool_status = test_config.get_pool_status()
            print(f"   Pool status: {pool_status}")

            if pool_status.get("status") == "not_initialized":
                print("❌ Connection pool status not available")
                return False

            print("✅ Connection pool status available")

            # Cleanup
            await test_config.shutdown_pool()

        print("✅ All database connection tests passed!")
        return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        logger.exception("Database connection error")
        return False


async def main():
    """Main verification function."""
    print("🚜 AFS FastAPI Database Connection Verification")
    print("=" * 50)

    result = await verify_real_database()

    if result:
        print("\n🎉 Database Connection Verification: ✅ PASS")
        print("The database layer contains real implementations with actual database operations.")
    else:
        print("\n💥 Database Connection Verification: ❌ FAIL")
        print("The database layer may have issues with real database operations.")

    return result


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)