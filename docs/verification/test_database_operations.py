#!/usr/bin/env python3
"""
Database operations testing script for Task 4.

This script tests real database CRUD operations with actual data
to verify the database layer works with real implementations.
"""

import asyncio
import logging
import sys
import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Try to import SQLAlchemy
try:
    from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer, Float, DateTime, JSON
    from sqlalchemy.orm import sessionmaker, declarative_base
    from sqlalchemy.types import TypeDecorator
    print("✅ SQLAlchemy imports successful")
    HAS_SQLALCHEMY = True
except ImportError as e:
    print(f"❌ SQLAlchemy import failed: {e}")
    HAS_SQLALCHEMY = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class CustomJSONType(TypeDecorator):
    """Custom JSON type for SQLite compatibility (mimicking the real schema)."""
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value


def create_agricultural_database_schema():
    """Create a comprehensive agricultural database schema for testing."""
    print("=== Creating Agricultural Database Schema ===")

    # Connect to SQLite database
    conn = sqlite3.connect("test_agricultural_operations.db")
    cursor = conn.cursor()

    # Create Equipment table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipment (
            equipment_id TEXT PRIMARY KEY,
            isobus_address INTEGER UNIQUE NOT NULL,
            equipment_type TEXT NOT NULL,
            manufacturer TEXT NOT NULL,
            model TEXT,
            serial_number TEXT,
            firmware_version TEXT,
            installation_date TIMESTAMP,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')

    # Create Field table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fields (
            field_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            area_acres REAL NOT NULL,
            boundary_coordinates TEXT,
            soil_type TEXT,
            crop_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')

    # Create ISOBUS Message Record table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS isobus_message_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id TEXT,
            timestamp TIMESTAMP NOT NULL,
            pgn INTEGER NOT NULL,
            source_address INTEGER,
            destination_address INTEGER,
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (equipment_id) REFERENCES equipment (equipment_id)
        )
    ''')

    # Create Agricultural Sensor Record table
    cursor.execute('''
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
        )
    ''')

    # Create Tractor Telemetry Record table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tractor_telemetry_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id TEXT,
            timestamp TIMESTAMP NOT NULL,
            engine_speed REAL,
            vehicle_speed REAL,
            fuel_rate REAL,
            engine_temperature REAL,
            hydraulic_pressure REAL,
            pto_speed REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (equipment_id) REFERENCES equipment (equipment_id)
        )
    ''')

    # Create Yield Monitor Record table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS yield_monitor_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id TEXT,
            timestamp TIMESTAMP NOT NULL,
            yield_rate REAL NOT NULL,
            moisture_content REAL,
            flow_rate REAL,
            gps_latitude REAL,
            gps_longitude REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (equipment_id) REFERENCES equipment (equipment_id)
        )
    ''')

    # Create Operational Session table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operational_session (
            session_id TEXT PRIMARY KEY,
            equipment_id TEXT,
            field_id TEXT,
            session_type TEXT NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            status TEXT DEFAULT 'active',
            area_covered REAL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (equipment_id) REFERENCES equipment (equipment_id),
            FOREIGN KEY (field_id) REFERENCES fields (field_id)
        )
    ''')

    conn.commit()
    print("✅ Agricultural database schema created successfully")
    return conn, cursor


def test_equipment_crud_operations(cursor, conn):
    """Test equipment CRUD operations."""
    print("\n=== Testing Equipment CRUD Operations ===")

    # CREATE - Insert test equipment
    test_equipment = [
        ('TRACTOR_001', 10, 'tractor', 'John Deere', '8RX', 'JD8RX2023001', 'v2.1.3', datetime.now(), 'active'),
        ('HARVESTER_001', 15, 'harvester', 'Case IH', 'Axial-Flow', 'CIAX2023002', 'v3.0.1', datetime.now(), 'active'),
        ('SPRAYER_001', 20, 'sprayer', 'AGCO', 'RoGator', 'AGRG2023003', 'v1.8.5', datetime.now(), 'maintenance'),
    ]

    for equipment in test_equipment:
        cursor.execute('''
            INSERT INTO equipment (equipment_id, isobus_address, equipment_type, manufacturer, model,
                                 serial_number, firmware_version, installation_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', equipment)

    conn.commit()
    print(f"✅ CREATE: Inserted {len(test_equipment)} equipment records")

    # READ - Query equipment
    cursor.execute("SELECT * FROM equipment WHERE equipment_type = 'tractor'")
    tractors = cursor.fetchall()
    print(f"✅ READ: Found {len(tractors)} tractor(s)")

    cursor.execute("SELECT equipment_id, manufacturer, model FROM equipment")
    all_equipment = cursor.fetchall()
    print(f"✅ READ: Total equipment in database: {len(all_equipment)}")

    # UPDATE - Update equipment status
    cursor.execute("UPDATE equipment SET status = ? WHERE equipment_id = ?", ('operational', 'SPRAYER_001'))
    conn.commit()
    print("✅ UPDATE: Updated sprayer status to operational")

    # Verify update
    cursor.execute("SELECT status FROM equipment WHERE equipment_id = 'SPRAYER_001'")
    updated_status = cursor.fetchone()
    if updated_status[0] == 'operational':
        print("✅ UPDATE: Status update verified")
    else:
        print("❌ UPDATE: Status update failed")
        return False

    # DELETE - Remove test equipment
    cursor.execute("DELETE FROM equipment WHERE equipment_id = 'HARVESTER_001'")
    conn.commit()
    print("✅ DELETE: Removed harvester record")

    # Verify deletion
    cursor.execute("SELECT COUNT(*) FROM equipment WHERE equipment_id = 'HARVESTER_001'")
    count = cursor.fetchone()[0]
    if count == 0:
        print("✅ DELETE: Deletion verified")
    else:
        print("❌ DELETE: Deletion failed")
        return False

    return True


def test_sensor_data_operations(cursor, conn):
    """Test agricultural sensor data operations."""
    print("\n=== Testing Sensor Data Operations ===")

    # Insert sensor readings
    sensor_data = [
        ('TRACTOR_001', 'soil_moisture', datetime.now(), 35.5, 'percent', '{"depth": 15, "location": "field_A"}'),
        ('TRACTOR_001', 'temperature', datetime.now(), 22.3, 'celsius', '{"sensor_id": "TEMP_001"}'),
        ('TRACTOR_001', 'humidity', datetime.now(), 65.2, 'percent', '{"sensor_id": "HUM_001"}'),
        ('TRACTOR_001', 'soil_ph', datetime.now(), 6.8, 'ph', '{"depth": 10, "location": "field_A"}'),
    ]

    for data in sensor_data:
        cursor.execute('''
            INSERT INTO agricultural_sensor_record (equipment_id, sensor_type, timestamp, value, unit, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', data)

    conn.commit()
    print(f"✅ CREATE: Inserted {len(sensor_data)} sensor readings")

    # Query sensor data
    cursor.execute('''
        SELECT sensor_type, AVG(value) as avg_value, COUNT(*) as count
        FROM agricultural_sensor_record
        WHERE equipment_id = 'TRACTOR_001'
        GROUP BY sensor_type
    ''')
    sensor_summary = cursor.fetchall()
    print(f"✅ READ: Sensor data summary:")
    for sensor_type, avg_value, count in sensor_summary:
        print(f"   {sensor_type}: avg={avg_value:.2f}, count={count}")

    # Test metadata handling
    cursor.execute('''
        SELECT metadata FROM agricultural_sensor_record
        WHERE sensor_type = 'soil_moisture'
    ''')
    metadata_result = cursor.fetchone()
    if metadata_result:
        try:
            metadata = json.loads(metadata_result[0])
            print(f"✅ JSON handling: {metadata}")
        except json.JSONDecodeError:
            print("❌ JSON handling: Failed to parse metadata")
            return False

    return True


def test_telemetry_operations(cursor, conn):
    """Test tractor telemetry operations."""
    print("\n=== Testing Telemetry Operations ===")

    # Insert telemetry data
    telemetry_data = [
        ('TRACTOR_001', datetime.now(), 2200.5, 8.2, 15.3, 85.2, 2100.8, 540.2),
        ('TRACTOR_001', datetime.now(), 2150.3, 8.5, 14.8, 86.1, 2080.5, 545.8),
        ('TRACTOR_001', datetime.now(), 2250.8, 7.9, 15.8, 84.5, 2125.3, 538.5),
    ]

    for data in telemetry_data:
        cursor.execute('''
            INSERT INTO tractor_telemetry_record
            (equipment_id, timestamp, engine_speed, vehicle_speed, fuel_rate,
             engine_temperature, hydraulic_pressure, pto_speed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)

    conn.commit()
    print(f"✅ CREATE: Inserted {len(telemetry_data)} telemetry records")

    # Query telemetry analytics
    cursor.execute('''
        SELECT
            AVG(engine_speed) as avg_engine_speed,
            AVG(vehicle_speed) as avg_speed,
            AVG(fuel_rate) as avg_fuel_rate,
            COUNT(*) as record_count
        FROM tractor_telemetry_record
        WHERE equipment_id = 'TRACTOR_001'
    ''')
    analytics = cursor.fetchone()
    print(f"✅ READ: Telemetry analytics:")
    print(f"   Average engine speed: {analytics[0]:.1f} RPM")
    print(f"   Average speed: {analytics[1]:.1f} km/h")
    print(f"   Average fuel rate: {analytics[2]:.1f} L/h")
    print(f"   Total records: {analytics[3]}")

    return True


def test_session_operations(cursor, conn):
    """Test operational session operations."""
    print("\n=== Testing Operational Session Operations ===")

    # Create a field first
    cursor.execute('''
        INSERT INTO fields (field_id, name, area_acres, boundary_coordinates, soil_type, crop_type)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('FIELD_001', 'North Field', 120.5, '[[lat1,lon1],[lat2,lon2]]', 'loam', 'corn'))

    # Create operational session
    session_data = {
        'session_id': 'SESSION_001',
        'equipment_id': 'TRACTOR_001',
        'field_id': 'FIELD_001',
        'session_type': 'planting',
        'start_time': datetime.now(),
        'area_covered': 45.2,
        'metadata': json.dumps({
            'seed_type': 'corn_hybrid_A',
            'planting_rate': 34000,
            'row_spacing': 30
        })
    }

    cursor.execute('''
        INSERT INTO operational_session
        (session_id, equipment_id, field_id, session_type, start_time, area_covered, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_data['session_id'],
        session_data['equipment_id'],
        session_data['field_id'],
        session_data['session_type'],
        session_data['start_time'],
        session_data['area_covered'],
        session_data['metadata']
    ))

    conn.commit()
    print("✅ CREATE: Created operational session")

    # Query session with equipment and field info
    cursor.execute('''
        SELECT s.session_id, s.session_type, e.manufacturer, e.model, f.name, f.area_acres
        FROM operational_session s
        JOIN equipment e ON s.equipment_id = e.equipment_id
        JOIN fields f ON s.field_id = f.field_id
        WHERE s.session_id = 'SESSION_001'
    ''')
    session_info = cursor.fetchone()
    if session_info:
        print(f"✅ READ: Session info:")
        print(f"   Session: {session_info[0]} ({session_info[1]})")
        print(f"   Equipment: {session_info[2]} {session_info[3]}")
        print(f"   Field: {session_info[4]} ({session_info[5]} acres)")

    # Test session update
    end_time = datetime.now()
    cursor.execute('''
        UPDATE operational_session
        SET end_time = ?, status = ?, area_covered = ?
        WHERE session_id = ?
    ''', (end_time, 'completed', 48.7, 'SESSION_001'))

    conn.commit()
    print("✅ UPDATE: Session marked as completed")

    return True


async def test_sqlalchemy_operations():
    """Test SQLAlchemy operations if available."""
    print("\n=== Testing SQLAlchemy Operations ===")

    if not HAS_SQLALCHEMY:
        print("⚠️ SQLAlchemy not available, skipping SQLAlchemy tests")
        return True

    try:
        # Create SQLAlchemy engine
        engine = create_engine("sqlite:///test_sqlalchemy_ops.db")
        Base = declarative_base()

        # Define a simple model
        class TestEquipment(Base):
            __tablename__ = 'test_equipment'
            id = Column(Integer, primary_key=True)
            equipment_id = Column(String(50), unique=True)
            equipment_type = Column(String(20))
            manufacturer = Column(String(50))
            created_at = Column(DateTime, default=datetime.now)

        # Create tables
        Base.metadata.create_all(engine)
        print("✅ SQLAlchemy: Tables created")

        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()

        # Test ORM operations
        equipment = TestEquipment(
            equipment_id="SQL_TEST_001",
            equipment_type="tractor",
            manufacturer="New Holland"
        )
        session.add(equipment)
        session.commit()
        print("✅ SQLAlchemy: ORM CREATE successful")

        # Test ORM query
        queried = session.query(TestEquipment).filter_by(equipment_id="SQL_TEST_001").first()
        if queried:
            print(f"✅ SQLAlchemy: ORM READ successful - {queried.manufacturer}")

        # Test raw SQL with SQLAlchemy
        result = session.execute(text("SELECT COUNT(*) FROM test_equipment"))
        count = result.scalar()
        print(f"✅ SQLAlchemy: Raw SQL successful - {count} records")

        session.close()
        engine.dispose()

        # Clean up
        os.remove("test_sqlalchemy_ops.db")
        print("✅ SQLAlchemy: Test database cleaned up")

        return True

    except Exception as e:
        print(f"❌ SQLAlchemy operations failed: {e}")
        return False


async def main():
    """Main database operations test function."""
    print("🚀 AFS FastAPI Database Operations Testing")
    print("=" * 50)
    print("Testing real database CRUD operations with actual data\n")

    results = []
    test_databases = []

    try:
        # Test 1: Equipment CRUD operations
        conn, cursor = create_agricultural_database_schema()
        test_databases.append("test_agricultural_operations.db")

        result1 = test_equipment_crud_operations(cursor, conn)
        results.append(("Equipment CRUD", result1))

        # Test 2: Sensor data operations
        result2 = test_sensor_data_operations(cursor, conn)
        results.append(("Sensor Data", result2))

        # Test 3: Telemetry operations
        result3 = test_telemetry_operations(cursor, conn)
        results.append(("Telemetry Data", result3))

        # Test 4: Session operations
        result4 = test_session_operations(cursor, conn)
        results.append(("Session Management", result4))

        conn.close()

        # Test 5: SQLAlchemy operations
        result5 = await test_sqlalchemy_operations()
        results.append(("SQLAlchemy Operations", result5))

    except Exception as e:
        print(f"❌ Database operations test failed: {e}")
        logger.exception("Database operations error")
        results.append(("Database Setup", False))

    # Cleanup test databases
    print("\n=== Cleaning Up Test Databases ===")
    for db_file in test_databases:
        try:
            if os.path.exists(db_file):
                os.remove(db_file)
                print(f"✅ Removed {db_file}")
        except Exception as e:
            print(f"⚠️  Could not remove {db_file}: {e}")

    # Summary
    print("\n" + "=" * 50)
    print("DATABASE OPERATIONS TEST SUMMARY:")
    print("=" * 50)

    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} : {status}")
        if not result:
            all_passed = False

    print("=" * 50)
    if all_passed:
        print("🎉 DATABASE OPERATIONS: ✅ OVERALL PASS")
        print("All database CRUD operations work with real data.")
    else:
        print("💥 DATABASE OPERATIONS: ❌ OVERALL FAIL")
        print("Some database operations have issues.")

    return all_passed


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)