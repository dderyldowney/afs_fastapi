"""
FarmTractor Test Verification Script

This script verifies that FarmTractor tests use the real implementation
instead of mocks or stubs.
"""

import ast
import re
import sys
from pathlib import Path


def verify_farm_tractor_tests():
    """Verify FarmTractor tests use real implementation."""
    print("=== FarmTractor Test Verification ===")

    # Find test files that might test FarmTractor
    test_patterns = [
        "tests/unit/equipment/test_farm_tractors.py",
        "tests/integration/test_farm_tractors.py",
        "tests/*/test_farm_tractors.py",
        "tests/**/test_*tractor*.py"
    ]

    test_files = []
    for pattern in test_patterns:
        for test_file in Path(".").glob(pattern):
            if test_file.is_file():
                test_files.append(test_file)

    if not test_files:
        print("❌ No FarmTractor test files found")
        return False

    print(f"Found {len(test_files)} potential test files:")
    for test_file in test_files:
        print(f"  - {test_file}")

    results = []

    for test_file in test_files:
        print(f"\n--- Analyzing {test_file} ---")

        try:
            with open(test_file, encoding='utf-8') as f:
                content = f.read()

            # Parse AST
            tree = ast.parse(content)

            # Check for mocking indicators
            mock_indicators = [
                "mock", "Mock", "@patch", "@mock_", "MagicMock", "AsyncMock",
                "unittest.mock", "pytest.mock"
            ]

            has_mocks = any(indicator in content for indicator in mock_indicators)

            # Count mock occurrences
            mock_count = sum(content.count(indicator) for indicator in mock_indicators)

            # Check for real FarmTractor import
            import_patterns = [
                "from afs_fastapi.equipment.farm_tractors import FarmTractor",
                "from afs_fastapi.equipment import FarmTractor",
                "import afs_fastapi.equipment.farm_tractors"
            ]

            has_real_import = any(pattern in content for pattern in import_patterns)

            # Check for test functions
            test_functions = [
                node.name for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
            ]

            # Check for FarmTractor usage in tests
            farm_tractor_usage = len(re.findall(r"FarmTractor", content))

            # Analyze mock usage patterns
            mock_heavy = mock_count > 5  # More than 5 mock indicators = heavy mocking

            # Check if tests actually instantiate FarmTractor
            instantiates_farm_tractor = bool(re.search(r"FarmTractor\s*\(", content))

            print(f"  Real FarmTractor import: {'✅ YES' if has_real_import else '❌ NO'}")
            print(f"  Uses mocks: {'⚠️  YES' if has_mocks else '✅ NO'}")
            print(f"  Mock indicators count: {mock_count}")
            print(f"  Test functions: {len(test_functions)}")
            print(f"  FarmTractor usage count: {farm_tractor_usage}")
            print(f"  Instantiates FarmTractor: {'✅ YES' if instantiates_farm_tractor else '❌ NO'}")
            print(f"  Mock-heavy: {'⚠️  YES' if mock_heavy else '✅ NO'}")

            # Determine test quality
            test_quality_good = (
                has_real_import and
                not mock_heavy and
                instantiates_farm_tractor and
                len(test_functions) > 0
            )

            print(f"  Test Quality: {'✅ GOOD' if test_quality_good else '⚠️  NEEDS REVIEW'}")

            # Show sample test functions
            if test_functions:
                print(f"  Sample test functions: {test_functions[:3]}")

            results.append({
                'file': str(test_file),
                'has_real_import': has_real_import,
                'has_mocks': has_mocks,
                'mock_count': mock_count,
                'test_count': len(test_functions),
                'farm_tractor_usage': farm_tractor_usage,
                'instantiates_farm_tractor': instantiates_farm_tractor,
                'mock_heavy': mock_heavy,
                'quality_good': test_quality_good
            })

        except Exception as e:
            print(f"  ❌ Error analyzing file: {e}")
            results.append({
                'file': str(test_file),
                'error': str(e),
                'quality_good': False
            })

    # Summary
    print("\n=== Summary ===")
    total_files = len(results)
    files_with_real_import = sum(1 for r in results if r.get('has_real_import', False))
    files_with_mocks = sum(1 for r in results if r.get('has_mocks', False))
    mock_heavy_files = sum(1 for r in results if r.get('mock_heavy', False))
    good_quality_files = sum(1 for r in results if r.get('quality_good', False))
    total_tests = sum(r.get('test_count', 0) for r in results)

    print(f"Total test files analyzed: {total_files}")
    print(f"Files with real FarmTractor import: {files_with_real_import}")
    print(f"Files using mocks: {files_with_mocks}")
    print(f"Files with heavy mocking: {mock_heavy_files}")
    print(f"Files with good test quality: {good_quality_files}")
    print(f"Total test functions: {total_tests}")

    # Overall assessment
    overall_quality = (
        total_files > 0 and
        files_with_real_import == total_files and
        mock_heavy_files == 0 and
        good_quality_files > 0
    )

    print(f"\nOverall Test Quality: {'✅ EXCELLENT' if overall_quality else '⚠️  NEEDS ATTENTION'}")

    if overall_quality:
        print("✅ Tests use real FarmTractor implementation")
    else:
        if files_with_real_import == 0:
            print("❌ No tests import real FarmTractor class")
        if mock_heavy_files > 0:
            print("⚠️  Some tests are mock-heavy")
        if good_quality_files == 0:
            print("❌ No tests meet quality standards")

    return overall_quality

if __name__ == "__main__":
    result = verify_farm_tractor_tests()
    print(f"\n{'='*60}")
    print(f"FINAL RESULT: FarmTractor tests {'USE REAL' if result else 'USE MOCKS/STUBS'}")
    print(f"{'='*60}")

    # Exit with appropriate code
    sys.exit(0 if result else 1)