#!/usr/bin/env python3
"""
Final comprehensive PyRight error analysis for requested directories.
Focuses on afs_fastapi/core/, afs_fastapi/database/, afs_fastapi/monitoring/, 
afs_fastapi/services/, and utils.py (single file utils).
"""
import re
from collections import defaultdict


def extract_pyright_errors(output_file):
    """Extract PyRight errors from the output file."""
    error_counts = defaultdict(list)

    with open(output_file) as f:
        lines = f.readlines()

    current_file = None
    for line in lines:
        # Check if this is an error line with file path
        file_match = re.search(
            r"/Users/dderyldowney/Documents/GitHub/dderyldowney/afs_fastapi/(.*?):\d+:\d+", line
        )
        if file_match:
            current_file = file_match.group(1)

            # Check if it's an error (not just a warning/info)
            if "error:" in line:
                error_counts[current_file].append(line.strip())

    return error_counts


def analyze_target_directories(error_counts):
    """Focus specifically on the requested directories and files."""
    target_dirs = ["core", "database", "monitoring", "services"]
    target_files = ["utils.py"]
    target_errors = {}

    for file_path, errors in error_counts.items():
        # Check if it's in one of the target directories
        for target_dir in target_dirs:
            if f"/{target_dir}/" in file_path:
                if target_dir not in target_errors:
                    target_errors[target_dir] = []
                target_errors[target_dir].append((file_path, len(errors)))
                break

        # Check if it's one of the target files
        if file_path in target_files:
            if "utils" not in target_errors:
                target_errors["utils"] = []
            target_errors["utils"].append((file_path, len(errors)))

    return target_errors


def create_ranked_report(target_errors):
    """Create a ranked report of files by error count."""
    report = []

    # Add directory summaries
    for directory, files in target_errors.items():
        total_errors = sum(count for _, count in files)
        report.append(
            {
                "category": directory.upper(),
                "total_errors": total_errors,
                "file_count": len(files),
                "files": files,
            }
        )

    # Sort categories by total errors
    report.sort(key=lambda x: x["total_errors"], reverse=True)

    # Add all individual files to the main list
    all_files = []
    for category in report:
        for file_path, error_count in category["files"]:
            all_files.append(
                {
                    "file_path": file_path,
                    "error_count": error_count,
                    "category": category["category"],
                }
            )

    # Sort all files by error count
    all_files.sort(key=lambda x: x["error_count"], reverse=True)

    return report, all_files


def main():
    # Read the verbose output
    output_file = "pyright_verbose.txt"
    error_counts = extract_pyright_errors(output_file)

    # Analyze target directories and files
    target_errors = analyze_target_directories(error_counts)

    # Create ranked report
    report, all_files = create_ranked_report(target_errors)

    # Print final results
    print("=" * 80)
    print("PYRIGHT ERROR ANALYSIS - PRIORITY FIXING ORDER")
    print("=" * 80)
    print("\n📊 RANKED DIRECTORIES BY ERROR COUNT:")
    print("-" * 50)

    for category in report:
        print(
            f"\n{category['category']}: {category['total_errors']} errors ({category['file_count']} files)"
        )
        avg_errors = category["total_errors"] / category["file_count"]
        print(f"  Average: {avg_errors:.1f} errors per file")

        # Show top 3 files in this directory
        category_files = sorted(category["files"], key=lambda x: x[1], reverse=True)[:3]
        for file_path, error_count in category_files:
            print(f"  📁 {file_path}: {error_count} errors")

    print("\n🎯 TOP PRIORITY FILES TO FIX (ranked by error count):")
    print("-" * 50)

    for i, file_info in enumerate(all_files[:15], 1):
        print(f"{i:2d}. [{file_info['category']}] {file_info['file_path']}")
        print(f"    {file_info['error_count']} errors")

        # Show sample error types
        if file_info["error_count"] > 0:
            sample_errors = error_counts[file_info["file_path"]][:2]
            for error in sample_errors:
                error_type = re.search(r"error: (.+)", error)
                if error_type:
                    print(f"    └─ {error_type.group(1)}")

    print("\n📈 SUMMARY STATISTICS:")
    print("-" * 50)
    total_files = len(all_files)
    total_errors = sum(file["error_count"] for file in all_files)
    avg_errors = total_errors / total_files if total_files > 0 else 0

    print(f"Total files in target directories: {total_files}")
    print(f"Total PyRight errors: {total_errors}")
    print(f"Average errors per file: {avg_errors:.1f}")

    # Calculate error type distribution
    all_error_types = []
    for file_info in all_files:
        for error in error_counts[file_info["file_path"]]:
            error_type = re.search(r"error: (.+)", error)
            if error_type:
                all_error_types.append(error_type.group(1))

    error_type_counts = defaultdict(int)
    for error_type in all_error_types:
        error_type_counts[error_type] += 1

    print("\n🔧 TOP ERROR TYPES ACROSS ALL TARGET FILES:")
    print("-" * 50)
    top_error_types = sorted(error_type_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    for error_type, count in top_error_types:
        print(f"{error_type}: {count} occurrences")

    print("\n" + "=" * 80)
    print("RECOMMENDATIONS:")
    print("=" * 80)
    print("1. Start with the top 3 highest-error files:")
    for i, file_info in enumerate(all_files[:3], 1):
        print(f"   {i}. {file_info['file_path']} ({file_info['error_count']} errors)")

    print("\n2. Focus on these common error patterns:")
    for error_type, count in top_error_types[:5]:
        print(f"   • {error_type} ({count} occurrences)")

    print("\n3. Consider addressing entire directory at a time for maximum efficiency:")
    for category in report:
        if category["file_count"] > 3:
            print(f"   • {category['category']} ({category['total_errors']} errors)")


if __name__ == "__main__":
    main()
