#!/usr/bin/env python3
"""
TodoWrite Validation Tool
Validates YAML plan files against JSON schema
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import jsonschema
import yaml


def load_schema(schema_path: Path) -> dict[str, Any]:
    """Load JSON schema from file."""
    try:
        with open(schema_path) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Schema file not found: {schema_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON schema: {e}")
        sys.exit(1)


def load_yaml_file(yaml_path: Path) -> dict[str, Any]:
    """Load and parse YAML file."""
    try:
        with open(yaml_path) as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ YAML file not found: {yaml_path}")
        return {}
    except yaml.YAMLError as e:
        print(f"❌ Invalid YAML in {yaml_path}: {e}")
        return {}


def validate_yaml_against_schema(
    yaml_data: dict[str, Any], schema: dict[str, Any], file_path: Path
) -> bool:
    """Validate YAML data against JSON schema."""
    try:
        jsonschema.validate(yaml_data, schema)
        print(f"✅ {file_path} - Valid")
        return True
    except jsonschema.ValidationError as e:
        print(f"❌ {file_path} - Validation error:")
        print(f"   {e.message}")
        if e.path:
            print(f"   Path: {' -> '.join(str(p) for p in e.path)}")
        return False
    except jsonschema.SchemaError as e:
        print(f"❌ Schema error: {e}")
        return False


def find_yaml_files(plans_dir: Path) -> list[Path]:
    """Find all YAML files in plans directory."""
    yaml_files = []
    if plans_dir.exists():
        for yaml_file in plans_dir.rglob("*.yaml"):
            yaml_files.append(yaml_file)
        for yml_file in plans_dir.rglob("*.yml"):
            yaml_files.append(yml_file)
    return sorted(yaml_files)


def write_default_schema(schema_path: Path) -> None:
    """Write default TodoWrite schema to file."""
    schema_path.parent.mkdir(parents=True, exist_ok=True)

    # Copy the schema from the schemas directory
    default_schema_path = Path("ToDoWrite/configs/schemas/todowrite.schema.json")
    if default_schema_path.exists():
        with open(default_schema_path) as src:
            schema_content = src.read()
        with open(schema_path, "w") as dst:
            dst.write(schema_content)
        print(f"✅ Schema written to {schema_path}")
    else:
        print(f"❌ Default schema not found at {default_schema_path}")
        sys.exit(1)


def main() -> None:
    """Main validation function."""
    parser = argparse.ArgumentParser(
        description="Validate TodoWrite YAML files against JSON schema"
    )
    parser.add_argument(
        "--plans",
        type=Path,
        default=Path("ToDoWrite/configs/plans"),
        help="Plans directory containing YAML files (default: ToDoWrite/configs/plans)",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("ToDoWrite/configs/schemas/todowrite.schema.json"),
        help="JSON schema file (default: ToDoWrite/configs/schemas/todowrite.schema.json)",
    )
    parser.add_argument(
        "--write-schema", type=Path, help="Write default schema to specified path and exit"
    )

    args = parser.parse_args()

    # Handle schema writing mode
    if args.write_schema:
        write_default_schema(args.write_schema)
        return

    # Load schema
    schema = load_schema(args.schema)

    # Find all YAML files
    yaml_files = find_yaml_files(args.plans)

    if not yaml_files:
        print(f"⚠️  No YAML files found in {args.plans}")
        return

    print(f"🔍 Validating {len(yaml_files)} YAML files...")

    # Validate each file
    valid_files = 0
    for yaml_file in yaml_files:
        yaml_data = load_yaml_file(yaml_file)
        if yaml_data:  # Skip empty files
            if validate_yaml_against_schema(yaml_data, schema, yaml_file):
                valid_files += 1

    # Summary
    total_files = len([f for f in yaml_files if load_yaml_file(f)])
    print("\n📊 Validation Summary:")
    print(f"   Valid: {valid_files}/{total_files}")
    print(f"   Invalid: {total_files - valid_files}/{total_files}")

    if valid_files == total_files:
        print("✅ All files are valid!")
        sys.exit(0)
    else:
        print("❌ Some files failed validation")
        sys.exit(1)


if __name__ == "__main__":
    main()
