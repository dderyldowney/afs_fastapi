#!/usr/bin/env python3
"""
Test Suite Analysis Script for AFS FastAPI Library Verification

This script analyzes the entire test suite to determine if tests are using
real implementations rather than mocks or stubs. It provides comprehensive
metrics on test quality and implementation usage.
"""

import ast
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


def analyze_test_file(test_file: Path) -> dict[str, Any]:
    """Analyze a single test file for implementation usage."""
    try:
        with open(test_file, encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        # Basic metrics
        test_count = len([n for n in ast.walk(tree)
                         if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")])
        async_test_count = len([n for n in ast.walk(tree)
                               if isinstance(n, ast.AsyncFunctionDef) and n.name.startswith("test_")])

        # Mock detection
        mock_indicators = ["@patch", "@mock_", "Mock(", "mock_", "MagicMock", "AsyncMock"]
        mock_count = sum(content.count(indicator) for indicator in mock_indicators)
        has_mocks = mock_count > 0

        # Real import detection
        real_import_patterns = [
            r"from afs_fastapi\.",
            r"import afs_fastapi\.",
            r"from \.\.",
            r"from \."
        ]

        has_real_imports = any(re.search(pattern, content) for pattern in real_import_patterns)

        # Import analysis
        afs_imports = re.findall(r"from afs_fastapi\.([^\s]+) import", content)
        relative_imports = re.findall(r"from \.+([^\s]+) import", content)

        # Test complexity analysis
        avg_test_length = 0
        if test_count > 0:
            test_functions = [n for n in ast.walk(tree)
                            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and n.name.startswith("test_")]
            total_lines = sum(n.end_lineno - n.lineno for n in test_functions)
            avg_test_length = total_lines / test_count

        # Assertion analysis (more assertions = better testing)
        assertion_count = len([n for n in ast.walk(tree) if isinstance(n, ast.Assert)])

        return {
            "file": str(test_file),
            "test_count": test_count,
            "async_test_count": async_test_count,
            "mock_count": mock_count,
            "has_mocks": has_mocks,
            "has_real_imports": has_real_imports,
            "afs_imports": afs_imports,
            "relative_imports": relative_imports,
            "avg_test_length": avg_test_length,
            "assertion_count": assertion_count,
            "assertion_per_test": assertion_count / max(test_count, 1)
        }

    except Exception as e:
        return {
            "file": str(test_file),
            "error": str(e),
            "test_count": 0,
            "mock_count": 0,
            "has_mocks": False,
            "has_real_imports": False
        }


def categorize_test_quality(analysis: dict[str, Any]) -> str:
    """Categorize test quality based on metrics."""
    if analysis.get("error"):
        return "error"

    test_count = analysis["test_count"]
    mock_ratio = analysis["mock_count"] / max(test_count, 1)
    has_real = analysis["has_real_imports"]
    assertions_per_test = analysis["assertion_per_test"]

    if test_count == 0:
        return "empty"
    elif mock_ratio > 2.0:
        return "mock_heavy"
    elif not has_real:
        return "no_real_imports"
    elif assertions_per_test < 1.0:
        return "low_assertions"
    elif mock_ratio == 0 and has_real and assertions_per_test >= 2.0:
        return "excellent"
    elif mock_ratio <= 0.5 and has_real and assertions_per_test >= 1.0:
        return "good"
    else:
        return "acceptable"


def analyze_test_suite() -> dict[str, Any]:
    """Analyze the entire test suite."""
    test_dir = Path("tests")

    if not test_dir.exists():
        return {"error": "tests directory not found"}

    analysis = {
        "summary": {
            "total_test_files": 0,
            "total_tests": 0,
            "total_async_tests": 0,
            "files_with_mocks": 0,
            "files_with_real_imports": 0,
            "total_mocks": 0,
            "total_assertions": 0
        },
        "quality_distribution": defaultdict(int),
        "files_by_category": defaultdict(list),
        "detailed_analysis": [],
        "mock_heavy_files": [],
        "real_implementation_files": [],
        "import_analysis": defaultdict(int),
        "problematic_files": []
    }

    # Analyze each test file
    for test_file in test_dir.rglob("*.py"):
        if "test_" not in test_file.name or test_file.name.startswith("__"):
            continue

        file_analysis = analyze_test_file(test_file)
        analysis["detailed_analysis"].append(file_analysis)

        # Update summary
        analysis["summary"]["total_test_files"] += 1
        analysis["summary"]["total_tests"] += file_analysis["test_count"]
        analysis["summary"]["total_async_tests"] += file_analysis["async_test_count"]
        analysis["summary"]["total_mocks"] += file_analysis["mock_count"]
        analysis["summary"]["total_assertions"] += file_analysis["assertion_count"]

        if file_analysis["has_mocks"]:
            analysis["summary"]["files_with_mocks"] += 1

        if file_analysis["has_real_imports"]:
            analysis["summary"]["files_with_real_imports"] += 1
            analysis["real_implementation_files"].append(file_analysis["file"])

        # Categorize quality
        quality = categorize_test_quality(file_analysis)
        analysis["quality_distribution"][quality] += 1
        analysis["files_by_category"][quality].append(file_analysis["file"])

        # Track problematic files
        if file_analysis.get("error"):
            analysis["problematic_files"].append(file_analysis["file"])
        elif quality in ["mock_heavy", "no_real_imports", "empty"]:
            analysis["problematic_files"].append(file_analysis["file"])

        # Track mock-heavy files (more than 3 mocks)
        if file_analysis["mock_count"] > 3:
            analysis["mock_heavy_files"].append({
                "file": file_analysis["file"],
                "mock_count": file_analysis["mock_count"],
                "test_count": file_analysis["test_count"],
                "mock_ratio": file_analysis["mock_count"] / max(file_analysis["test_count"], 1)
            })

        # Import analysis
        for imp in file_analysis["afs_imports"]:
            analysis["import_analysis"][f"afs_fastapi.{imp}"] += 1
        for imp in file_analysis["relative_imports"]:
            analysis["import_analysis"][f"relative.{imp}"] += 1

    # Calculate quality metrics
    total_files = analysis["summary"]["total_test_files"]
    if total_files > 0:
        analysis["quality_metrics"] = {
            "real_implementation_percentage": (analysis["summary"]["files_with_real_imports"] / total_files) * 100,
            "mock_heavy_percentage": (len(analysis["mock_heavy_files"]) / total_files) * 100,
            "problematic_percentage": (len(analysis["problematic_files"]) / total_files) * 100,
            "excellent_quality_percentage": (analysis["quality_distribution"]["excellent"] / total_files) * 100,
            "avg_tests_per_file": analysis["summary"]["total_tests"] / total_files,
            "avg_assertions_per_test": analysis["summary"]["total_assertions"] / max(analysis["summary"]["total_tests"], 1),
            "async_test_percentage": (analysis["summary"]["total_async_tests"] / max(analysis["summary"]["total_tests"], 1)) * 100
        }
    else:
        analysis["quality_metrics"] = {}

    return analysis


def print_analysis_summary(analysis: dict[str, Any]) -> None:
    """Print a human-readable summary of the analysis."""
    print("=" * 60)
    print("AFS FASTAPI TEST SUITE ANALYSIS SUMMARY")
    print("=" * 60)

    if "error" in analysis:
        print(f"❌ Analysis failed: {analysis['error']}")
        return

    summary = analysis["summary"]
    metrics = analysis["quality_metrics"]

    print("\n📊 BASIC METRICS:")
    print(f"   Total test files: {summary['total_test_files']}")
    print(f"   Total tests: {summary['total_tests']}")
    print(f"   Total async tests: {summary['total_async_tests']}")
    print(f"   Total assertions: {summary['total_assertions']}")

    print("\n🎯 QUALITY METRICS:")
    print(f"   Real implementation usage: {metrics.get('real_implementation_percentage', 0):.1f}%")
    print(f"   Mock-heavy files: {metrics.get('mock_heavy_percentage', 0):.1f}%")
    print(f"   Problematic files: {metrics.get('problematic_percentage', 0):.1f}%")
    print(f"   Excellent quality: {metrics.get('excellent_quality_percentage', 0):.1f}%")
    print(f"   Avg tests per file: {metrics.get('avg_tests_per_file', 0):.1f}")
    print(f"   Avg assertions per test: {metrics.get('avg_assertions_per_test', 0):.1f}")
    print(f"   Async test percentage: {metrics.get('async_test_percentage', 0):.1f}%")

    print("\n📈 QUALITY DISTRIBUTION:")
    for quality, count in sorted(analysis["quality_distribution"].items()):
        emoji = {"excellent": "🟢", "good": "🟡", "acceptable": "🟠",
                "mock_heavy": "🔴", "no_real_imports": "🔴", "empty": "⚪", "error": "❌"}.get(quality, "⚫")
        print(f"   {emoji} {quality}: {count} files")

    if analysis["mock_heavy_files"]:
        print("\n⚠️  MOCK-HEAVY FILES:")
        for file_info in analysis["mock_heavy_files"][:5]:  # Show top 5
            print(f"   {file_info['file']}: {file_info['mock_count']} mocks, {file_info['test_count']} tests")
        if len(analysis["mock_heavy_files"]) > 5:
            print(f"   ... and {len(analysis['mock_heavy_files']) - 5} more")

    if analysis["problematic_files"]:
        print("\n❌ PROBLEMATIC FILES:")
        for file_path in analysis["problematic_files"][:5]:  # Show top 5
            print(f"   {file_path}")
        if len(analysis["problematic_files"]) > 5:
            print(f"   ... and {len(analysis['problematic_files']) - 5} more")

    print(f"\n✅ REAL IMPLEMENTATION FILES: {len(analysis['real_implementation_files'])}")
    print("   (Files that import from afs_fastapi)")


def main():
    """Main function to run the test suite analysis."""
    print("Analyzing AFS FastAPI test suite...")
    print("This may take a moment for large test suites...\n")

    analysis = analyze_test_suite()

    # Save detailed analysis to JSON
    output_file = Path("docs/verification/test_suite_analysis.json")
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)

    print(f"✅ Detailed analysis saved to: {output_file}\n")

    # Print summary
    print_analysis_summary(analysis)

    # Return quality assessment
    metrics = analysis.get("quality_metrics", {})
    real_impl_pct = metrics.get("real_implementation_percentage", 0)
    mock_heavy_pct = metrics.get("mock_heavy_percentage", 0)

    print("\n🎉 OVERALL ASSESSMENT:")
    if real_impl_pct >= 80 and mock_heavy_pct <= 20:
        print("   ✅ EXCELLENT: Tests primarily use real implementations")
        return "excellent"
    elif real_impl_pct >= 60 and mock_heavy_pct <= 40:
        print("   🟡 GOOD: Tests mostly use real implementations")
        return "good"
    elif real_impl_pct >= 40:
        print("   🟠 ACCEPTABLE: Mix of real and mocked implementations")
        return "acceptable"
    else:
        print("   🔴 NEEDS IMPROVEMENT: Tests rely heavily on mocks")
        return "needs_improvement"


if __name__ == "__main__":
    overall_quality = main()
    print(f"\nOverall test suite quality: {overall_quality}")