"""
Test critical tractor data handlers for speed, fuel level, and GPS coordinates.

These tests validate the specialized handlers for the most critical agricultural
equipment data streams, including validation, filtering, alerting, and
precision agriculture features.

Implementation follows Test-First Development (TDD) validation.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from afs_fastapi.core.can_frame_codec import CANFrameCodec, DecodedPGN, DecodedSPN
from afs_fastapi.equipment.can_error_handling import CANErrorHandler
from afs_fastapi.equipment.critical_tractor_data_handlers import (
    Alert,
    AlertLevel,
    CriticalDataAggregator,
    DataQuality,
    FuelData,
    FuelDataHandler,
    GPSData,
    GPSDataHandler,
    SpeedData,
    SpeedDataHandler,
)


class TestSpeedDataHandler:
    """Test speed data handler with agricultural validation."""

    @pytest.fixture
    def error_handler(self) -> CANErrorHandler:
        """Create error handler for testing."""
        return CANErrorHandler()

    @pytest.fixture
    def speed_handler(self, error_handler: CANErrorHandler) -> SpeedDataHandler:
        """Create speed data handler for testing."""
        return SpeedDataHandler(error_handler)

    @pytest.fixture
    def speed_message(self) -> DecodedPGN:
        """Create test speed message."""
        speed_spn = DecodedSPN(
            spn=84,  # Wheel-Based Vehicle Speed
            name="Wheel-Based Vehicle Speed",
            value=15.5,  # 15.5 km/h
            units="km/h",
            raw_value=3968,  # Raw encoded value
            is_valid=True,
            is_not_available=False,
            is_error=False,
        )

        return DecodedPGN(
            pgn=0xFEF1,  # Wheel-Based Vehicle Speed
            name="Wheel-Based Vehicle Speed",
            source_address=0x81,
            destination_address=0xFF,
            priority=6,
            timestamp=datetime.now(UTC),
            spn_values=[speed_spn],
            raw_data=b"\x00\x00\x00\x00\x00\x00\x00\x00",
            data_length=8,
        )

    def test_process_valid_speed_message(
        self, speed_handler: SpeedDataHandler, speed_message: DecodedPGN
    ) -> None:
        """Test processing a valid speed message."""
        # Process speed message
        result = speed_handler.process_speed_message(speed_message)

        # Verify processing
        assert result is not None
        assert isinstance(result, SpeedData)
        assert result.value == 15.5
        assert result.units == "km/h"
        assert result.source_address == 0x81
        assert result.working_speed is True  # 15.5 km/h is working speed
        assert result.quality == DataQuality.GOOD

    def test_process_invalid_speed_message(
        self, speed_handler: SpeedDataHandler, speed_message: DecodedPGN
    ) -> None:
        """Test processing invalid speed message."""
        # Make SPN invalid
        speed_message.spn_values[0].is_valid = False

        # Process message
        result = speed_handler.process_speed_message(speed_message)

        # Should return None for invalid data
        assert result is None

    def test_speed_quality_assessment(
        self, speed_handler: SpeedDataHandler, speed_message: DecodedPGN
    ) -> None:
        """Test speed quality assessment with variance analysis."""
        # Process several similar speeds to build history
        for speed in [15.0, 15.2, 15.1, 15.3, 15.0]:
            speed_message.spn_values[0].value = speed
            speed_handler.process_speed_message(speed_message)

        # Process a very stable speed
        speed_message.spn_values[0].value = 15.1
        result = speed_handler.process_speed_message(speed_message)

        assert result is not None
        assert result.quality == DataQuality.EXCELLENT

        # Process a highly variable speed
        speed_message.spn_values[0].value = 20.0  # 30%+ variance
        result = speed_handler.process_speed_message(speed_message)

        assert result is not None
        assert result.quality == DataQuality.POOR

    def test_working_speed_detection(
        self, speed_handler: SpeedDataHandler, speed_message: DecodedPGN
    ) -> None:
        """Test working speed vs transport speed detection."""
        # Test working speed
        speed_message.spn_values[0].value = 12.0
        result = speed_handler.process_speed_message(speed_message)
        assert result is not None
        assert result.working_speed is True

        # Test transport speed
        speed_message.spn_values[0].value = 50.0
        result = speed_handler.process_speed_message(speed_message)
        assert result is not None
        assert result.working_speed is False

        # Test idle speed
        speed_message.spn_values[0].value = 0.1
        result = speed_handler.process_speed_message(speed_message)
        assert result is not None
        assert result.working_speed is False

    def test_speed_alerts(self, speed_handler: SpeedDataHandler, speed_message: DecodedPGN) -> None:
        """Test speed alert generation."""
        alerts_received: list[Alert] = []
        speed_handler.add_alert_callback(alerts_received.append)

        # Test overspeed in working mode (speed is 30.0 but not in working mode, so no working speed alert)
        speed_message.spn_values[0].value = (
            30.0  # Exceeds max working speed (25.0), so not working speed
        )
        result = speed_handler.process_speed_message(speed_message)

        assert result is not None
        # Since 30.0 > 25.0 (max_working_speed), this is NOT considered working speed
        # So no "Working speed exceeded" alert should be generated
        assert len(alerts_received) == 0  # No alerts for transport speed that's not excessive

        # Test critical overspeed
        alerts_received.clear()
        speed_message.spn_values[0].value = 90.0  # Exceeds max transport speed
        result = speed_handler.process_speed_message(speed_message)

        assert result is not None
        assert len(alerts_received) == 1
        assert alerts_received[0].level == AlertLevel.CRITICAL
        assert "Transport speed exceeded" in alerts_received[0].message


class TestFuelDataHandler:
    """Test fuel data handler with consumption tracking."""

    @pytest.fixture
    def error_handler(self) -> CANErrorHandler:
        """Create error handler for testing."""
        return CANErrorHandler()

    @pytest.fixture
    def fuel_handler(self, error_handler: CANErrorHandler) -> FuelDataHandler:
        """Create fuel data handler for testing."""
        return FuelDataHandler(error_handler)

    @pytest.fixture
    def fuel_message(self) -> DecodedPGN:
        """Create test fuel message."""
        fuel_rate_spn = DecodedSPN(
            spn=183,  # Engine Fuel Rate
            name="Engine Fuel Rate",
            value=12.5,  # 12.5 L/h
            units="L/h",
            raw_value=250,  # Raw encoded value
            is_valid=True,
            is_not_available=False,
            is_error=False,
        )

        return DecodedPGN(
            pgn=0xFEF2,  # Fuel Economy
            name="Fuel Economy",
            source_address=0x81,
            destination_address=0xFF,
            priority=6,
            timestamp=datetime.now(UTC),
            spn_values=[fuel_rate_spn],
            raw_data=b"\x00\x00\x00\x00\x00\x00\x00\x00",
            data_length=8,
        )

    def test_process_valid_fuel_message(
        self, fuel_handler: FuelDataHandler, fuel_message: DecodedPGN
    ) -> None:
        """Test processing a valid fuel message."""
        # Process fuel message
        result = fuel_handler.process_fuel_message(fuel_message)

        # Verify processing
        assert result is not None
        assert isinstance(result, FuelData)
        assert result.value == 12.5
        assert result.units == "L/h"
        assert result.source_address == 0x81
        assert result.fuel_rate_lh == 12.5
        assert result.operational_mode == "normal_work"
        assert result.fuel_level_percent > 0

    def test_operational_mode_detection(
        self, fuel_handler: FuelDataHandler, fuel_message: DecodedPGN
    ) -> None:
        """Test operational mode detection based on fuel consumption."""
        # Test idle mode
        fuel_message.spn_values[0].value = 1.5
        result = fuel_handler.process_fuel_message(fuel_message)
        assert result is not None
        assert result.operational_mode == "idle"

        # Test light work mode
        fuel_message.spn_values[0].value = 5.0
        result = fuel_handler.process_fuel_message(fuel_message)
        assert result is not None
        assert result.operational_mode == "light_work"

        # Test normal work mode
        fuel_message.spn_values[0].value = 15.0
        result = fuel_handler.process_fuel_message(fuel_message)
        assert result is not None
        assert result.operational_mode == "normal_work"

        # Test heavy work mode
        fuel_message.spn_values[0].value = 25.0
        result = fuel_handler.process_fuel_message(fuel_message)
        assert result is not None
        assert result.operational_mode == "heavy_work"

    def test_fuel_alerts(self, fuel_handler: FuelDataHandler, fuel_message: DecodedPGN) -> None:
        """Test fuel level and consumption alerts."""
        alerts_received: list[Alert] = []
        fuel_handler.add_alert_callback(alerts_received.append)

        # Mock fuel level estimation to return low fuel
        with patch.object(fuel_handler, "_estimate_fuel_level", return_value=15.0):
            result = fuel_handler.process_fuel_message(fuel_message)

        assert result is not None
        assert len(alerts_received) == 1
        assert alerts_received[0].level == AlertLevel.WARNING
        assert "Low fuel level" in alerts_received[0].message

        # Test critical fuel level
        alerts_received.clear()
        with patch.object(fuel_handler, "_estimate_fuel_level", return_value=5.0):
            result = fuel_handler.process_fuel_message(fuel_message)

        assert result is not None
        assert len(alerts_received) == 1
        assert alerts_received[0].level == AlertLevel.CRITICAL
        assert "Critical fuel level" in alerts_received[0].message

        # Test high consumption alert
        alerts_received.clear()
        fuel_message.spn_values[0].value = 35.0  # High consumption
        with patch.object(fuel_handler, "_estimate_fuel_level", return_value=50.0):
            result = fuel_handler.process_fuel_message(fuel_message)

        assert result is not None
        assert len(alerts_received) == 1
        assert alerts_received[0].level == AlertLevel.WARNING
        assert "High fuel consumption" in alerts_received[0].message


class TestGPSDataHandler:
    """Test GPS data handler with precision agriculture features."""

    @pytest.fixture
    def error_handler(self) -> CANErrorHandler:
        """Create error handler for testing."""
        return CANErrorHandler()

    @pytest.fixture
    def gps_handler(self, error_handler: CANErrorHandler) -> GPSDataHandler:
        """Create GPS data handler for testing."""
        return GPSDataHandler(error_handler)

    @pytest.fixture
    def gps_message(self) -> DecodedPGN:
        """Create test GPS message."""
        lat_spn = DecodedSPN(
            spn=584,  # Latitude
            name="Latitude",
            value=40.123456,  # Valid latitude
            units="degrees",
            raw_value=401234560,  # Raw encoded value
            is_valid=True,
            is_not_available=False,
            is_error=False,
        )

        lon_spn = DecodedSPN(
            spn=585,  # Longitude
            name="Longitude",
            value=-85.654321,  # Valid longitude
            units="degrees",
            raw_value=-856543210,  # Raw encoded value
            is_valid=True,
            is_not_available=False,
            is_error=False,
        )

        return DecodedPGN(
            pgn=0xFEF3,  # Vehicle Position
            name="Vehicle Position",
            source_address=0x81,
            destination_address=0xFF,
            priority=6,
            timestamp=datetime.now(UTC),
            spn_values=[lat_spn, lon_spn],
            raw_data=b"\x00\x00\x00\x00\x00\x00\x00\x00",
            data_length=8,
        )

    def test_process_valid_gps_message(
        self, gps_handler: GPSDataHandler, gps_message: DecodedPGN
    ) -> None:
        """Test processing a valid GPS message."""
        # Process GPS message
        result = gps_handler.process_gps_message(gps_message)

        # Verify processing
        assert result is not None
        assert isinstance(result, GPSData)
        assert result.latitude == 40.123456
        assert result.longitude == -85.654321
        assert result.source_address == 0x81
        assert result.field_id is not None
        assert result.zone_id is not None
        assert result.satellite_count is not None
        assert result.hdop is not None

    def test_coordinate_validation(
        self, gps_handler: GPSDataHandler, gps_message: DecodedPGN
    ) -> None:
        """Test GPS coordinate validation."""
        # Test invalid latitude
        gps_message.spn_values[0].value = 91.0  # Invalid latitude
        result = gps_handler.process_gps_message(gps_message)
        assert result is None

        # Test invalid longitude
        gps_message.spn_values[0].value = 40.0  # Valid latitude
        gps_message.spn_values[1].value = 181.0  # Invalid longitude
        result = gps_handler.process_gps_message(gps_message)
        assert result is None

    def test_haversine_distance_calculation(self, gps_handler: GPSDataHandler) -> None:
        """Test Haversine distance calculation."""
        # Test known distance calculation
        # Approximate distance between two points
        lat1, lon1 = 40.0, -85.0
        lat2, lon2 = 40.001, -85.001  # ~157 meters apart

        distance = gps_handler._haversine_distance(lat1, lon1, lat2, lon2)

        # Should be approximately 0.157 km
        assert 0.1 < distance < 0.2

    def test_speed_over_ground_calculation(
        self, gps_handler: GPSDataHandler, gps_message: DecodedPGN
    ) -> None:
        """Test speed over ground calculation from position history."""
        # First position
        result1 = gps_handler.process_gps_message(gps_message)
        assert result1 is not None
        assert result1.speed_over_ground is None  # No history yet

        # Second position (simulate movement)
        with patch(
            "afs_fastapi.equipment.critical_tractor_data_handlers.datetime"
        ) as mock_datetime:
            # Simulate 1 second later
            mock_datetime.now.return_value = datetime.now(UTC) + timedelta(seconds=1)

            gps_message.spn_values[0].value = 40.124456  # Moved ~111 meters north
            result2 = gps_handler.process_gps_message(gps_message)

        assert result2 is not None
        assert result2.speed_over_ground is not None
        # Should show significant speed (movement over time)

    def test_precision_agriculture_features(
        self, gps_handler: GPSDataHandler, gps_message: DecodedPGN
    ) -> None:
        """Test precision agriculture feature enhancement."""
        result = gps_handler.process_gps_message(gps_message)

        assert result is not None
        # Check that precision agriculture features are added
        assert result.field_id is not None
        assert result.field_id.startswith("field_")
        assert result.zone_id is not None
        assert result.zone_id.startswith("zone_")
        assert result.guidance_error == 0.5  # Default guidance error

    def test_gps_quality_alerts(self, gps_handler: GPSDataHandler, gps_message: DecodedPGN) -> None:
        """Test GPS quality and satellite alerts."""
        alerts_received: list[Alert] = []
        gps_handler.add_alert_callback(alerts_received.append)

        # Mock poor quality GPS
        with patch.object(gps_handler, "_assess_gps_quality", return_value=DataQuality.POOR):
            with patch.object(gps_handler, "_estimate_satellite_count", return_value=3):
                with patch.object(gps_handler, "_estimate_hdop", return_value=3.0):
                    result = gps_handler.process_gps_message(gps_message)

        assert result is not None
        assert len(alerts_received) == 3  # Quality, satellites, HDOP alerts

        alert_messages = [alert.message for alert in alerts_received]
        assert any("GPS signal quality degraded" in msg for msg in alert_messages)
        assert any("Low satellite count" in msg for msg in alert_messages)
        assert any("Poor GPS accuracy" in msg for msg in alert_messages)


class TestCriticalDataAggregator:
    """Test unified critical data aggregator and alerting system."""

    @pytest.fixture
    def codec(self) -> CANFrameCodec:
        """Create CAN frame codec for testing."""
        return CANFrameCodec()

    @pytest.fixture
    def error_handler(self) -> CANErrorHandler:
        """Create error handler for testing."""
        return CANErrorHandler()

    @pytest.fixture
    def aggregator(
        self, codec: CANFrameCodec, error_handler: CANErrorHandler
    ) -> CriticalDataAggregator:
        """Create critical data aggregator for testing."""
        return CriticalDataAggregator(codec, error_handler)

    @pytest.fixture
    def speed_message(self) -> DecodedPGN:
        """Create test speed message."""
        speed_spn = DecodedSPN(
            spn=84,
            name="Wheel-Based Vehicle Speed",
            value=15.5,
            units="km/h",
            raw_value=3968,  # Raw encoded value
            is_valid=True,
            is_not_available=False,
            is_error=False,
        )

        return DecodedPGN(
            pgn=0xFEF1,
            name="Wheel-Based Vehicle Speed",
            source_address=0x81,
            destination_address=0xFF,
            priority=6,
            timestamp=datetime.now(UTC),
            spn_values=[speed_spn],
            raw_data=b"\x00\x00\x00\x00\x00\x00\x00\x00",
            data_length=8,
        )

    def test_process_speed_message(
        self, aggregator: CriticalDataAggregator, speed_message: DecodedPGN
    ) -> None:
        """Test processing speed message through aggregator."""
        # Process speed message
        result = aggregator.process_message(speed_message)

        assert result is True

        # Check aggregated data
        current_data = aggregator.get_current_data(0x81)
        assert 0x81 in current_data
        assert current_data[0x81]["speed"] is not None
        assert current_data[0x81]["speed"].value == 15.5

    def test_equipment_summary(
        self, aggregator: CriticalDataAggregator, speed_message: DecodedPGN
    ) -> None:
        """Test equipment summary generation."""
        # Process a message to have some data
        aggregator.process_message(speed_message)

        # Get equipment summary
        summary = aggregator.get_equipment_summary(0x81)

        assert summary["source_address"] == 0x81
        assert summary["online"] is True
        assert summary["speed"] is not None
        assert summary["speed"]["current_speed"] == 15.5
        assert summary["speed"]["working_speed"] is True
        assert summary["overall_status"] == "healthy"

    def test_equipment_status_assessment(self, aggregator: CriticalDataAggregator) -> None:
        """Test overall equipment status assessment."""
        # Test offline status
        summary = aggregator.get_equipment_summary(0x99)  # Non-existent equipment
        assert (
            summary["overall_status"] == "offline"
        )  # Should be offline for non-existent equipment
        assert summary["online"] is False

    def test_alert_forwarding(
        self, aggregator: CriticalDataAggregator, speed_message: DecodedPGN
    ) -> None:
        """Test alert forwarding from individual handlers."""
        alerts_received: list[Alert] = []
        aggregator.add_alert_callback(alerts_received.append)

        # Process high speed message that should trigger alert
        speed_message.spn_values[0].value = 90.0  # Exceeds transport speed limit
        aggregator.process_message(speed_message)

        # Should receive forwarded alert
        assert len(alerts_received) == 1
        assert alerts_received[0].level == AlertLevel.CRITICAL
        assert "Transport speed exceeded" in alerts_received[0].message

    def test_data_callback_notifications(
        self, aggregator: CriticalDataAggregator, speed_message: DecodedPGN
    ) -> None:
        """Test data update callback notifications."""
        updates_received: list[tuple[int, dict]] = []

        def data_callback(source_address: int, data: dict) -> None:
            updates_received.append((source_address, data))

        aggregator.add_data_callback(data_callback)

        # Process message
        aggregator.process_message(speed_message)

        # Should receive data update notification
        assert len(updates_received) == 1
        assert updates_received[0][0] == 0x81
        assert "speed" in updates_received[0][1]

    def test_multiple_message_types(
        self, aggregator: CriticalDataAggregator, speed_message: DecodedPGN
    ) -> None:
        """Test processing multiple types of critical messages."""
        # Create fuel message
        fuel_spn = DecodedSPN(
            spn=183,
            name="Engine Fuel Rate",
            value=12.5,
            units="L/h",
            raw_value=250,
            is_valid=True,
            is_not_available=False,
            is_error=False,
        )
        fuel_message = DecodedPGN(
            pgn=0xFEF2,
            name="Fuel Economy",
            source_address=0x81,
            destination_address=0xFF,
            priority=6,
            timestamp=datetime.now(UTC),
            spn_values=[fuel_spn],
            raw_data=b"\x00\x00\x00\x00\x00\x00\x00\x00",
            data_length=8,
        )

        # Create GPS message
        lat_spn = DecodedSPN(
            spn=584,
            name="Latitude",
            value=40.123456,
            units="degrees",
            raw_value=401234560,
            is_valid=True,
            is_not_available=False,
            is_error=False,
        )
        lon_spn = DecodedSPN(
            spn=585,
            name="Longitude",
            value=-85.654321,
            units="degrees",
            raw_value=-856543210,
            is_valid=True,
            is_not_available=False,
            is_error=False,
        )
        gps_message = DecodedPGN(
            pgn=0xFEF3,  # Vehicle Position
            name="Vehicle Position",
            source_address=0x81,
            destination_address=0xFF,
            priority=6,
            timestamp=datetime.now(UTC),
            spn_values=[lat_spn, lon_spn],
            raw_data=b"\x00\x00\x00\x00\x00\x00\x00\x00",
            data_length=8,
        )

        # Process all message types
        assert aggregator.process_message(speed_message) is True
        assert aggregator.process_message(fuel_message) is True
        assert aggregator.process_message(gps_message) is True

        # Check comprehensive summary
        summary = aggregator.get_equipment_summary(0x81)
        assert summary["speed"] is not None
        assert summary["fuel"] is not None
        assert summary["gps"] is not None
        assert summary["overall_status"] == "healthy"


# Integration test to verify the complete system
class TestCriticalDataIntegration:
    """Integration tests for the complete critical data handling system."""

    def test_complete_tractor_monitoring_workflow(self) -> None:
        """Test complete workflow for tractor monitoring with all critical data types."""
        # Setup components
        codec = CANFrameCodec()
        error_handler = CANErrorHandler()
        aggregator = CriticalDataAggregator(codec, error_handler)

        # Collection for alerts and data updates
        alerts_received: list[Alert] = []
        data_updates: list[tuple[int, dict]] = []

        aggregator.add_alert_callback(alerts_received.append)
        aggregator.add_data_callback(lambda addr, data: data_updates.append((addr, data)))

        # Simulate tractor operation data over time
        tractor_address = 0x81

        # Initial speed data - working speed
        speed_spn = DecodedSPN(
            spn=84,
            name="Wheel-Based Vehicle Speed",
            value=12.0,
            units="km/h",
            raw_value=3072,
            is_valid=True,
            is_not_available=False,
            is_error=False,
        )
        speed_msg = DecodedPGN(
            pgn=0xFEF1,
            name="Wheel-Based Vehicle Speed",
            source_address=tractor_address,
            destination_address=0xFF,
            priority=6,
            timestamp=datetime.now(UTC),
            spn_values=[speed_spn],
            raw_data=b"\x00\x00\x00\x00\x00\x00\x00\x00",
            data_length=8,
        )

        # Normal fuel consumption
        fuel_spn = DecodedSPN(
            spn=183,
            name="Engine Fuel Rate",
            value=15.0,
            units="L/h",
            raw_value=300,
            is_valid=True,
            is_not_available=False,
            is_error=False,
        )
        fuel_msg = DecodedPGN(
            pgn=0xFEF2,
            name="Fuel Economy",
            source_address=tractor_address,
            destination_address=0xFF,
            priority=6,
            timestamp=datetime.now(UTC),
            spn_values=[fuel_spn],
            raw_data=b"\x00\x00\x00\x00\x00\x00\x00\x00",
            data_length=8,
        )

        # GPS position
        lat_spn = DecodedSPN(
            spn=584,
            name="Latitude",
            value=40.123456,
            units="degrees",
            raw_value=401234560,
            is_valid=True,
            is_not_available=False,
            is_error=False,
        )
        lon_spn = DecodedSPN(
            spn=585,
            name="Longitude",
            value=-85.654321,
            units="degrees",
            raw_value=-856543210,
            is_valid=True,
            is_not_available=False,
            is_error=False,
        )
        gps_msg = DecodedPGN(
            pgn=0xFEF3,
            name="Vehicle Position",
            source_address=tractor_address,
            destination_address=0xFF,
            priority=6,
            timestamp=datetime.now(UTC),
            spn_values=[lat_spn, lon_spn],
            raw_data=b"\x00\x00\x00\x00\x00\x00\x00\x00",
            data_length=8,
        )

        # Process normal operation
        assert aggregator.process_message(speed_msg) is True
        assert aggregator.process_message(fuel_msg) is True
        assert aggregator.process_message(gps_msg) is True

        # Verify normal operation status
        summary = aggregator.get_equipment_summary(tractor_address)
        assert summary["overall_status"] == "healthy"
        assert summary["online"] is True
        assert len(summary["alerts"]) == 0

        # Simulate problem conditions
        # High speed condition
        speed_spn.value = 85.0  # Excessive transport speed
        aggregator.process_message(speed_msg)

        # Check alert generation
        assert len(alerts_received) == 1
        assert alerts_received[0].level == AlertLevel.CRITICAL
        assert "Transport speed exceeded" in alerts_received[0].message

        # Updated status should show critical condition
        summary = aggregator.get_equipment_summary(tractor_address)
        assert summary["overall_status"] == "critical"
        assert len(summary["alerts"]) > 0

        # Verify all data update notifications were sent
        assert len(data_updates) >= 4  # At least 4 processing events
