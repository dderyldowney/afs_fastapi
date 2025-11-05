#!/usr/bin/env python3
"""
Script to analyze PyRight errors and count them by file in target directories.
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


def analyze_target_directories(error_counts):
    """Focus on target directories: core/, database/, monitoring/, services/, utils/"""
    target_dirs = ["core", "database", "monitoring", "services", "utils"]
    target_errors = {}

    for file_path, errors in error_counts.items():
        # Check if file is in one of the target directories
        for target_dir in target_dirs:
            if f"/{target_dir}/" in file_path:
                if target_dir not in target_errors:
                    target_errors[target_dir] = []
                target_errors[target_dir].append((file_path, len(errors)))
                break

    return target_errors


def main():
    # Read the verbose output
    output_file = "pyright_verbose.txt"
    error_counts = extract_pyright_errors(output_file)

    # Analyze target directories
    target_errors = analyze_target_directories(error_counts)

    # Print results
    print("=== PYRIGHT ERROR ANALYSIS FOR TARGET DIRECTORIES ===\n")

    # Sort directories by total error count
    sorted_dirs = sorted(
        target_errors.items(), key=lambda x: sum(count for _, count in x[1]), reverse=True
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
    print("=== FILES WITH HIGHEST INDIVIDUAL ERROR COUNTS ===\n")

    all_files = []
    for files in target_errors.values():
        all_files.extend(files)

    # Sort by error count (highest first)
    all_files_sorted = sorted(all_files, key=lambda x: x[1], reverse=True)

    for file_path, error_count in all_files_sorted[:20]:  # Top 20
        directory = file_path.split("/")[0]
        print(f"{directory.upper()}: {file_path}: {error_count} errors")

    # Summary statistics
    total_files = len(all_files)
    total_errors = sum(count for _, count in all_files)
    print("\n=== SUMMARY ===")
    print(f"Total files with errors in target directories: {total_files}")
    print(f"Total PyRight errors: {total_errors}")
    print(f"Average errors per file: {total_errors / total_files:.1f}")


if __name__ == "__main__":
    main()
