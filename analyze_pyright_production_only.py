#!/usr/bin/env python3
"""
Script to analyze PyRight errors in production files only (excluding tests).
"""
import re
from collections import defaultdict


def extract_pyright_errors(output_file):
    """Extract PyRight errors from the output file."""
    error_counts = defaultdict(list)
    error_pattern = (
        r"/Users/dderyldowney/Documents/GitHub/dderyldowney/afs_fastapi/(.*?):\d+:\d+.*?error:"
    )

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


def filter_production_files(error_counts):
    """Filter out test files, keep only production files."""
    production_files = {}

    for file_path, errors in error_counts.items():
        # Skip test files
        if "/tests/" in file_path or file_path.startswith("tests/"):
            continue

        # Focus on target directories
        target_dirs = ["core", "database", "monitoring", "services", "utils"]
        for target_dir in target_dirs:
            if f"/{target_dir}/" in file_path:
                if target_dir not in production_files:
                    production_files[target_dir] = []
                production_files[target_dir].append((file_path, len(errors)))
                break

    return production_files


def main():
    # Read the verbose output
    output_file = "pyright_verbose.txt"
    error_counts = extract_pyright_errors(output_file)

    # Filter production files only
    production_errors = filter_production_files(error_counts)

    # Print results
    print("=== PYRIGHT ERROR ANALYSIS - PRODUCTION FILES ONLY ===\n")

    # Sort directories by total error count
    sorted_dirs = sorted(
        production_errors.items(), key=lambda x: sum(count for _, count in x[1]), reverse=True
    )

    for directory, files in sorted_dirs:
        total_errors = sum(count for _, count in files)
        print(f"{directory.upper()}: {total_errors} total errors")

        # Sort files by error count (highest first)
        sorted_files = sorted(files, key=lambda x: x[1], reverse=True)

        for file_path, error_count in sorted_files:
            print(f"  ├── {file_path}: {error_count} errors")
            # Show first few error types as examples
            if error_count > 0:
                first_few = error_counts[file_path][:2]
                for error in first_few:
                    # Extract just the error type
                    error_type = re.search(r"error: (.+)", error)
                    if error_type:
                        print(f"  │   └─ {error_type.group(1)}")
                if len(first_few) < len(error_counts[file_path]):
                    print(f"  │   └─ ... and {len(error_counts[file_path]) - len(first_few)} more")

        print()

    # Also show files with highest individual error counts
    print("=== TOP PRODUCTION FILES BY ERROR COUNT ===\n")

    all_files = []
    for files in production_errors.values():
        all_files.extend(files)

    # Sort by error count (highest first)
    all_files_sorted = sorted(all_files, key=lambda x: x[1], reverse=True)

    for file_path, error_count in all_files_sorted[:15]:  # Top 15
        directory = file_path.split("/")[0]
        print(f"{directory.upper()}: {file_path}: {error_count} errors")

    # Summary statistics
    total_files = len(all_files)
    total_errors = sum(count for _, count in all_files)
    print("\n=== SUMMARY ===")
    print(f"Total production files with errors: {total_files}")
    print(f"Total PyRight errors in production files: {total_errors}")
    print(f"Average errors per production file: {total_errors / total_files:.1f}")

    # Error type breakdown
    print("\n=== TOP ERROR TYPES ACROSS ALL PRODUCTION FILES ===")
    all_error_types = []
    for file_path, errors in error_counts.items():
        if "/tests/" not in file_path and not file_path.startswith("tests/"):
            for error in errors:
                error_type = re.search(r"error: (.+)", error)
                if error_type:
                    all_error_types.append(error_type.group(1))

    # Count and show top error types
    error_type_counts = defaultdict(int)
    for error_type in all_error_types:
        error_type_counts[error_type] += 1

    top_error_types = sorted(error_type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    for error_type, count in top_error_types:
        print(f"{error_type}: {count} occurrences")


if __name__ == "__main__":
    main()
