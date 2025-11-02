"""
Test agricultural sensor data models with ISOBUS integration.

This module tests the agricultural sensor data structures that integrate
with the established ISOBUS communication infrastructure for real-world
tractor and implement data collection.

Implementation follows Test-First Development (TDD) RED phase.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from afs_fastapi.equipment.farm_tractors import ISOBUSMessage
from afs_fastapi.models.agricultural_sensor_data import (
    AgriculturalSensorData,
    SensorType,
    TractorTelemetryData,
    YieldMonitorData,
)


class TestAgriculturalSensorData:
    """Test agricultural sensor data with ISOBUS message integration."""

    def test_agricultural_sensor_data_creation(self) -> None:
        """Test creation of agricultural sensor data from ISOBUS message."""
        # RED: Define desired agricultural sensor behavior

        # Create ISOBUS message for soil moisture sensor
        isobus_msg = ISOBUSMessage(
            pgn=0xE003,  # Agricultural sensor PGN
            source_address=0x42,
            destination_address=0xFF,  # Broadcast
            data=b"\x01\x23\x45\x67",  # Sensor reading bytes
            timestamp=datetime(2025, 10, 8, 17, 0, 0),
        )

        # Create agricultural sensor data
        sensor_data = AgriculturalSensorData(
            timestamp=datetime(2025, 10, 8, 17, 0, 0),
            tractor_id="FIELD_CULTIVATOR_01",
            isobus_source=isobus_msg,
            sensor_type=SensorType.SOIL_MOISTURE,
            value=45.7,
            unit="percent",
            field_coordinates=(40.7128, -74.0060),  # Example farm coordinates
        )

        # Test agricultural sensor data properties
        assert sensor_data.tractor_id == "FIELD_CULTIVATOR_01"
        assert sensor_data.sensor_type == SensorType.SOIL_MOISTURE
        assert sensor_data.value == 45.7
        assert sensor_data.unit == "percent"
        assert sensor_data.isobus_source.pgn == 0xE003
        assert sensor_data.field_coordinates == (40.7128, -74.0060)

    def test_sensor_type_enumeration(self) -> None:
        """Test sensor type enumeration for agricultural operations."""
        # RED: Test comprehensive sensor type support

        # Verify soil monitoring sensors
        assert SensorType.SOIL_MOISTURE == "soil_moisture"
        assert SensorType.SOIL_TEMPERATURE == "soil_temperature"
        assert SensorType.SOIL_PH == "soil_ph"

        # Verify crop monitoring sensors
        assert SensorType.YIELD_MONITOR == "yield_monitor"
        assert SensorType.CROP_HEIGHT == "crop_height"

        # Verify environmental sensors
        assert SensorType.GPS_POSITION == "gps_position"
        assert SensorType.WEATHER_STATION == "weather_station"

        # Verify equipment sensors
        assert SensorType.FUEL_LEVEL == "fuel_level"
        assert SensorType.ENGINE_TEMPERATURE == "engine_temperature"


class TestTractorTelemetryData:
    """Test tractor telemetry data structures for fleet coordination."""

    def test_tractor_telemetry_creation(self) -> None:
        """Test creation of tractor telemetry from ISOBUS communication."""
        # RED: Define desired tractor telemetry behavior

        # Create ISOBUS message for tractor status
        isobus_msg = ISOBUSMessage(
            pgn=0xE004,  # Tractor telemetry PGN
            source_address=0x23,
            destination_address=0xFF,  # Broadcast
            data=b"\x12\x34\x56\x78\x9A\xBC",  # Telemetry bytes
            timestamp=datetime(2025, 10, 8, 17, 5, 0),
        )

        # Create tractor telemetry data
        telemetry = TractorTelemetryData(
            timestamp=datetime(2025, 10, 8, 17, 5, 0),
            tractor_id="HARVESTER_02",
            isobus_source=isobus_msg,
            vehicle_speed=12.5,  # km/h
            fuel_level=78.3,  # percent
            engine_temperature=87.2,  # celsius
            gps_coordinates=(40.7580, -73.9855),
            operational_mode="harvesting",
        )

        # Test tractor telemetry properties
        assert telemetry.tractor_id == "HARVESTER_02"
        assert telemetry.vehicle_speed == 12.5
        assert telemetry.fuel_level == 78.3
        assert telemetry.engine_temperature == 87.2
        assert telemetry.gps_coordinates == (40.7580, -73.9855)
        assert telemetry.operational_mode == "harvesting"
        assert telemetry.isobus_source.pgn == 0xE004

    def test_telemetry_validation(self) -> None:
        """Test tractor telemetry data validation for safety compliance."""
        # RED: Test validation for agricultural safety requirements

        isobus_msg = ISOBUSMessage(
            pgn=0xE004,
            source_address=0x23,
            destination_address=0xFF,
            data=b"\x00\x00\x00\x00",
            timestamp=datetime.now(),
        )

        # Test speed validation (must be non-negative)
        with pytest.raises(ValueError, match="Vehicle speed must be non-negative"):
            TractorTelemetryData(
                timestamp=datetime.now(),
                tractor_id="TEST_TRACTOR",
                isobus_source=isobus_msg,
                vehicle_speed=-5.0,  # Invalid negative speed
                fuel_level=50.0,
                engine_temperature=80.0,
                gps_coordinates=(0.0, 0.0),
                operational_mode="testing",
            )

        # Test fuel level validation (must be 0-100%)
        with pytest.raises(ValueError, match="Fuel level must be between 0 and 100 percent"):
            TractorTelemetryData(
                timestamp=datetime.now(),
                tractor_id="TEST_TRACTOR",
                isobus_source=isobus_msg,
                vehicle_speed=10.0,
                fuel_level=150.0,  # Invalid fuel level
                engine_temperature=80.0,
                gps_coordinates=(0.0, 0.0),
                operational_mode="testing",
            )


class TestYieldMonitorData:
    """Test yield monitoring data for agricultural analytics."""

    def test_yield_monitor_creation(self) -> None:
        """Test creation of yield monitoring data from combine harvester."""
        # RED: Define desired yield monitoring behavior

        # Create ISOBUS message for yield data
        isobus_msg = ISOBUSMessage(
            pgn=0xE005,  # Yield monitor PGN
            source_address=0x45,
            destination_address=0xFF,  # Broadcast
            data=b"\xAA\xBB\xCC\xDD\xEE\xFF",  # Yield data bytes
            timestamp=datetime(2025, 10, 8, 17, 10, 0),
        )

        # Create yield monitor data
        yield_data = YieldMonitorData(
            timestamp=datetime(2025, 10, 8, 17, 10, 0),
            tractor_id="COMBINE_03",
            isobus_source=isobus_msg,
            crop_type="corn",
            yield_volume=8.7,  # tons per hectare
            moisture_content=15.2,  # percent
            field_coordinates=(40.7200, -74.0100),
            harvest_width=6.0,  # meters
            harvest_speed=5.5,  # km/h
        )

        # Test yield monitor properties
        assert yield_data.tractor_id == "COMBINE_03"
        assert yield_data.crop_type == "corn"
        assert yield_data.yield_volume == 8.7
        assert yield_data.moisture_content == 15.2
        assert yield_data.field_coordinates == (40.7200, -74.0100)
        assert yield_data.harvest_width == 6.0
        assert yield_data.harvest_speed == 5.5
        assert yield_data.isobus_source.pgn == 0xE005

    def test_yield_analytics_calculation(self) -> None:
        """Test yield analytics calculations for farm management."""
        # RED: Test agricultural yield calculation features

        isobus_msg = ISOBUSMessage(
            pgn=0xE005,
            source_address=0x45,
            destination_address=0xFF,
            data=b"\x12\x34\x56\x78",
            timestamp=datetime.now(),
        )

        yield_data = YieldMonitorData(
            timestamp=datetime.now(),
            tractor_id="COMBINE_03",
            isobus_source=isobus_msg,
            crop_type="soybeans",
            yield_volume=3.2,  # tons per hectare
            moisture_content=13.5,
            field_coordinates=(40.7200, -74.0100),
            harvest_width=6.0,
            harvest_speed=4.8,
        )

        # Test yield per minute calculation
        expected_yield_per_minute = (
            yield_data.yield_volume
            * yield_data.harvest_width
            * (yield_data.harvest_speed * 1000 / 60)
            / 10000  # Convert to tons/minute
        )

        assert abs(yield_data.calculate_yield_per_minute() - expected_yield_per_minute) < 0.001

        # Test area coverage calculation
        expected_area_hectares = (
            yield_data.harvest_width
            * (yield_data.harvest_speed * 1000)
            / 10000  # Convert to hectares per hour
        )

        assert (
            abs(yield_data.calculate_coverage_hectares_per_hour() - expected_area_hectares) < 0.001
        )
