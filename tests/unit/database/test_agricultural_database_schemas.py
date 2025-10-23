"""
Test agricultural database schemas for time-series and relational data.

This module tests the database schema design for agricultural operations,
including time-series data for ISOBUS messages and relational data for
equipment, fields, and operational metadata.

Implementation follows Test-First Development (TDD) RED phase.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from afs_fastapi.database.agricultural_schemas import (
    AgriculturalSensorRecord,
    Equipment,
    Field,
    ISOBUSMessageRecord,
    OperationalSession,
    TractorTelemetryRecord,
    create_agricultural_tables,
)
from afs_fastapi.models.agricultural_sensor_data import SensorType


class TestAgriculturalDatabaseSchemas:
    """Test agricultural database schema design and functionality."""

    @pytest.fixture
    def db_engine(self):
        """Create in-memory SQLite database for testing."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        create_agricultural_tables(engine)
        return engine

    @pytest.fixture
    def db_session(self, db_engine):
        """Create database session for testing."""
        Session = sessionmaker(bind=db_engine)
        session = Session()
        yield session
        session.close()

    def test_equipment_table_creation(self, db_session) -> None:
        """Test equipment table for ISOBUS device registry."""
        # RED: Test equipment registration with ISOBUS compliance

        # Create tractor equipment entry
        tractor = Equipment(
            equipment_id="FIELD_CULTIVATOR_01",
            isobus_address=0x42,
            equipment_type="tractor",
            manufacturer="John Deere",
            model="8R 410",
            serial_number="1RW8R410ABC123456",
            firmware_version="v2.1.3",
            installation_date=datetime(2025, 1, 15),
            status="active",
        )

        # Add to database
        db_session.add(tractor)
        db_session.commit()

        # Test equipment retrieval
        retrieved = (
            db_session.query(Equipment).filter_by(equipment_id="FIELD_CULTIVATOR_01").first()
        )

        assert retrieved is not None
        assert retrieved.isobus_address == 0x42
        assert retrieved.equipment_type == "tractor"
        assert retrieved.manufacturer == "John Deere"
        assert retrieved.status == "active"

    def test_field_table_creation(self, db_session) -> None:
        """Test field boundary and metadata storage."""
        # RED: Test agricultural field management

        # Create field entry with GPS boundaries
        corn_field = Field(
            field_id="NORTH_40_CORN",
            field_name="North 40 Acres - Corn",
            crop_type="corn",
            field_area_hectares=16.19,  # 40 acres
            boundary_coordinates=[
                (40.7128, -74.0060),
                (40.7130, -74.0050),
                (40.7140, -74.0052),
                (40.7138, -74.0062),
            ],
            soil_type="loamy",
            drainage_class="well_drained",
            created_date=datetime(2025, 3, 1),
            last_updated=datetime.now(),
        )

        db_session.add(corn_field)
        db_session.commit()

        # Test field retrieval
        retrieved = db_session.query(Field).filter_by(field_id="NORTH_40_CORN").first()

        assert retrieved is not None
        assert retrieved.crop_type == "corn"
        assert retrieved.field_area_hectares == 16.19
        assert len(retrieved.boundary_coordinates) == 4
        assert retrieved.soil_type == "loamy"

    def test_isobus_message_time_series(self, db_session) -> None:
        """Test time-series storage for ISOBUS messages."""
        # RED: Test high-frequency ISOBUS message storage

        # Create equipment for foreign key
        equipment = Equipment(
            equipment_id="HARVESTER_02",
            isobus_address=0x23,
            equipment_type="combine",
            manufacturer="Case IH",
            status="active",
        )
        db_session.add(equipment)
        db_session.commit()

        # Create time-series ISOBUS message records
        messages = []
        base_time = datetime(2025, 10, 8, 14, 0, 0)

        for i in range(100):  # Simulate 100 high-frequency messages
            message = ISOBUSMessageRecord(
                timestamp=base_time + timedelta(milliseconds=i * 100),
                equipment_id="HARVESTER_02",
                pgn=0xE004,  # Tractor telemetry PGN
                source_address=0x23,
                destination_address=0xFF,
                data_payload={"speed": 12.5 + i * 0.1, "fuel": 78.3 - i * 0.05},
                priority_level=2,  # FIELD_COORDINATION priority
            )
            messages.append(message)

        db_session.add_all(messages)
        db_session.commit()

        # Test time-series query performance
        query_start = base_time + timedelta(seconds=2)
        query_end = base_time + timedelta(seconds=8)

        time_range_messages = (
            db_session.query(ISOBUSMessageRecord)
            .filter(
                ISOBUSMessageRecord.timestamp >= query_start,
                ISOBUSMessageRecord.timestamp <= query_end,
                ISOBUSMessageRecord.equipment_id == "HARVESTER_02",
            )
            .all()
        )

        # Should return messages within the 6-second window
        assert 50 <= len(time_range_messages) <= 70  # Approximate range
        assert all(msg.equipment_id == "HARVESTER_02" for msg in time_range_messages)
        assert all(query_start <= msg.timestamp <= query_end for msg in time_range_messages)

    def test_agricultural_sensor_time_series(self, db_session) -> None:
        """Test time-series storage for agricultural sensor data."""
        # RED: Test sensor data time-series with agricultural analytics

        # Create equipment
        equipment = Equipment(
            equipment_id="FIELD_CULTIVATOR_01",
            isobus_address=0x42,
            equipment_type="tractor",
            manufacturer="John Deere",
            status="active",
        )
        db_session.add(equipment)
        db_session.commit()

        # Create field
        field = Field(
            field_id="SOUTH_FIELD",
            field_name="South Field",
            crop_type="soybeans",
            field_area_hectares=20.0,
        )
        db_session.add(field)
        db_session.commit()

        # Create sensor data records
        base_time = datetime(2025, 10, 8, 10, 0, 0)
        sensor_records = []

        for i in range(50):
            record = AgriculturalSensorRecord(
                timestamp=base_time + timedelta(minutes=i * 5),
                equipment_id="FIELD_CULTIVATOR_01",
                field_id="SOUTH_FIELD",
                sensor_type=SensorType.SOIL_MOISTURE.value,
                sensor_value=45.7 + (i % 10) * 2.1,  # Varying moisture levels
                unit="percent",
                gps_latitude=40.7128 + i * 0.0001,
                gps_longitude=-74.0060 + i * 0.0001,
                quality_indicator="good",
            )
            sensor_records.append(record)

        db_session.add_all(sensor_records)
        db_session.commit()

        # Test agricultural analytics queries
        avg_moisture = (
            db_session.query(text("AVG(sensor_value)"))
            .filter(
                AgriculturalSensorRecord.sensor_type == SensorType.SOIL_MOISTURE.value,
                AgriculturalSensorRecord.field_id == "SOUTH_FIELD",
            )
            .scalar()
        )

        assert 45.0 <= avg_moisture <= 60.0  # Adjusted range for varying moisture levels

    def test_operational_session_tracking(self, db_session) -> None:
        """Test operational session tracking for agricultural analytics."""
        # RED: Test field operation session management

        # Create equipment and field
        equipment = Equipment(
            equipment_id="COMBINE_03",
            isobus_address=0x45,
            equipment_type="combine",
            manufacturer="Claas",
            status="active",
        )
        field = Field(
            field_id="HARVEST_FIELD",
            field_name="Harvest Field",
            crop_type="corn",
            field_area_hectares=25.0,
        )
        db_session.add_all([equipment, field])
        db_session.commit()

        # Create operational session
        harvest_session = OperationalSession(
            session_id="HARVEST_20251008_001",
            equipment_id="COMBINE_03",
            field_id="HARVEST_FIELD",
            operation_type="harvesting",
            start_time=datetime(2025, 10, 8, 8, 0, 0),
            end_time=datetime(2025, 10, 8, 16, 30, 0),
            total_area_covered=24.5,  # hectares
            total_yield=196.0,  # tons
            average_speed=6.2,  # km/h
            fuel_consumed=180.5,  # liters
            operator_id="OPERATOR_001",
            weather_conditions="clear",
            notes="Excellent harvest conditions, high yield",
        )

        db_session.add(harvest_session)
        db_session.commit()

        # Test session analytics
        retrieved_session = (
            db_session.query(OperationalSession)
            .filter_by(session_id="HARVEST_20251008_001")
            .first()
        )

        assert retrieved_session is not None
        assert retrieved_session.operation_type == "harvesting"
        assert retrieved_session.total_yield == 196.0

        # Calculate yield per hectare
        yield_per_hectare = retrieved_session.total_yield / retrieved_session.total_area_covered
        assert 7.5 <= yield_per_hectare <= 8.5  # Reasonable corn yield

    def test_database_relationships(self, db_session) -> None:
        """Test foreign key relationships between tables."""
        # RED: Test relational data integrity

        # Create related records
        equipment = Equipment(
            equipment_id="TEST_TRACTOR",
            isobus_address=0x50,
            equipment_type="tractor",
            manufacturer="New Holland",
            status="active",
        )
        field = Field(
            field_id="TEST_FIELD",
            field_name="Test Field",
            crop_type="wheat",
            field_area_hectares=10.0,
        )
        db_session.add_all([equipment, field])
        db_session.commit()

        # Create operational session with relationships
        session = OperationalSession(
            session_id="TEST_SESSION",
            equipment_id="TEST_TRACTOR",
            field_id="TEST_FIELD",
            operation_type="cultivation",
            start_time=datetime.now(),
            total_area_covered=9.5,
            operator_id="TEST_OPERATOR",
        )
        db_session.add(session)
        db_session.commit()

        # Test relationship queries
        session_with_equipment = (
            db_session.query(OperationalSession)
            .join(Equipment)
            .filter(Equipment.manufacturer == "New Holland")
            .first()
        )

        assert session_with_equipment is not None
        assert session_with_equipment.equipment_id == "TEST_TRACTOR"

        session_with_field = (
            db_session.query(OperationalSession)
            .join(Field)
            .filter(Field.crop_type == "wheat")
            .first()
        )

        assert session_with_field is not None
        assert session_with_field.field_id == "TEST_FIELD"

    def test_time_series_indexing_performance(self, db_session) -> None:
        """Test time-series query performance with indexing."""
        # RED: Test database performance for high-frequency agricultural data

        # This test validates that our time-series schema design
        # supports efficient querying of large agricultural datasets

        # Create equipment
        equipment = Equipment(
            equipment_id="PERF_TEST_TRACTOR",
            isobus_address=0x60,
            equipment_type="tractor",
            manufacturer="Performance Test",
            status="active",
        )
        db_session.add(equipment)
        db_session.commit()

        # Create large dataset simulation
        base_time = datetime(2025, 10, 8, 6, 0, 0)
        records = []

        # Simulate 1000 records over 8 hours (realistic field operation)
        for i in range(1000):
            record = TractorTelemetryRecord(
                timestamp=base_time + timedelta(seconds=i * 28.8),  # ~29 second intervals
                equipment_id="PERF_TEST_TRACTOR",
                vehicle_speed=8.5 + (i % 20) * 0.3,
                fuel_level=95.0 - (i * 0.02),
                engine_temperature=82.0 + (i % 15) * 1.2,
                gps_latitude=40.7200 + i * 0.00001,
                gps_longitude=-74.0100 + i * 0.00001,
                operational_mode="cultivation",
            )
            records.append(record)

        db_session.add_all(records)
        db_session.commit()

        # Test time-range query performance
        start_query = base_time + timedelta(hours=2)
        end_query = base_time + timedelta(hours=6)

        time_range_records = (
            db_session.query(TractorTelemetryRecord)
            .filter(
                TractorTelemetryRecord.timestamp >= start_query,
                TractorTelemetryRecord.timestamp <= end_query,
                TractorTelemetryRecord.equipment_id == "PERF_TEST_TRACTOR",
            )
            .all()
        )

        # Should efficiently retrieve records within 4-hour window (approximately 500 records)
        assert 400 <= len(time_range_records) <= 600

        # Test aggregation query performance
        avg_speed = (
            db_session.query(text("AVG(vehicle_speed)"))
            .filter(
                TractorTelemetryRecord.equipment_id == "PERF_TEST_TRACTOR",
                TractorTelemetryRecord.timestamp >= start_query,
                TractorTelemetryRecord.timestamp <= end_query,
            )
            .scalar()
        )

        assert 8.0 <= avg_speed <= 14.0  # Reasonable speed range
