#!/usr/bin/env python3
"""
Database schema verification script for Task 4.

This script verifies that database schemas are real implementations,
not stub definitions, and checks the actual schema structure.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def analyze_schema_file():
    """Analyze the agricultural schemas file for real implementations."""
    print("=== Database Schema Analysis ===")

    schema_file = "afs_fastapi/database/agricultural_schemas.py"

    if not os.path.exists(schema_file):
        print(f"❌ Schema file {schema_file} not found")
        return False

    with open(schema_file) as f:
        content = f.read()

    # Extract class definitions
    lines = content.splitlines()
    classes_found = []
    current_class = None
    class_lines = []
    class_methods = []

    for i, line in enumerate(lines):
        if line.strip().startswith('class ') and '(Base)' in line:
            # Save previous class if exists
            if current_class:
                classes_found.append({
                    'name': current_class,
                    'line': class_start_line,
                    'lines': len(class_lines),
                    'methods': class_methods,
                    'source': '\n'.join(class_lines)
                })

            # Start new class
            current_class = line.split('(')[0].replace('class ', '').strip()
            class_start_line = i + 1
            class_lines = [line]
            class_methods = []

        elif current_class and line.strip().startswith('def '):
            method_name = line.split('(')[0].replace('def ', '').strip()
            class_methods.append(method_name)
            class_lines.append(line)

        elif current_class:
            class_lines.append(line)

    # Add the last class
    if current_class:
        classes_found.append({
            'name': current_class,
            'line': class_start_line,
            'lines': len(class_lines),
            'methods': class_methods,
            'source': '\n'.join(class_lines)
        })

    print(f"Found {len(classes_found)} database model classes:")

    all_classes_real = True
    for cls in classes_found:
        print(f"\n📋 {cls['name']}:")
        print(f"   Line: {cls['line']}, Size: {cls['lines']} lines, Methods: {len(cls['methods'])}")

        # Check if it's a real implementation
        source = cls['source']

        has_tablename = '__tablename__' in source
        has_columns = 'Mapped[' in source or 'Column(' in source
        has_relationships = 'relationship(' in source
        has_imports = any(imp in source for imp in ['from sqlalchemy', 'import sqlalchemy'])
        has_table_config = '__table_args__' in source
        has_indexes = 'Index(' in source

        print(f"   Has table name: {'✅' if has_tablename else '❌'}")
        print(f"   Has columns: {'✅' if has_columns else '❌'}")
        print(f"   Has relationships: {'✅' if has_relationships else '❌'}")
        print(f"   Has table config: {'✅' if has_table_config else '❌'}")
        print(f"   Has indexes: {'✅' if has_indexes else '❌'}")

        # Check for stub indicators
        pass_count = source.count('pass')
        docstring_count = source.count('"""')

        print(f"   Pass statements: {pass_count}")
        print(f"   Docstrings: {docstring_count}")

        # Determine if it's real or stub
        if cls['lines'] < 10:
            print("   ⚠️  Very small class - might be stub")
            all_classes_real = False
        elif pass_count > 3:
            print("   ⚠️  Many pass statements - might be stub")
            all_classes_real = False
        elif not has_tablename:
            print("   ❌ No table name - invalid schema")
            all_classes_real = False
        elif not has_columns:
            print("   ❌ No columns defined - invalid schema")
            all_classes_real = False
        else:
            print("   ✅ Appears to be complete implementation")

        # Count mapped fields/columns
        if 'Mapped[' in source:
            mapped_fields = source.count('Mapped[')
            print(f"   Mapped fields: {mapped_fields}")
        elif 'Column(' in source:
            column_fields = source.count('Column(')
            print(f"   Columns: {column_fields}")

    return all_classes_real


def verify_schema_structure():
    """Verify specific schema structure elements."""
    print("\n=== Schema Structure Verification ===")

    # Expected schema classes based on the actual file
    expected_classes = [
        'Base', 'JSONType', 'Equipment', 'Field', 'ISOBUSMessageRecord',
        'AgriculturalSensorRecord', 'TractorTelemetryRecord',
        'YieldMonitorRecord', 'OperationalSession'
    ]

    schema_file = "afs_fastapi/database/agricultural_schemas.py"
    with open(schema_file) as f:
        content = f.read()

    found_classes = []
    for cls in expected_classes:
        if f'class {cls}(' in content:
            found_classes.append(cls)
            print(f"✅ Found {cls}")
        else:
            print(f"❌ Missing {cls}")

    print(f"\nSchema coverage: {len(found_classes)}/{len(expected_classes)} classes found")

    # Check for important SQLAlchemy features
    sql_alchemy_features = {
        'DeclarativeBase': 'DeclarativeBase' in content,
        'Mapped type': 'Mapped[' in content,
        'Column definitions': 'Column(' in content,
        'Relationships': 'relationship(' in content,
        'Foreign Keys': 'ForeignKey(' in content,
        'Indexes': 'Index(' in content,
        'TypeDecorator': 'TypeDecorator' in content,
        'JSON handling': 'JSONType' in content,
        'DateTime fields': 'DateTime' in content,
        'Table configuration': '__table_args__' in content,
    }

    print("\n🔧 SQLAlchemy Feature Check:")
    for feature, present in sql_alchemy_features.items():
        status = '✅' if present else '❌'
        print(f"   {status} {feature}")

    # Check for agricultural-specific schema elements
    agricultural_elements = {
        'Equipment registry': 'Equipment' in content,
        'Field management': 'Field' in content,
        'ISOBUS messaging': 'ISOBUSMessageRecord' in content,
        'Sensor data': 'AgriculturalSensorRecord' in content,
        'Tractor telemetry': 'TractorTelemetryRecord' in content,
        'Yield monitoring': 'YieldMonitorRecord' in content,
        'Operational sessions': 'OperationalSession' in content,
        'ISOBUS address': 'isobus_address' in content,
        'GNSS data': 'gnss_' in content,
        'PGN handling': 'pgn' in content,
    }

    print("\n🚜 Agricultural Schema Elements:")
    for element, present in agricultural_elements.items():
        status = '✅' if present else '❌'
        print(f"   {status} {element}")

    agricultural_coverage = sum(agricultural_elements.values())
    agricultural_total = len(agricultural_elements)

    print(f"\nAgricultural schema coverage: {agricultural_coverage}/{agricultural_total} elements")

    return len(found_classes) >= 8 and agricultural_coverage >= 8


def test_schema_imports():
    """Test that schema classes can be imported (without using the full module)."""
    print("\n=== Schema Import Test ===")

    # Try to read and parse the schema file
    schema_file = "afs_fastapi/database/agricultural_schemas.py"

    try:
        with open(schema_file) as f:
            content = f.read()

        # Check import statements
        imports = {
            'SQLAlchemy core': 'from sqlalchemy' in content,
            'SQLAlchemy ORM': 'from sqlalchemy.orm' in content,
            'SQLAlchemy types': 'from sqlalchemy import' in content,
            'DateTime handling': 'DateTime' in content,
            'JSON handling': 'json' in content,
            'Type hints': 'from typing' in content,
            'Future annotations': 'from __future__ import annotations' in content,
        }

        print("📦 Import Analysis:")
        all_imports_good = True
        for import_type, present in imports.items():
            status = '✅' if present else '❌'
            print(f"   {status} {import_type}")
            if not present and 'SQLAlchemy' in import_type:
                all_imports_good = False

        # Check for syntax errors by trying to compile
        try:
            compile(content, schema_file, 'exec')
            print("✅ Schema file compiles without syntax errors")
        except SyntaxError as e:
            print(f"❌ Syntax error in schema file: {e}")
            all_imports_good = False

        return all_imports_good

    except Exception as e:
        print(f"❌ Error reading schema file: {e}")
        return False


def count_database_entities():
    """Count actual database entities in the schema."""
    print("\n=== Database Entity Count ===")

    schema_file = "afs_fastapi/database/agricultural_schemas.py"
    with open(schema_file) as f:
        content = f.read()

    # Count different types of database entities
    entity_counts = {
        'Tables': content.count('__tablename__'),
        'Mapped fields': content.count('Mapped['),
        'Column fields': content.count('Column('),
        'Relationships': content.count('relationship('),
        'Foreign keys': content.count('ForeignKey('),
        'Indexes': content.count('Index('),
        'Table configurations': content.count('__table_args__'),
        'Custom types': content.count('TypeDecorator'),
        'JSON fields': content.count('JSONType'),
    }

    print("📊 Database Entity Summary:")
    total_entities = 0
    for entity_type, count in entity_counts.items():
        print(f"   {entity_type}: {count}")
        total_entities += count

    print(f"\nTotal database entities: {total_entities}")

    # Check if we have a substantial database schema
    has_substantial_schema = total_entities > 50
    if has_substantial_schema:
        print("✅ Database schema appears substantial and complete")
    else:
        print("⚠️  Database schema may be minimal")

    return has_substantial_schema


async def main():
    """Main schema verification function."""
    print("🗄️ AFS FastAPI Database Schema Verification")
    print("=" * 50)
    print("Verifying that database schemas are real implementations\n")

    results = []

    # Test 1: Analyze schema file for real implementations
    result1 = analyze_schema_file()
    results.append(("Schema File Analysis", result1))

    # Test 2: Verify schema structure
    result2 = verify_schema_structure()
    results.append(("Schema Structure", result2))

    # Test 3: Test schema imports and syntax
    result3 = test_schema_imports()
    results.append(("Schema Imports", result3))

    # Test 4: Count database entities
    result4 = count_database_entities()
    results.append(("Database Entities", result4))

    # Summary
    print("\n" + "=" * 50)
    print("SCHEMA VERIFICATION SUMMARY:")
    print("=" * 50)

    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} : {status}")
        if not result:
            all_passed = False

    print("=" * 50)
    if all_passed:
        print("🎉 SCHEMA VERIFICATION: ✅ OVERALL PASS")
        print("Database schemas contain real implementations with complete definitions.")
    else:
        print("💥 SCHEMA VERIFICATION: ❌ OVERALL FAIL")
        print("Some database schemas may be incomplete or contain stubs.")

    return all_passed


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)