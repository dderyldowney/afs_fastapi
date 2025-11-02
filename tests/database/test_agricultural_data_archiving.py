"""
Test agricultural data archiving and retention policies.

This module tests the data lifecycle management for agricultural operations,
including time-based retention policies, archival processes, and storage
optimization for high-frequency ISOBUS and sensor data.

Implementation follows Test-First Development (TDD) RED phase.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from afs_fastapi.database.agricultural_archiving import (
    ArchivalManager,
    ArchivalStatus,
    DataLifecycleStage,
    DataRetentionPolicy,
    RetentionPeriod,
)
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


class TestAgriculturalDataArchiving:
    """Test agricultural data archiving and retention policies."""

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

    @pytest.fixture
    def sample_equipment(self, db_session):
        """Create sample equipment for testing."""
        equipment = Equipment(
            equipment_id="TEST_TRACTOR_ARCHIVE",
            isobus_address=0x70,
            equipment_type="tractor",
            manufacturer="Archive Test",
            status="active",
        )
        db_session.add(equipment)
        db_session.commit()
        return equipment

    def test_data_retention_policy_creation(self) -> None:
        """Test creation of agricultural data retention policies."""
        # RED: Test comprehensive retention policy framework

        # Create retention policy for high-frequency ISOBUS messages
        isobus_policy = DataRetentionPolicy(
            policy_id="ISOBUS_MESSAGES_RETENTION",
            table_name="isobus_messages",
            retention_period=RetentionPeriod.DAYS_30,
            lifecycle_stage=DataLifecycleStage.REAL_TIME,
            compression_enabled=True,
            archive_location="s3://agricultural-archives/isobus/",
            metadata_retention=RetentionPeriod.YEARS_10,
            policy_description="High-frequency CAN bus messages for real-time operations",
        )

        # Test policy properties
        assert isobus_policy.policy_id == "ISOBUS_MESSAGES_RETENTION"
        assert isobus_policy.retention_period == RetentionPeriod.DAYS_30
        assert isobus_policy.lifecycle_stage == DataLifecycleStage.REAL_TIME
        assert isobus_policy.compression_enabled is True
        assert isobus_policy.metadata_retention == RetentionPeriod.YEARS_10

        # Create retention policy for sensor data
        sensor_policy = DataRetentionPolicy(
            policy_id="SENSOR_DATA_RETENTION",
            table_name="agricultural_sensor_data",
            retention_period=RetentionPeriod.YEARS_2,
            lifecycle_stage=DataLifecycleStage.DAILY_AGGREGATION,
            compression_enabled=True,
            archive_location="s3://agricultural-archives/sensors/",
            metadata_retention=RetentionPeriod.YEARS_10,
            policy_description="Agricultural sensor readings with daily aggregations",
        )

        assert sensor_policy.retention_period == RetentionPeriod.YEARS_2
        assert sensor_policy.lifecycle_stage == DataLifecycleStage.DAILY_AGGREGATION

        # Create retention policy for operational sessions (permanent)
        operational_policy = DataRetentionPolicy(
            policy_id="OPERATIONAL_SESSIONS_RETENTION",
            table_name="operational_sessions",
            retention_period=RetentionPeriod.PERMANENT,
            lifecycle_stage=DataLifecycleStage.HISTORICAL_ANALYTICS,
            compression_enabled=False,
            archive_location="s3://agricultural-archives/operations/",
            metadata_retention=RetentionPeriod.PERMANENT,
            policy_description="Critical operational data for compliance and analytics",
        )

        assert operational_policy.retention_period == RetentionPeriod.PERMANENT
        assert operational_policy.lifecycle_stage == DataLifecycleStage.HISTORICAL_ANALYTICS

    def test_retention_period_enumeration(self) -> None:
        """Test retention period enumeration for agricultural compliance."""
        # RED: Test comprehensive retention period options

        # Test real-time data retention periods
        assert RetentionPeriod.DAYS_30.days == 30
        assert RetentionPeriod.DAYS_90.days == 90

        # Test aggregated data retention periods
        assert RetentionPeriod.YEARS_2.days == 730  # 2 * 365
        assert RetentionPeriod.YEARS_5.days == 1825  # 5 * 365
        assert RetentionPeriod.YEARS_10.days == 3650  # 10 * 365

        # Test permanent retention
        assert RetentionPeriod.PERMANENT.days == -1  # Special value for permanent

        # Test data lifecycle stages
        assert DataLifecycleStage.REAL_TIME.value == "real_time"
        assert DataLifecycleStage.DAILY_AGGREGATION.value == "daily_aggregation"
        assert DataLifecycleStage.HISTORICAL_ANALYTICS.value == "historical_analytics"
        assert DataLifecycleStage.ARCHIVED.value == "archived"

    def test_archival_manager_initialization(self, db_session) -> None:
        """Test archival manager initialization and configuration."""
        # RED: Test archival manager setup for agricultural data

        # Create archival manager with agricultural-specific configuration
        archival_manager = ArchivalManager(
            database_session=db_session,
            storage_backend="s3",
            compression_algorithm="gzip",
            encryption_enabled=True,
            batch_size=1000,
            max_archive_workers=4,
            notification_webhook="https://farm-ops.example.com/archival-notifications",
        )

        # Test archival manager properties
        assert archival_manager.storage_backend == "s3"
        assert archival_manager.compression_algorithm == "gzip"
        assert archival_manager.encryption_enabled is True
        assert archival_manager.batch_size == 1000
        assert archival_manager.max_archive_workers == 4

        # Test default retention policies creation
        default_policies = archival_manager.get_default_policies()
        assert len(default_policies) >= 5  # ISOBUS, sensor, telemetry, yield, operational

        # Verify agricultural-specific policies
        policy_names = [policy.policy_id for policy in default_policies]
        assert "ISOBUS_MESSAGES_RETENTION" in policy_names
        assert "SENSOR_DATA_RETENTION" in policy_names
        assert "TELEMETRY_DATA_RETENTION" in policy_names
        assert "YIELD_DATA_RETENTION" in policy_names
        assert "OPERATIONAL_SESSIONS_RETENTION" in policy_names

    def test_expired_data_identification(self, db_session, sample_equipment) -> None:
        """Test identification of expired data for archival."""
        # RED: Test expired data detection with agricultural time-series

        # Create archival manager
        archival_manager = ArchivalManager(database_session=db_session)

        # Create old ISOBUS message records (older than 30 days)
        old_time = datetime.now(UTC) - timedelta(days=35)
        old_messages = []

        for i in range(20):
            message = ISOBUSMessageRecord(
                timestamp=old_time + timedelta(minutes=i),
                equipment_id="TEST_TRACTOR_ARCHIVE",
                pgn=0xE004,
                source_address=0x70,
                destination_address=0xFF,
                data_payload={"test": f"old_data_{i}"},
                priority_level=2,
            )
            old_messages.append(message)

        # Create recent ISOBUS message records (within 30 days)
        recent_time = datetime.now(UTC) - timedelta(days=10)
        recent_messages = []

        for i in range(10):
            message = ISOBUSMessageRecord(
                timestamp=recent_time + timedelta(minutes=i),
                equipment_id="TEST_TRACTOR_ARCHIVE",
                pgn=0xE004,
                source_address=0x70,
                destination_address=0xFF,
                data_payload={"test": f"recent_data_{i}"},
                priority_level=2,
            )
            recent_messages.append(message)

        db_session.add_all(old_messages + recent_messages)
        db_session.commit()

        # Test expired data identification
        retention_policy = DataRetentionPolicy(
            policy_id="TEST_ISOBUS_RETENTION",
            table_name="isobus_messages",
            retention_period=RetentionPeriod.DAYS_30,
            lifecycle_stage=DataLifecycleStage.REAL_TIME,
        )

        expired_data = archival_manager.identify_expired_data(retention_policy)

        # Should identify old messages but not recent ones
        assert len(expired_data) == 20  # All old messages
        assert all(msg.timestamp < datetime.now() - timedelta(days=30) for msg in expired_data)

    def test_data_archival_process(self, db_session, sample_equipment) -> None:
        """Test complete data archival process for agricultural records."""
        # RED: Test end-to-end archival workflow

        # Create archival manager
        archival_manager = ArchivalManager(
            database_session=db_session,
            storage_backend="local",  # Use local for testing
            compression_algorithm="gzip",
        )

        # Create field for sensor data
        field = Field(
            field_id="ARCHIVE_TEST_FIELD",
            field_name="Archive Test Field",
            crop_type="test_crop",
            field_area_hectares=10.0,
        )
        db_session.add(field)
        db_session.commit()

        # Create old sensor data records
        old_time = datetime.now(UTC) - timedelta(days=400)  # Older than 1 year
        old_sensor_records = []

        for i in range(50):
            record = AgriculturalSensorRecord(
                timestamp=old_time + timedelta(hours=i),
                equipment_id="TEST_TRACTOR_ARCHIVE",
                field_id="ARCHIVE_TEST_FIELD",
                sensor_type=SensorType.SOIL_MOISTURE.value,
                sensor_value=45.0 + i * 0.5,
                unit="percent",
                gps_latitude=40.7000 + i * 0.0001,
                gps_longitude=-74.0000 + i * 0.0001,
                quality_indicator="good",
            )
            old_sensor_records.append(record)

        db_session.add_all(old_sensor_records)
        db_session.commit()

        # Create retention policy for sensor data
        sensor_policy = DataRetentionPolicy(
            policy_id="TEST_SENSOR_RETENTION",
            table_name="agricultural_sensor_data",
            retention_period=RetentionPeriod.DAYS_365,  # 1 year
            lifecycle_stage=DataLifecycleStage.DAILY_AGGREGATION,
            compression_enabled=True,
        )

        # Execute archival process
        archival_result = archival_manager.archive_expired_data(sensor_policy)

        # Test archival results
        assert archival_result.status == ArchivalStatus.SUCCESS
        assert archival_result.records_archived == 50
        assert archival_result.compression_ratio > 0.1  # Some compression achieved
        assert archival_result.archive_location is not None

        # Verify records were removed from active database
        remaining_records = (
            db_session.query(AgriculturalSensorRecord)
            .filter(AgriculturalSensorRecord.equipment_id == "TEST_TRACTOR_ARCHIVE")
            .all()
        )

        assert len(remaining_records) == 0  # All old records archived

    def test_storage_statistics_calculation(self, db_session, sample_equipment) -> None:
        """Test storage statistics for agricultural data optimization."""
        # RED: Test comprehensive storage analytics

        # Create archival manager
        archival_manager = ArchivalManager(database_session=db_session)

        # Create various types of agricultural data for statistics
        current_time = datetime.now(UTC)

        # Add telemetry records
        telemetry_records = []
        for i in range(100):
            record = TractorTelemetryRecord(
                timestamp=current_time - timedelta(minutes=i),
                equipment_id="TEST_TRACTOR_ARCHIVE",
                vehicle_speed=10.0 + i * 0.1,
                fuel_level=80.0 - i * 0.1,
                engine_temperature=85.0 + i * 0.05,
                gps_latitude=40.7000,
                gps_longitude=-74.0000,
                operational_mode="testing",
            )
            telemetry_records.append(record)

        db_session.add_all(telemetry_records)
        db_session.commit()

        # Calculate storage statistics
        storage_stats = archival_manager.get_storage_statistics()

        # Test storage statistics structure
        assert "total_records" in storage_stats
        assert "table_statistics" in storage_stats
        assert "retention_policy_compliance" in storage_stats
        assert "estimated_storage_size" in storage_stats
        assert "archival_candidates" in storage_stats

        # Test table-specific statistics
        table_stats = storage_stats["table_statistics"]
        assert "tractor_telemetry" in table_stats
        assert table_stats["tractor_telemetry"]["record_count"] == 100

        # Test archival candidates identification
        candidates = storage_stats["archival_candidates"]
        assert isinstance(candidates, dict)

    def test_compliance_retention_policies(self, db_session) -> None:
        """Test agricultural compliance-specific retention policies."""
        # RED: Test regulatory compliance retention requirements

        # Create equipment and field for compliance testing
        equipment = Equipment(
            equipment_id="COMPLIANCE_TRACTOR",
            isobus_address=0x80,
            equipment_type="tractor",
            manufacturer="Compliance Test",
            status="active",
        )
        field = Field(
            field_id="COMPLIANCE_FIELD",
            field_name="Compliance Field",
            crop_type="regulated_crop",
            field_area_hectares=50.0,
        )
        db_session.add_all([equipment, field])
        db_session.commit()

        # Create safety-critical operational session (must be retained permanently)
        safety_session = OperationalSession(
            session_id="SAFETY_INCIDENT_20251008",
            equipment_id="COMPLIANCE_TRACTOR",
            field_id="COMPLIANCE_FIELD",
            operation_type="emergency_stop",
            start_time=datetime.now(UTC) - timedelta(days=1000),  # Very old
            end_time=datetime.now(UTC) - timedelta(days=1000, hours=1),
            notes="Emergency stop activated - safety incident",
            session_status="completed",
        )

        db_session.add(safety_session)
        db_session.commit()

        # Create archival manager
        archival_manager = ArchivalManager(database_session=db_session)

        # Apply permanent retention policy for safety data
        safety_policy = DataRetentionPolicy(
            policy_id="SAFETY_INCIDENT_RETENTION",
            table_name="operational_sessions",
            retention_period=RetentionPeriod.PERMANENT,
            lifecycle_stage=DataLifecycleStage.HISTORICAL_ANALYTICS,
            policy_description="Safety incidents must be retained permanently for compliance",
        )

        # Test that safety data is never marked for archival
        expired_data = archival_manager.identify_expired_data(safety_policy)
        assert len(expired_data) == 0  # No safety data should be expired

        # Verify compliance categorization
        compliance_check = archival_manager.check_compliance_retention(safety_session)
        assert compliance_check.requires_permanent_retention is True
        assert compliance_check.compliance_category == "safety_critical"
        assert compliance_check.regulatory_basis == "agricultural_safety_regulations"

    def test_archival_recovery_process(self, db_session) -> None:
        """Test recovery of archived agricultural data when needed."""
        # RED: Test data recovery from archival storage

        # Create archival manager
        archival_manager = ArchivalManager(database_session=db_session)

        # Simulate archived data recovery request
        recovery_request = {
            "archive_id": "SENSOR_DATA_2024_Q1",
            "table_name": "agricultural_sensor_data",
            "date_range": {"start": datetime(2024, 1, 1), "end": datetime(2024, 3, 31)},
            "equipment_ids": ["TEST_TRACTOR_ARCHIVE"],
            "sensor_types": [SensorType.SOIL_MOISTURE.value],
            "restore_location": "temporary_restoration_table",
        }

        # Test recovery process
        recovery_result = archival_manager.restore_archived_data(recovery_request)

        # Test recovery result structure
        assert recovery_result.status in [ArchivalStatus.SUCCESS, ArchivalStatus.IN_PROGRESS]
        assert recovery_result.restoration_id is not None
        assert recovery_result.estimated_records > 0
        assert recovery_result.estimated_completion_time is not None

        # Test recovery status monitoring
        status = archival_manager.get_recovery_status(recovery_result.restoration_id)
        assert status.restoration_id == recovery_result.restoration_id
        assert status.progress_percentage >= 0
        assert status.current_stage in ["decompression", "validation", "restoration", "completed"]
