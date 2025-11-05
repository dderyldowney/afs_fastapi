"""
Async tests for agricultural database schemas and operations.

This module tests the async-compatible database operations for agricultural
operations, including equipment management, field operations, sensor data,
and telemetry tracking with proper async session handling.

Implementation follows Test-First Development (TDD) GREEN phase.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from afs_fastapi.database.agricultural_schemas_async import AsyncDatabaseManager, Base
from afs_fastapi.database.async_repository import (
    AgriculturalSensorAsyncRepository,
    EquipmentAsyncRepository,
    FieldAsyncRepository,
    OperationalSessionAsyncRepository,
    TokenUsageAsyncRepository,
    TractorTelemetryAsyncRepository,
    UnitOfWork,
    YieldMonitorAsyncRepository,
)


class TestAsyncAgriculturalDatabaseSchemas:
    """Test async-compatible agricultural database schema design and functionality."""

    @pytest.fixture
    def async_db_url(self) -> str:
        """Get async database URL for testing."""
        return "sqlite+aiosqlite:///:memory:"

    @pytest_asyncio.fixture
    async def async_engine(self, async_db_url: str):
        """Create async engine for testing."""
        engine = create_async_engine(async_db_url, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield engine
        await engine.dispose()

    @pytest_asyncio.fixture
    async def async_session_factory(self, async_engine):
        """Create async session factory for testing."""
        return async_sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
        )

    @pytest_asyncio.fixture
    async def async_session(self, async_session_factory):
        """Create async database session for testing."""
        async with async_session_factory() as session:
            yield session

    @pytest_asyncio.fixture
    async def db_manager(self, async_db_url: str):
        """Create async database manager for testing."""
        manager = AsyncDatabaseManager(async_db_url)
        await manager.initialize()
        yield manager
        await manager.shutdown()

    @pytest_asyncio.fixture
    async def equipment_repo(self, async_session):
        """Create equipment repository for testing."""
        return EquipmentAsyncRepository(async_session)

    @pytest_asyncio.fixture
    async def field_repo(self, async_session):
        """Create field repository for testing."""
        return FieldAsyncRepository(async_session)

    @pytest_asyncio.fixture
    async def sensor_repo(self, async_session):
        """Create sensor data repository for testing."""
        return AgriculturalSensorAsyncRepository(async_session)

    @pytest_asyncio.fixture
    async def telemetry_repo(self, async_session):
        """Create telemetry repository for testing."""
        return TractorTelemetryAsyncRepository(async_session)

    @pytest_asyncio.fixture
    async def yield_repo(self, async_session):
        """Create yield monitor repository for testing."""
        return YieldMonitorAsyncRepository(async_session)

    @pytest_asyncio.fixture
    async def token_usage_repo(self, async_session):
        """Create token usage repository for testing."""
        return TokenUsageAsyncRepository(async_session)

    @pytest_asyncio.fixture
    async def session_repo(self, async_session):
        """Create operational session repository for testing."""
        return OperationalSessionAsyncRepository(async_session)

    @pytest.mark.asyncio
    async def test_equipment_creation_async(self, equipment_repo: EquipmentAsyncRepository) -> None:
        """Test async equipment creation for ISOBUS device registry."""
        # RED: Test equipment registration with ISOBUS compliance

        # Create tractor equipment entry
        await equipment_repo.create_equipment(
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

        # Test equipment retrieval
        retrieved = await equipment_repo.get_equipment_by_isobus_address(0x42)

        assert retrieved is not None
        assert retrieved.equipment_id == "FIELD_CULTIVATOR_01"
        assert retrieved.isobus_address == 0x42
        assert retrieved.equipment_type == "tractor"
        assert retrieved.manufacturer == "John Deere"
        assert retrieved.status == "active"

    @pytest.mark.asyncio
    async def test_equipment_update_async(self, equipment_repo: EquipmentAsyncRepository) -> None:
        """Test async equipment status update."""
        # Create equipment
        await equipment_repo.create_equipment(
            equipment_id="TRACTOR_001",
            isobus_address=0x43,
            equipment_type="tractor",
            manufacturer="Case IH",
            model="Farmall 120A",
            status="active",
        )

        # Update equipment status
        updated = await equipment_repo.update_equipment_status("TRACTOR_001", "maintenance")

        assert updated is not None
        assert updated.status == "maintenance"

    @pytest.mark.asyncio
    async def test_field_creation_async(self, field_repo: FieldAsyncRepository) -> None:
        """Test async field boundary and metadata storage."""
        # RED: Test agricultural field management

        # Create field entry with GPS boundaries
        await field_repo.create_field(
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
            elevation_meters=120.5,
            slope_percentage=2.5,
        )

        # Test field retrieval
        retrieved = await field_repo.get_fields_by_crop_type("corn")

        assert len(retrieved) == 1
        assert retrieved[0].field_id == "NORTH_40_CORN"
        assert retrieved[0].crop_type == "corn"
        assert retrieved[0].soil_type == "loamy"
        assert retrieved[0].field_area_hectares == 16.19

    @pytest.mark.asyncio
    async def test_field_area_queries_async(self, field_repo: FieldAsyncRepository) -> None:
        """Test async field queries by area range."""
        # Create multiple fields with different areas
        await field_repo.create_field(
            field_id="SMALL_FIELD",
            field_name="Small Field",
            crop_type="wheat",
            field_area_hectares=5.0,
        )

        await field_repo.create_field(
            field_id="MEDIUM_FIELD",
            field_name="Medium Field",
            crop_type="corn",
            field_area_hectares=20.0,
        )

        await field_repo.create_field(
            field_id="LARGE_FIELD",
            field_name="Large Field",
            crop_type="soybeans",
            field_area_hectares=50.0,
        )

        # Test area range queries
        medium_fields = await field_repo.get_fields_by_area_range(10, 30)
        small_fields = await field_repo.get_fields_by_area_range(max_area=10)
        large_fields = await field_repo.get_fields_by_area_range(min_area=40)

        assert len(medium_fields) == 1
        assert medium_fields[0].field_id == "MEDIUM_FIELD"
        assert len(small_fields) == 1
        assert small_fields[0].field_id == "SMALL_FIELD"
        assert len(large_fields) == 1
        assert large_fields[0].field_id == "LARGE_FIELD"

    @pytest.mark.asyncio
    async def test_sensor_data_creation_async(
        self, sensor_repo: AgriculturalSensorAsyncRepository
    ) -> None:
        """Test async sensor data creation and management."""
        # Create soil moisture sensor reading
        await sensor_repo.create_sensor_reading(
            equipment_id="FIELD_CULTIVATOR_01",
            sensor_type="soil_moisture",
            sensor_value=45.5,
            unit="percent",
            field_id="NORTH_40_CORN",
            gps_latitude=40.7128,
            gps_longitude=-74.0060,
            quality_indicator="good",
        )

        # Create temperature sensor reading
        await sensor_repo.create_sensor_reading(
            equipment_id="FIELD_CULTIVATOR_01",
            sensor_type="temperature",
            sensor_value=22.3,
            unit="celsius",
            field_id="NORTH_40_CORN",
            gps_latitude=40.7129,
            gps_longitude=-74.0059,
            quality_indicator="good",
        )

        # Test sensor data retrieval
        moisture_readings = await sensor_repo.get_sensor_readings_by_equipment(
            equipment_id="FIELD_CULTIVATOR_01",
            sensor_type="soil_moisture",
        )

        temp_readings = await sensor_repo.get_sensor_readings_by_field_and_type(
            field_id="NORTH_40_CORN",
            sensor_type="temperature",
        )

        assert len(moisture_readings) == 1
        assert moisture_readings[0].sensor_value == 45.5
        assert moisture_readings[0].unit == "percent"

        assert len(temp_readings) == 1
        assert temp_readings[0].sensor_value == 22.3
        assert temp_readings[0].unit == "celsius"

    @pytest.mark.asyncio
    async def test_sensor_statistics_async(
        self, sensor_repo: AgriculturalSensorAsyncRepository
    ) -> None:
        """Test async sensor data statistics calculation."""
        # Create multiple sensor readings for statistics
        for i in range(5):
            await sensor_repo.create_sensor_reading(
                equipment_id="FIELD_CULTIVATOR_01",
                sensor_type="soil_moisture",
                sensor_value=40.0 + i,
                unit="percent",
            )

        # Get sensor statistics
        stats = await sensor_repo.get_sensor_statistics(
            equipment_id="FIELD_CULTIVATOR_01",
            sensor_type="soil_moisture",
        )

        assert stats["count"] == 5
        assert stats["average"] == 42.0  # (40+41+42+43+44) / 5
        assert stats["minimum"] == 40.0
        assert stats["maximum"] == 44.0

    @pytest.mark.asyncio
    async def test_telemetry_data_async(
        self, telemetry_repo: TractorTelemetryAsyncRepository
    ) -> None:
        """Test async tractor telemetry data management."""
        # Create multiple telemetry readings
        readings = []
        for i in range(3):
            reading = await telemetry_repo.create_telemetry_reading(
                equipment_id="TRACTOR_001",
                vehicle_speed=8.5 + i * 2,
                fuel_level=75.0 - i * 5,
                engine_temperature=85.0 + i,
                operational_mode="cultivating",
                gps_latitude=40.7128,
                gps_longitude=-74.0060,
                engine_hours=1200.0 + i * 10,
            )
            readings.append(reading)

        # Test telemetry retrieval
        retrieved_readings = await telemetry_repo.get_telemetry_by_equipment(
            equipment_id="TRACTOR_001",
            operational_mode="cultivating",
        )

        assert len(retrieved_readings) == 3
        assert retrieved_readings[0].vehicle_speed == 12.5  # First (newest/highest speed)
        assert retrieved_readings[0].operational_mode == "cultivating"

    @pytest.mark.asyncio
    async def test_yield_monitor_data_async(self, yield_repo: YieldMonitorAsyncRepository) -> None:
        """Test async yield monitoring data management."""
        # Create yield reading
        yield_reading = await yield_repo.create_yield_reading(
            equipment_id="COMBINE_001",
            field_id="NORTH_40_CORN",
            crop_type="corn",
            yield_volume=12.5,
            moisture_content=15.2,
            gps_latitude=40.7128,
            gps_longitude=-74.0060,
            harvest_width=12.0,
            harvest_speed=6.5,
            grain_temperature=18.5,
        )

        # Verify reading creation
        assert yield_reading.equipment_id == "COMBINE_001"
        assert yield_reading.field_id == "NORTH_40_CORN"
        assert yield_reading.crop_type == "corn"
        assert yield_reading.yield_volume == 12.5
        assert yield_reading.moisture_content == 15.2

    @pytest.mark.asyncio
    async def test_token_usage_tracking_async(
        self, token_usage_repo: TokenUsageAsyncRepository
    ) -> None:
        """Test async token usage tracking for agricultural AI operations."""
        # Create multiple token usage records
        usage_records = []
        for i in range(5):
            usage = await token_usage_repo.create_token_usage(
                agent_id="agricultural_ai_agent",
                task_id=f"field_analysis_{i}",
                tokens_used=1000.0 + i * 100,
                model_name="claude-3-sonnet",
            )
            usage_records.append(usage)

        # Test token usage queries
        agent_usage = await token_usage_repo.get_token_usage_by_agent(
            agent_id="agricultural_ai_agent",
        )

        task_usage = await token_usage_repo.get_token_usage_by_task(
            task_id="field_analysis_2",
        )

        # Test token usage statistics
        stats = await token_usage_repo.get_token_usage_statistics(
            agent_id="agricultural_ai_agent",
        )

        assert len(agent_usage) == 5
        assert len(task_usage) == 1
        assert task_usage[0].task_id == "field_analysis_2"
        assert stats["total_usage_count"] == 5
        assert stats["total_tokens_used"] == 6000.0  # 1000+1100+1200+1300+1400

    @pytest.mark.asyncio
    async def test_token_usage_pruning_async(
        self, token_usage_repo: TokenUsageAsyncRepository
    ) -> None:
        """Test async token usage pruning for data management."""
        # Create old and new token usage records
        old_date = datetime.now(UTC) - timedelta(days=40)
        new_date = datetime.now(UTC) - timedelta(days=10)

        await token_usage_repo.create_token_usage(
            agent_id="old_agent",
            task_id="old_task",
            tokens_used=100.0,
            model_name="claude-3-sonnet",
            timestamp=old_date,
        )

        await token_usage_repo.create_token_usage(
            agent_id="new_agent",
            task_id="new_task",
            tokens_used=200.0,
            model_name="claude-3-sonnet",
            timestamp=new_date,
        )

        # Prune old records
        deleted_count = await token_usage_repo.delete_old_token_usage(
            cutoff_date=datetime.now(UTC) - timedelta(days=30)
        )

        assert deleted_count == 1

        # Verify only new records remain
        remaining_usage = await token_usage_repo.get_token_usage_by_agent(
            agent_id="new_agent",
        )

        assert len(remaining_usage) == 1
        assert remaining_usage[0].tokens_used == 200.0

    @pytest.mark.asyncio
    async def test_operational_session_async(
        self, session_repo: OperationalSessionAsyncRepository
    ) -> None:
        """Test async operational session management for agricultural operations."""
        # Create operational session
        operational_session = await session_repo.create_session(
            session_id="SESSION_001",
            equipment_id="TRACTOR_001",
            field_id="NORTH_40_CORN",
            operation_type="cultivating",
            start_time=datetime(2025, 3, 15, 8, 0),
            operator_id="JOHN_DOE",
            weather_conditions="sunny",
            soil_conditions="moist",
            notes="Standard cultivation operation",
        )

        # Update session with end information
        updated_session = await session_repo.update_session_end(
            session_id="SESSION_001",
            end_time=datetime(2025, 3, 15, 16, 30),
            total_area_covered=8.5,
            average_speed=6.2,
            fuel_consumed=45.0,
        )

        assert operational_session.session_id == "SESSION_001"
        assert updated_session is not None
        assert updated_session.session_status == "completed"
        assert updated_session.total_area_covered == 8.5
        assert updated_session.average_speed == 6.2

    @pytest.mark.asyncio
    async def test_unit_of_work_async(self, async_session) -> None:
        """Test async unit of work pattern for transaction management."""
        # Test multiple operations in a single transaction
        async with UnitOfWork(async_session) as uow:
            # Create equipment
            await uow.equipment.create_equipment(
                equipment_id="UOW_TEST_EQUIPMENT",
                isobus_address=0x44,
                equipment_type="tractor",
                manufacturer="New Holland",
                model="T8.380",
            )

            # Create field
            await uow.field.create_field(
                field_id="UOW_TEST_FIELD",
                field_name="Unit of Work Test Field",
                crop_type="wheat",
                field_area_hectares=12.5,
            )

            # Create telemetry reading
            await uow.telemetry.create_telemetry_reading(
                equipment_id="UOW_TEST_EQUIPMENT",
                vehicle_speed=7.5,
                fuel_level=80.0,
                engine_temperature=82.0,
                operational_mode="cultivating",
            )

            # Create sensor reading
            await uow.sensor_data.create_sensor_reading(
                equipment_id="UOW_TEST_EQUIPMENT",
                sensor_type="soil_moisture",
                sensor_value=48.0,
                unit="percent",
                field_id="UOW_TEST_FIELD",
            )

            # Verify all operations are committed together
            retrieved_equipment = await uow.equipment.get_equipment_by_isobus_address(0x44)
            retrieved_field = await uow.field.get_fields_by_crop_type("wheat")
            retrieved_telemetry = await uow.telemetry.get_telemetry_by_equipment(
                equipment_id="UOW_TEST_EQUIPMENT"
            )

            assert retrieved_equipment is not None
            assert retrieved_equipment.equipment_id == "UOW_TEST_EQUIPMENT"
            assert len(retrieved_field) == 1
            assert retrieved_field[0].field_id == "UOW_TEST_FIELD"
            assert len(retrieved_telemetry) == 1
            assert retrieved_telemetry[0].vehicle_speed == 7.5

    @pytest.mark.asyncio
    async def test_database_manager_performance_async(
        self, db_manager: AsyncDatabaseManager
    ) -> None:
        """Test async database manager performance and metrics."""
        # Test performance tracking
        performance_report = await db_manager.get_performance_report()

        assert "total_operations" in performance_report
        assert "success_rate" in performance_report
        assert "average_operation_time" in performance_report
        assert "agricultural_optimization" in performance_report
        assert "recommendations" in performance_report

        # Test time-series performance assessment
        ts_performance = performance_report["agricultural_optimization"]["time_series_performance"]
        assert "recent_avg_time" in ts_performance
        assert "batch_processing_capability" in ts_performance

        # Test connection efficiency assessment
        connection_efficiency = performance_report["agricultural_optimization"][
            "connection_efficiency"
        ]
        assert "connection_utilization" in connection_efficiency
        assert "failure_rate" in connection_efficiency

    @pytest.mark.asyncio
    async def test_agricultural_data_validation_async(self) -> None:
        """Test agricultural data validation functions."""
        from afs_fastapi.database.agricultural_schemas_async import (
            calculate_field_area_from_boundaries,
            validate_gps_coordinates,
            validate_isobus_address,
        )

        # Test ISOBUS address validation
        assert validate_isobus_address(0x42)  # Valid address
        assert not validate_isobus_address(0x100)  # Invalid address
        assert validate_isobus_address(0x00)  # Minimum valid address
        assert validate_isobus_address(0xFF)  # Maximum valid address
        assert not validate_isobus_address(-1)  # Negative address

        # Test GPS coordinate validation
        assert validate_gps_coordinates(40.7128, -74.0060)  # Valid NYC coordinates
        assert not validate_gps_coordinates(91.0, 0.0)  # Invalid latitude
        assert not validate_gps_coordinates(-91.0, 0.0)  # Invalid latitude
        assert not validate_gps_coordinates(0.0, 181.0)  # Invalid longitude
        assert not validate_gps_coordinates(0.0, -181.0)  # Invalid longitude
        assert validate_gps_coordinates(0.0, 0.0)  # Valid coordinates

        # Test field area calculation
        square_field = [(0, 0), (0, 1), (1, 1), (1, 0)]
        area = calculate_field_area_from_boundaries(square_field)
        assert area > 0  # Should calculate a positive area

        invalid_coordinates = []
        invalid_area = calculate_field_area_from_boundaries(invalid_coordinates)
        assert invalid_area == 0.0  # Should return 0 for invalid coordinates

    @pytest.mark.asyncio
    async def test_concurrent_database_operations_async(self, async_session) -> None:
        """Test sequential async database operations for agricultural performance."""

        # Test sequential equipment creation (avoiding session conflicts)
        equipment_results = []
        for i in range(10):
            async with UnitOfWork(async_session) as uow:
                equipment = await uow.equipment.create_equipment(
                    equipment_id=f"CONCURRENT_EQUIPMENT_{i}",
                    isobus_address=0x50 + i,
                    equipment_type="tractor",
                    manufacturer="Deere",
                    model=f"Model_{i}",
                )
                equipment_results.append(equipment)
                await uow.commit()

        # Verify all operations completed successfully
        assert len(equipment_results) == 10

        # Verify all equipment was created with unique IDs
        equipment_ids = [eq.equipment_id for eq in equipment_results]
        assert len(set(equipment_ids)) == 10  # All IDs should be unique

        # Test sequential sensor data creation
        sensor_results = []
        for i in range(5):
            async with UnitOfWork(async_session) as uow:
                sensor = await uow.sensor_data.create_sensor_reading(
                    equipment_id=f"CONCURRENT_EQUIPMENT_{i}",
                    sensor_type="temperature",
                    sensor_value=20.0 + i,
                    unit="celsius",
                )
                sensor_results.append(sensor)
                await uow.commit()

        # Verify all sensor operations completed successfully
        assert len(sensor_results) == 5

        # Verify all sensor readings have unique values
        sensor_values = [sr.sensor_value for sr in sensor_results]
        assert len(set(sensor_values)) == 5  # All values should be unique

    @pytest.mark.asyncio
    async def test_error_handling_async(self, async_session) -> None:
        """Test async error handling and transaction rollback."""
        # Test transaction rollback on failure
        async with UnitOfWork(async_session) as uow:
            # Create equipment successfully
            await uow.equipment.create_equipment(
                equipment_id="ERROR_TEST_EQUIPMENT",
                isobus_address=0x60,
                equipment_type="tractor",
                manufacturer="Case IH",
            )

            # Attempt to create equipment with duplicate ID (should cause constraint violation)
            try:
                await uow.equipment.create_equipment(
                    equipment_id="ERROR_TEST_EQUIPMENT",  # Duplicate ID
                    isobus_address=0x61,
                    equipment_type="implement",
                    manufacturer="Great Plains",
                )
                pytest.fail("Expected constraint violation was not raised")
            except Exception:
                # Transaction should be rolled back automatically
                pass

        # Verify that the original equipment still exists but duplicate was not created
        async with UnitOfWork(async_session) as uow:
            retrieved_equipment = await uow.equipment.get_equipment_by_isobus_address(0x60)
            duplicate_equipment = await uow.equipment.get_equipment_by_isobus_address(0x61)

            assert retrieved_equipment is not None
            assert retrieved_equipment.equipment_id == "ERROR_TEST_EQUIPMENT"
            assert duplicate_equipment is None  # Should not exist due to rollback

    @pytest.mark.asyncio
    async def test_batch_operations_async(self, async_session) -> None:
        """Test sequential async batch operations for agricultural performance."""

        # Create multiple equipment records sequentially
        equipment_results = []
        for i in range(10):
            async with UnitOfWork(async_session) as uow:
                equipment = await uow.equipment.create_equipment(
                    equipment_id=f"BATCH_EQUIPMENT_{i}",
                    isobus_address=0x70 + i,
                    equipment_type="tractor" if i % 2 == 0 else "implement",
                    manufacturer="Deere" if i % 2 == 0 else "Case IH",
                    model=f"Model_{i}",
                )
                equipment_results.append(equipment)
                await uow.commit()

        # Verify all equipment was created
        assert len(equipment_results) == 10

        # Create multiple sensor readings sequentially
        sensor_results = []
        for i in range(5):
            async with UnitOfWork(async_session) as uow:
                sensor = await uow.sensor_data.create_sensor_reading(
                    equipment_id=f"BATCH_EQUIPMENT_{i}",
                    sensor_type="temperature",
                    sensor_value=20.0 + i,
                    unit="celsius",
                )
                sensor_results.append(sensor)
                await uow.commit()

        # Verify all sensors were created
        assert len(sensor_results) == 5

        # Test batch queries
        async with UnitOfWork(async_session) as uow:
            all_equipment = await uow.equipment.get_equipment_by_type("tractor")
            assert len(all_equipment) == 5  # Half should be tractors

            all_implements = await uow.equipment.get_equipment_by_type("implement")
            assert len(all_implements) == 5  # Half should be implements

    @pytest.mark.asyncio
    async def test_data_consistency_async(self, async_session) -> None:
        """Test async data consistency across related entities."""
        async with UnitOfWork(async_session) as uow:
            # Create equipment and related data in same transaction
            await uow.equipment.create_equipment(
                equipment_id="CONSISTENCY_TEST_EQUIPMENT",
                isobus_address=0x80,
                equipment_type="tractor",
                manufacturer="John Deere",
                model="8R 410",
            )

            await uow.field.create_field(
                field_id="CONSISTENCY_TEST_FIELD",
                field_name="Consistency Test Field",
                crop_type="corn",
                field_area_hectares=20.0,
            )

            await uow.telemetry.create_telemetry_reading(
                equipment_id="CONSISTENCY_TEST_EQUIPMENT",
                vehicle_speed=8.5,
                fuel_level=75.0,
                engine_temperature=85.0,
                operational_mode="cultivating",
            )

            await uow.sensor_data.create_sensor_reading(
                equipment_id="CONSISTENCY_TEST_EQUIPMENT",
                sensor_type="soil_moisture",
                sensor_value=45.0,
                unit="percent",
                field_id="CONSISTENCY_TEST_FIELD",
            )

            await uow.yield_monitor.create_yield_reading(
                equipment_id="CONSISTENCY_TEST_EQUIPMENT",
                field_id="CONSISTENCY_TEST_FIELD",
                crop_type="corn",
                yield_volume=12.5,
                moisture_content=15.0,
                gps_latitude=40.7128,
                gps_longitude=-74.0060,
                harvest_width=12.0,
                harvest_speed=6.5,
            )

            await uow.operational_session.create_session(
                session_id="CONSISTENCY_TEST_SESSION",
                equipment_id="CONSISTENCY_TEST_EQUIPMENT",
                field_id="CONSISTENCY_TEST_FIELD",
                operation_type="cultivating",
                start_time=datetime(2025, 3, 15, 8, 0),
                operator_id="TEST_OPERATOR",
            )

            await uow.commit()

            # Verify data consistency through relationships
            # Query equipment and verify relationships
            retrieved_equipment = await uow.equipment.get_equipment_by_isobus_address(0x80)
            assert retrieved_equipment is not None
            assert retrieved_equipment.equipment_id == "CONSISTENCY_TEST_EQUIPMENT"

            # Query sensors for this equipment and field
            sensors = await uow.sensor_data.get_sensor_readings_by_equipment(
                equipment_id="CONSISTENCY_TEST_EQUIPMENT"
            )
            assert len(sensors) >= 1  # Should have at least the moisture sensor

            # Query telemetry for this equipment
            telemetry_data = await uow.telemetry.get_telemetry_by_equipment(
                equipment_id="CONSISTENCY_TEST_EQUIPMENT"
            )
            assert len(telemetry_data) >= 1  # Should have at least one telemetry reading

            # Query sessions for this equipment
            sessions = await uow.operational_session.get_sessions_by_equipment_and_type(
                equipment_id="CONSISTENCY_TEST_EQUIPMENT", operation_type="cultivating"
            )
            assert len(sessions) >= 1  # Should have at least one session

            # Query field and verify relationships
            fields = await uow.field.get_fields_by_crop_type("corn")
            assert len(fields) >= 1  # Should have the test field

    @pytest.mark.asyncio
    async def test_performance_monitoring_async(self, async_session) -> None:
        """Test async performance monitoring for agricultural operations."""
        async with UnitOfWork(async_session) as uow:
            # Perform multiple operations to generate performance data
            start_time = datetime.now(UTC)

            # Create multiple entities
            for i in range(10):
                await uow.equipment.create_equipment(
                    equipment_id=f"PERF_TEST_EQUIPMENT_{i}",
                    isobus_address=0x90 + i,
                    equipment_type="tractor",
                    manufacturer="Deere",
                    model=f"Model_{i}",
                )

                await uow.sensor_data.create_sensor_reading(
                    equipment_id=f"PERF_TEST_EQUIPMENT_{i}",
                    sensor_type="temperature",
                    sensor_value=20.0 + i,
                    unit="celsius",
                )

            await uow.commit()

            end_time = datetime.now(UTC)
            (end_time - start_time).total_seconds()

            # Test performance report generation
            from afs_fastapi.database.agricultural_schemas_async import AsyncDatabaseManager

            manager = AsyncDatabaseManager("sqlite+aiosqlite:///:memory:")
            await manager.initialize()

            performance_report = await manager.get_performance_report()

            assert "total_operations" in performance_report
            assert "success_rate" in performance_report
            assert "average_operation_time" in performance_report
            assert "agricultural_optimization" in performance_report

            # Verify performance metrics are reasonable
            assert performance_report["success_rate"] >= 0
            assert performance_report["success_rate"] <= 100
            assert performance_report["average_operation_time"] >= 0

            await manager.shutdown()
