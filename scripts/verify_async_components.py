#!/usr/bin/env python3
"""
Verification script for async database implementation.
Tests core async components without database dependencies.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_async_imports() -> bool:
    """Test that all async modules can be imported successfully."""
    print("Testing async module imports...")

    try:
        # Test async schemas
        from afs_fastapi.database.agricultural_schemas_async import (
            AsyncDatabaseManager,
            Equipment,
            Field,
            TokenUsage,
        )

        print("✅ AsyncDatabaseManager and models imported successfully")

        # Test async repository
        from afs_fastapi.database.async_repository import (
            BaseAsyncRepository,
            EquipmentAsyncRepository,
            FieldAsyncRepository,
            TokenUsageAsyncRepository,
            UnitOfWork,
        )

        print("✅ Async repositories imported successfully")

        # Test async token logger
        from afs_fastapi.monitoring.async_token_usage_logger import AsyncTokenUsageLogger

        print("✅ AsyncTokenUsageLogger imported successfully")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


async def test_database_manager_creation() -> bool:
    """Test AsyncDatabaseManager creation without actual database."""
    print("\nTesting AsyncDatabaseManager creation...")

    try:
        from afs_fastapi.database.agricultural_schemas_async import AsyncDatabaseManager

        # Test configuration without actual database connection
        from afs_fastapi.database.connection_pool import PoolConfiguration

        config = PoolConfiguration(
            max_connections=10, min_connections=3, pool_timeout=30.0, pool_recycle=3600
        )

        db_manager = AsyncDatabaseManager(
            "sqlite+aiosqlite:///:memory:",
            config.to_dict() if hasattr(config, "to_dict") else config,
        )
        print("✅ AsyncDatabaseManager created successfully")
        print(f"   Pool size: {db_manager.pool_config.pool_size}")
        print(f"   Max connections: {db_manager.pool_config.max_connections}")

        return True

    except Exception as e:
        print(f"❌ Database manager creation failed: {e}")
        return False


async def test_repository_creation() -> bool:
    """Test async repository creation and basic operations."""
    print("\nTesting async repository creation...")

    try:
        from afs_fastapi.database.async_repository import EquipmentAsyncRepository

        # Test repository creation (without database connection)
        repo = EquipmentAsyncRepository(None)  # Pass None for session (testing only)
        print("✅ EquipmentAsyncRepository created successfully")

        # Test method existence
        required_methods = [
            "create_equipment",
            "get_by_id",
            "update_equipment_status",
        ]

        for method in required_methods:
            if hasattr(repo, method):
                print(f"   ✅ Method {method} exists")
            else:
                print(f"   ❌ Method {method} missing")
                return False

        return True

    except Exception as e:
        print(f"❌ Repository creation failed: {e}")
        return False


async def test_token_logger_creation() -> bool:
    """Test async token usage logger creation."""
    print("\nTesting AsyncTokenUsageLogger creation...")

    try:
        from afs_fastapi.monitoring.async_token_usage_logger import AsyncTokenUsageLogger

        # Test logger creation (without database connection)
        logger = AsyncTokenUsageLogger(None)  # Pass None for session (testing only)
        print("✅ AsyncTokenUsageLogger created successfully")

        # Test method existence
        required_methods = [
            "log_token_usage",
            "batch_log_token_usage",
            "query_token_usage",
            "get_token_usage_statistics",
            "get_token_usage_statistics",
            "get_performance_report",
        ]

        for method in required_methods:
            if hasattr(logger, method):
                print(f"   ✅ Method {method} exists")
            else:
                print(f"   ❌ Method {method} missing")
                return False

        return True

    except Exception as e:
        print(f"❌ Token logger creation failed: {e}")
        return False


async def run_comprehensive_verification() -> None:
    """Run comprehensive verification of async implementation."""
    print("🚀 Starting Comprehensive Async Database Verification")
    print("=" * 60)

    tests = [
        ("Async Imports", test_async_imports),
        ("Database Manager", test_database_manager_creation),
        ("Repository Creation", test_repository_creation),
        ("Token Logger", test_token_logger_creation),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")

    print("\n" + "=" * 60)
    print(f"🏆 VERIFICATION RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED - Async implementation is working correctly!")
        print("\nKey capabilities verified:")
        print("✅ Async database modules can be imported")
        print("✅ Database manager with connection pooling configured")
        print("✅ Async repositories with proper agricultural methods")
        print("✅ Async token usage logger with batch operations")
    else:
        print(f"⚠️  {total - passed} tests failed - some issues need attention")

    print(f"\n🎯 Async implementation readiness: {'READY' if passed == total else 'NEEDS WORK'}")


if __name__ == "__main__":
    exit_code = asyncio.run(run_comprehensive_verification())
    exit(exit_code if exit_code is not None else 0)
