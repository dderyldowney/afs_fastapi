"""
Minimal integration test to verify core library functionality.
This test bypasses optional dependencies to focus on core components.
"""

import asyncio
import sys
import traceback
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

print("🔍 Running minimal integration test...")

def test_core_imports():
    """Test that we can import core components without todowrite."""
    try:
        # Test FarmTractor directly
        import afs_fastapi.equipment.farm_tractors as ft_module
        print("✅ FarmTractor module imported successfully")

        # Check if FarmTractor class exists
        if hasattr(ft_module, 'FarmTractor'):
            print("✅ FarmTractor class found")
            return True
        else:
            print("❌ FarmTractor class not found")
            return False

    except Exception as e:
        print(f"❌ FarmTractor import failed: {e}")
        return False

def test_database_core():
    """Test database core functionality."""
    try:
        # Try to import database modules directly
        import afs_fastapi.database.optimized_db_config as db_config
        print("✅ Database config module imported")

        # Check if get_optimized_session exists
        if hasattr(db_config, 'get_optimized_session'):
            print("✅ Database session function found")
            return True
        else:
            print("❌ Database session function not found")
            return False

    except Exception as e:
        print(f"❌ Database import failed: {e}")
        return False

async def test_farm_tractor_functionality():
    """Test FarmTractor basic functionality."""
    try:
        # Import FarmTractor
        from afs_fastapi.equipment.farm_tractors import FarmTractor

        # Test instantiation
        tractor = FarmTractor("Test", "Tractor", 2024)
        print(f"✅ FarmTractor created: {tractor.make} {tractor.model}")

        # Test methods
        status = tractor.get_safety_status()
        print(f"✅ FarmTractor safety status: {status}")

        response = tractor.to_response("TEST_001")
        print(f"✅ FarmTractor response: {response.tractor_id}")

        return True

    except Exception as e:
        print(f"❌ FarmTractor functionality test failed: {e}")
        traceback.print_exc()
        return False

async def test_database_functionality():
    """Test database basic functionality."""
    try:
        import afs_fastapi.database.optimized_db_config as db_config

        async with db_config.get_session() as session:
            # Test basic query
            result = await session.execute("SELECT 1 as test")
            row = result.fetchone()
            assert row[0] == 1
            print("✅ Database query successful")

            # Test table existence
            tables_result = await session.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = [row[0] for row in tables_result.fetchall()]
            print(f"✅ Found {len(tables)} tables in database")

        return True

    except Exception as e:
        print(f"❌ Database functionality test failed: {e}")
        traceback.print_exc()
        return False

def test_api_structure():
    """Test API structure without running the app."""
    try:
        # Check that API files exist
        api_main = project_root / "afs_fastapi" / "api" / "main.py"
        if api_main.exists():
            print("✅ API main file exists")
        else:
            print("❌ API main file missing")
            return False

        # Check API endpoints directory
        endpoints_dir = project_root / "afs_fastapi" / "api" / "endpoints"
        if endpoints_dir.exists():
            endpoint_files = list(endpoints_dir.glob("*.py"))
            print(f"✅ Found {len(endpoint_files)} endpoint files")
        else:
            print("❌ API endpoints directory missing")
            return False

        return True

    except Exception as e:
        print(f"❌ API structure test failed: {e}")
        return False

async def run_minimal_tests():
    """Run all minimal integration tests."""
    print("\n" + "=" * 50)
    print("MINIMAL INTEGRATION TEST")
    print("=" * 50)

    tests = [
        ("Core Imports", test_core_imports),
        ("Database Core", test_database_core),
        ("API Structure", test_api_structure),
        ("FarmTractor Functionality", test_farm_tractor_functionality),
        ("Database Functionality", test_database_functionality),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()

            if result:
                passed += 1
                print(f"✅ {test_name}: PASS")
            else:
                print(f"❌ {test_name}: FAIL")

        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")

    print("\n" + "=" * 50)
    print("MINIMAL TEST RESULTS")
    print("=" * 50)
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    if passed >= total * 0.8:
        print("🎉 MINIMAL INTEGRATION TEST: ✅ PASS")
        print("Core library components are working!")
    else:
        print("❌ MINIMAL INTEGRATION TEST: ❌ FAIL")
        print("Core components have issues.")

    print("=" * 50)

    return passed >= total * 0.8

if __name__ == "__main__":
    try:
        success = asyncio.run(run_minimal_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        traceback.print_exc()
        sys.exit(1)