"""
Comprehensive tests for agricultural-specific CAN protocol handlers.

Tests validate agricultural equipment communication, field operations,
safety systems, and precision agriculture protocols with SAE J1939/ISOBUS compliance.
"""

from __future__ import annotations

import asyncio
import struct
import time

import can
import pytest

from afs_fastapi.core.enhanced_can_validator import AgriculturalCANMessage, J1939ComplianceLevel
from afs_fastapi.equipment.agricultural_can_protocols import (
    AgriculturalCANBusManager,
    AgriculturalCANConfig,
    AgriculturalEquipmentProfile,
    AgriculturalEquipmentType,
    AgriculturalOperationMode,
    AgriculturalProtocolHandler,
)


class TestAgriculturalEquipmentProfile:
    """Test agricultural equipment profile management."""

    def test_equipment_profile_creation(self) -> None:
        """Test creation of agricultural equipment profiles."""
        profile = AgriculturalEquipmentProfile(
            equipment_id="TRACTOR_001",
            equipment_type=AgriculturalEquipmentType.TRACTOR,
            manufacturer="John Deere",
            model="6M Series",
            serial_number="JD6M001234",
            can_address=0x23,
            function_code=0x00,
            capabilities=["engine_control", "navigation", "implement_control"],
        )

        assert profile.equipment_id == "TRACTOR_001"
        assert profile.equipment_type == AgriculturalEquipmentType.TRACTOR
        assert profile.can_address == 0x23
        assert profile.function_code == 0x00
        assert profile.supports_j1939 is True
        assert profile.supports_isobus is True

    def test_j1939_name_field_generation(self) -> None:
        """Test J1939 NAME field generation for address claiming."""
        profile = AgriculturalEquipmentProfile(
            equipment_id="TRACTOR_001",
            equipment_type=AgriculturalEquipmentType.TRACTOR,
            manufacturer="John Deere",
            model="6M Series",
            serial_number="JD6M001234",
            can_address=0x23,
            function_code=0x00,
            capabilities=["engine_control"],
        )

        name_field = profile.to_j1939_name_field()
        assert len(name_field) == 8  # NAME field is 8 bytes
        # Verify some key bits are set
        assert name_field[0] & 0x80  # Arbitrary address capable bit

    def test_equipment_type_classification(self) -> None:
        """Test equipment type classification for agricultural operations."""
        profiles = [
            AgriculturalEquipmentProfile(
                equipment_id="TRACTOR_001",
                equipment_type=AgriculturalEquipmentType.TRACTOR,
                manufacturer="John Deere",
                model="6M Series",
                serial_number="JD6M001234",
                can_address=0x23,
                function_code=0x00,
                capabilities=[],
            ),
            AgriculturalEquipmentProfile(
                equipment_id="PLANTER_001",
                equipment_type=AgriculturalEquipmentType.PLANTER,
                manufacturer="Kincaid",
                model="Air Seeder",
                serial_number="KS001234",
                can_address=0x24,
                function_code=0x03,
                capabilities=[],
            ),
            AgriculturalEquipmentProfile(
                equipment_id="SPRAYER_001",
                equipment_type=AgriculturalEquipmentType.SPRAYER,
                manufacturer="Case IH",
                model="Applicator",
                serial_number="CI001234",
                can_address=0x25,
                function_code=0x05,
                capabilities=[],
            ),
        ]

        assert profiles[0].equipment_type == AgriculturalEquipmentType.TRACTOR
        assert profiles[1].equipment_type == AgriculturalEquipmentType.PLANTER
        assert profiles[2].equipment_type == AgriculturalEquipmentType.SPRAYER


class TestAgriculturalCANConfig:
    """Test agricultural CAN configuration management."""

    def test_default_configuration(self) -> None:
        """Test default configuration initialization."""
        profile = AgriculturalEquipmentProfile(
            equipment_id="TRACTOR_001",
            equipment_type=AgriculturalEquipmentType.TRACTOR,
            manufacturer="John Deere",
            model="6M Series",
            serial_number="JD6M001234",
            can_address=0x23,
            function_code=0x00,
            capabilities=[],
        )

        config = AgriculturalCANConfig(equipment_profile=profile)

        # Test default priorities
        assert config.message_priorities[0xE001] == 0  # Emergency Stop
        assert config.message_priorities[0xF004] == 1  # Engine Controller
        assert config.message_priorities[0xFEF1] == 2  # Vehicle Speed

        # Test default rate limits
        assert config.rate_limits[0xF004] == 50  # Engine data: 50ms
        assert config.rate_limits[0xFEF3] == 1000  # GPS position: 1000ms

        # Test default retry policies
        assert config.retry_policies["safety_critical"]["max_attempts"] == 5
        assert config.retry_policies["engine_data"]["max_attempts"] == 3

    def test_custom_configuration(self) -> None:
        """Test custom configuration with agricultural-specific settings."""
        profile = AgriculturalEquipmentProfile(
            equipment_id="IRRIGATION_001",
            equipment_type=AgriculturalEquipmentType.IRRIGATION,
            manufacturer="Valmont",
            model="Linear Move",
            serial_number="VM001234",
            can_address=0x26,
            function_code=0x09,
            capabilities=["irrigation_control", "weather_monitoring"],
        )

        custom_config = AgriculturalCANConfig(
            equipment_profile=profile,
            compliance_level=J1939ComplianceLevel.BASIC_COMPLIANCE,
            message_priorities={
                0xF004: 0,  # Engine data - high priority for irrigation system
                0xFEF1: 1,  # Vehicle speed
            },
            rate_limits={
                0xF004: 25,  # Higher rate for engine monitoring
                0xFEF3: 500,  # More frequent GPS updates
            },
        )

        assert custom_config.compliance_level == J1939ComplianceLevel.BASIC_COMPLIANCE
        assert custom_config.message_priorities[0xF004] == 0
        assert custom_config.rate_limits[0xF004] == 25


class TestAgriculturalOperationMode:
    """Test agricultural operation mode management."""

    def test_mode_transitions(self) -> None:
        """Test operation mode transitions for agricultural equipment."""
        # Initial mode should be IDLE
        assert AgriculturalOperationMode.IDLE.value == "idle"

        # Test valid transitions
        valid_transitions = [
            (AgriculturalOperationMode.IDLE, AgriculturalOperationMode.PREPARING),
            (AgriculturalOperationMode.PREPARING, AgriculturalOperationMode.WORKING),
            (AgriculturalOperationMode.WORKING, AgriculturalOperationMode.TRANSPORTING),
            (AgriculturalOperationMode.WORKING, AgriculturalOperationMode.IDLE),
            (AgriculturalOperationMode.EMERGENCY, AgriculturalOperationMode.IDLE),
        ]

        for _from_mode, to_mode in valid_transitions:
            assert to_mode.value in [
                "idle",
                "preparing",
                "working",
                "transporting",
                "maintenance",
                "emergency",
                "error",
            ]

    def test_mode_properties(self) -> None:
        """Test agricultural operation mode properties."""
        assert AgriculturalOperationMode.WORKING.value == "working"
        assert AgriculturalOperationMode.EMERGENCY.value == "emergency"
        assert AgriculturalOperationMode.MAINTENANCE.value == "maintenance"


class TestAgriculturalProtocolHandler:
    """Test agricultural protocol handler for equipment communication."""

    @pytest.mark.asyncio
    async def test_handler_initialization(self) -> None:
        """Test protocol handler initialization."""
        profile = AgriculturalEquipmentProfile(
            equipment_id="TRACTOR_001",
            equipment_type=AgriculturalEquipmentType.TRACTOR,
            manufacturer="John Deere",
            model="6M Series",
            serial_number="JD6M001234",
            can_address=0x23,
            function_code=0x00,
            capabilities=[],
        )

        config = AgriculturalCANConfig(equipment_profile=profile)
        handler = AgriculturalProtocolHandler(config)

        assert handler.equipment == profile
        assert handler.operation_mode == AgriculturalOperationMode.IDLE
        assert handler.codec is not None
        assert len(handler.received_messages) == 0

    @pytest.mark.asyncio
    async def test_valid_message_processing(self) -> None:
        """Test processing of valid agricultural messages."""
        profile = AgriculturalEquipmentProfile(
            equipment_id="TRACTOR_001",
            equipment_type=AgriculturalEquipmentType.TRACTOR,
            manufacturer="John Deere",
            model="6M Series",
            serial_number="JD6M001234",
            can_address=0x23,
            function_code=0x00,
            capabilities=[],
        )

        config = AgriculturalCANConfig(equipment_profile=profile)
        handler = AgriculturalProtocolHandler(config)

        # Create valid engine data message
        rpm_data = bytes([0x00, 0x00, 0x40, 0x00])  # 2000 RPM
        engine_message = can.Message(
            arbitration_id=0x18EEDF23,  # Engine Controller PGN + address
            data=rpm_data + b"\x00\x00\x00\x00",
            is_extended_id=True,
            timestamp=time.time(),
        )

        result = await handler.process_agricultural_message(engine_message)

        assert isinstance(result, AgriculturalCANMessage)
        assert result.pgn == 0xF004
        assert result.source_address == 0x23
        assert len(result.validation_results) > 0

        # Should update engine data
        assert "rpm" in handler.engine_data
        assert handler.engine_data["rpm"] == 250.0  # 2000 * 0.125

    @pytest.mark.asyncio
    async def test_operation_mode_updates(self) -> None:
        """Test operation mode updates based on message processing."""
        profile = AgriculturalEquipmentProfile(
            equipment_id="TRACTOR_001",
            equipment_type=AgriculturalEquipmentType.TRACTOR,
            manufacturer="John Deere",
            model="6M Series",
            serial_number="JD6M001234",
            can_address=0x23,
            function_code=0x00,
            capabilities=[],
        )

        config = AgriculturalCANConfig(equipment_profile=profile)
        handler = AgriculturalProtocolHandler(config)

        # Start in IDLE mode
        assert handler.operation_mode == AgriculturalOperationMode.IDLE

        # Process vehicle speed message (should transition to WORKING)
        speed_data = bytes([0x00, 0x40, 0x00, 0x00])  # 64 km/h
        speed_message = can.Message(
            arbitration_id=0x18FEDF21,  # Vehicle Speed PGN + address
            data=speed_data + b"\x00\x00\x00\x00",
            is_extended_id=True,
            timestamp=time.time(),
        )

        await handler.process_agricultural_message(speed_message)

        # Should transition to working mode
        assert handler.operation_mode == AgriculturalOperationMode.WORKING

    @pytest.mark.asyncio
    async def test_safety_message_handling(self) -> None:
        """Test safety-critical message handling."""
        profile = AgriculturalEquipmentProfile(
            equipment_id="TRACTOR_001",
            equipment_type=AgriculturalEquipmentType.TRACTOR,
            manufacturer="John Deere",
            model="6M Series",
            serial_number="JD6M001234",
            can_address=0x23,
            function_code=0x00,
            capabilities=[],
        )

        config = AgriculturalCANConfig(equipment_profile=profile)
        handler = AgriculturalProtocolHandler(config)

        # Process emergency stop message
        emergency_message = can.Message(
            arbitration_id=0x00EEDF23,  # Emergency Stop PGN + address
            data=b"\x00\x00\x00\x00\x00\x00\x00\x00",
            is_extended_id=True,
            timestamp=time.time(),
        )

        await handler.process_agricultural_message(emergency_message)

        # Should transition to emergency mode
        assert handler.operation_mode == AgriculturalOperationMode.EMERGENCY
        assert handler.safety_status["emergency_stop"] is True
        assert "emergency_timestamp" in handler.safety_status

    @pytest.mark.asyncio
    async def test_gps_position_processing(self) -> None:
        """Test GPS position data processing for agricultural navigation."""
        profile = AgriculturalEquipmentProfile(
            equipment_id="TRACTOR_001",
            equipment_type=AgriculturalEquipmentType.TRACTOR,
            manufacturer="John Deere",
            model="6M Series",
            serial_number="JD6M001234",
            can_address=0x23,
            function_code=0x00,
            capabilities=[],
        )

        config = AgriculturalCANConfig(equipment_profile=profile)
        handler = AgriculturalProtocolHandler(config)

        # Process GPS position message
        lat = int(40.7128 * 1e7)  # New York latitude
        lon = int(-74.0060 * 1e7)  # New York longitude
        # Handle negative longitude by using signed int representation
        gps_data = struct.pack("<ii", lat, lon)
        gps_message = can.Message(
            arbitration_id=0x18FEDF23,  # Vehicle Position PGN + address
            data=gps_data,
            is_extended_id=True,
            timestamp=time.time(),
        )

        await handler.process_agricultural_message(gps_message)

        # Should update position data
        assert "latitude" in handler.position_data
        assert "longitude" in handler.position_data
        assert handler.position_data["latitude"] == 40.7128
        assert handler.position_data["longitude"] == -74.0060
        assert handler.position_data["accuracy"] == "high"

    @pytest.mark.asyncio
    async def test_fuel_data_processing(self) -> None:
        """Test fuel data processing for agricultural operations."""
        profile = AgriculturalEquipmentProfile(
            equipment_id="TRACTOR_001",
            equipment_type=AgriculturalEquipmentType.TRACTOR,
            manufacturer="John Deere",
            model="6M Series",
            serial_number="JD6M001234",
            can_address=0x23,
            function_code=0x00,
            capabilities=[],
        )

        config = AgriculturalCANConfig(equipment_profile=profile)
        handler = AgriculturalProtocolHandler(config)

        # Process fuel level message
        fuel_data = bytes([0x00, 0x64, 0x00, 0x00])  # 25% fuel level
        fuel_message = can.Message(
            arbitration_id=0x18FEFC23,  # Fuel Level PGN + address
            data=fuel_data + b"\x00\x00\x00\x00",
            is_extended_id=True,
            timestamp=time.time(),
        )

        await handler.process_agricultural_message(fuel_message)

        # Should update fuel status
        assert "fuel_level_percent" in handler.safety_status
        assert handler.safety_status["fuel_level_percent"] == 25.0
        assert handler.safety_status["fuel_status"] == "moderate"

    def test_speed_category_assessment(self) -> None:
        """Test speed category assessment for agricultural operations."""
        profile = AgriculturalEquipmentProfile(
            equipment_id="TRACTOR_001",
            equipment_type=AgriculturalEquipmentType.TRACTOR,
            manufacturer="John Deere",
            model="6M Series",
            serial_number="JD6M001234",
            can_address=0x23,
            function_code=0x00,
            capabilities=[],
        )

        config = AgriculturalCANConfig(equipment_profile=profile)
        handler = AgriculturalProtocolHandler(config)

        # Test different speed categories
        assert handler._get_speed_category(0.0) == "stopped"
        assert handler._get_speed_category(3.0) == "maneuvering"
        assert handler._get_speed_category(10.0) == "field_work"
        assert handler._get_speed_category(25.0) == "transport"
        assert handler._get_speed_category(50.0) == "road_transport"

    def test_fuel_efficiency_assessment(self) -> None:
        """Test fuel efficiency assessment for agricultural operations."""
        profile = AgriculturalEquipmentProfile(
            equipment_id="TRACTOR_001",
            equipment_type=AgriculturalEquipmentType.TRACTOR,
            manufacturer="John Deere",
            model="6M Series",
            serial_number="JD6M001234",
            can_address=0x23,
            function_code=0x00,
            capabilities=[],
        )

        config = AgriculturalCANConfig(equipment_profile=profile)
        handler = AgriculturalProtocolHandler(config)

        # Test different efficiency scenarios
        assert handler._assess_fuel_efficiency(10.0, 20.0) == "excellent"  # Good economy
        assert handler._assess_fuel_efficiency(20.0, 12.0) == "good"
        assert handler._assess_fuel_efficiency(30.0, 7.0) == "fair"
        assert handler._assess_fuel_efficiency(40.0, 3.0) == "poor"

    def test_fuel_status_assessment(self) -> None:
        """Test fuel status assessment for agricultural equipment."""
        profile = AgriculturalEquipmentProfile(
            equipment_id="TRACTOR_001",
            equipment_type=AgriculturalEquipmentType.TRACTOR,
            manufacturer="John Deere",
            model="6M Series",
            serial_number="JD6M001234",
            can_address=0x23,
            function_code=0x00,
            capabilities=[],
        )

        config = AgriculturalCANConfig(equipment_profile=profile)
        handler = AgriculturalProtocolHandler(config)

        # Test different fuel levels
        assert handler._assess_fuel_status(75.0) == "good"
        assert handler._assess_fuel_status(30.0) == "moderate"
        assert handler._assess_fuel_status(15.0) == "low"
        assert handler._assess_fuel_status(5.0) == "critical"

    def test_equipment_status_summary(self) -> None:
        """Test equipment status summary generation."""
        profile = AgriculturalEquipmentProfile(
            equipment_id="TRACTOR_001",
            equipment_type=AgriculturalEquipmentType.TRACTOR,
            manufacturer="John Deere",
            model="6M Series",
            serial_number="JD6M001234",
            can_address=0x23,
            function_code=0x00,
            capabilities=[],
        )

        config = AgriculturalCANConfig(equipment_profile=profile)
        handler = AgriculturalProtocolHandler(config)

        # Process some messages to populate data
        rpm_data = bytes([0x00, 0x00, 0x40, 0x00])
        engine_message = can.Message(
            arbitration_id=0x18EEDF23,
            data=rpm_data + b"\x00\x00\x00\x00",
            is_extended_id=True,
            timestamp=time.time(),
        )

        # Async processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(handler.process_agricultural_message(engine_message))
        finally:
            loop.close()

        status = handler.get_equipment_status()

        assert "equipment_id" in status
        assert "equipment_type" in status
        assert "operation_mode" in status
        assert "engine_data" in status
        assert "position_data" in status
        assert "implement_status" in status
        assert "safety_status" in status
        assert "message_statistics" in status

        assert status["equipment_id"] == "TRACTOR_001"
        assert status["operation_mode"] == "working"

    def test_agricultural_summary_generation(self) -> None:
        """Test agricultural operation summary generation."""
        profile = AgriculturalEquipmentProfile(
            equipment_id="TRACTOR_001",
            equipment_type=AgriculturalEquipmentType.TRACTOR,
            manufacturer="John Deere",
            model="6M Series",
            serial_number="JD6M001234",
            can_address=0x23,
            function_code=0x00,
            capabilities=[],
        )

        config = AgriculturalCANConfig(equipment_profile=profile)
        handler = AgriculturalProtocolHandler(config)

        summary = handler.get_agricultural_summary()

        assert "operation_summary" in summary
        assert "performance_metrics" in summary
        assert "equipment_health" in summary
        assert "agricultural_recommendations" in summary

        # Should have operation summary
        assert "mode" in summary["operation_summary"]
        assert "field_operations" in summary["operation_summary"]
        assert "active_tasks" in summary["operation_summary"]

        # Should have performance metrics
        assert "message_success_rate" in summary["performance_metrics"]
        assert "total_messages_processed" in summary["performance_metrics"]

        # Should have equipment health assessment
        assert "engine" in summary["equipment_health"]
        assert "fuel" in summary["equipment_health"]
        assert "gps" in summary["equipment_health"]
        assert "overall" in summary["equipment_health"]

        # Should have recommendations
        assert isinstance(summary["agricultural_recommendations"], list)


class TestAgriculturalCANBusManager:
    """Test agricultural CAN bus manager for multi-equipment operations."""

    def test_manager_initialization(self) -> None:
        """Test manager initialization with multiple equipment."""
        profiles = [
            AgriculturalEquipmentProfile(
                equipment_id="TRACTOR_001",
                equipment_type=AgriculturalEquipmentType.TRACTOR,
                manufacturer="John Deere",
                model="6M Series",
                serial_number="JD6M001234",
                can_address=0x23,
                function_code=0x00,
                capabilities=[],
            ),
            AgriculturalEquipmentProfile(
                equipment_id="PLANTER_001",
                equipment_type=AgriculturalEquipmentType.PLANTER,
                manufacturer="Kincaid",
                model="Air Seeder",
                serial_number="KS001234",
                can_address=0x24,
                function_code=0x03,
                capabilities=[],
            ),
        ]

        manager = AgriculturalCANBusManager(profiles)

        assert len(manager.equipment_profiles) == 2
        assert len(manager.protocol_handlers) == 2
        assert "TRACTOR_001" in manager.protocol_handlers
        assert "PLANTER_001" in manager.protocol_handlers
        assert manager.system_status == "initialized"

    @pytest.mark.asyncio
    async def test_message_routing(self) -> None:
        """Test message routing to correct equipment."""
        profiles = [
            AgriculturalEquipmentProfile(
                equipment_id="TRACTOR_001",
                equipment_type=AgriculturalEquipmentType.TRACTOR,
                manufacturer="John Deere",
                model="6M Series",
                serial_number="JD6M001234",
                can_address=0x23,
                function_code=0x00,
                capabilities=[],
            ),
            AgriculturalEquipmentProfile(
                equipment_id="PLANTER_001",
                equipment_type=AgriculturalEquipmentType.PLANTER,
                manufacturer="Kincaid",
                model="Air Seeder",
                serial_number="KS001234",
                can_address=0x24,
                function_code=0x03,
                capabilities=[],
            ),
        ]

        manager = AgriculturalCANBusManager(profiles)

        # Create message for tractor
        rpm_data = bytes([0x00, 0x00, 0x40, 0x00])
        tractor_message = can.Message(
            arbitration_id=0x18EEDF23,  # Tractor address
            data=rpm_data + b"\x00\x00\x00\x00",
            is_extended_id=True,
            timestamp=time.time(),
        )

        results = await manager.process_message(tractor_message)

        assert "TRACTOR_001" in results
        assert "PLANTER_001" not in results  # Should not receive this message
        assert isinstance(results["TRACTOR_001"], AgriculturalCANMessage)

    def test_equipment_address_mapping(self) -> None:
        """Test equipment address mapping functionality."""
        profiles = [
            AgriculturalEquipmentProfile(
                equipment_id="TRACTOR_001",
                equipment_type=AgriculturalEquipmentType.TRACTOR,
                manufacturer="John Deere",
                model="6M Series",
                serial_number="JD6M001234",
                can_address=0x23,
                function_code=0x00,
                capabilities=[],
            ),
            AgriculturalEquipmentProfile(
                equipment_id="IMPLEMENT_001",
                equipment_type=AgriculturalEquipmentType.TILLAGE,
                manufacturer="Great Plains",
                model="Disc Harrow",
                serial_number="GP001234",
                can_address=0x35,
                function_code=0x01,
                capabilities=[],
            ),
        ]

        manager = AgriculturalCANBusManager(profiles)

        # Test address to equipment ID mapping
        assert manager._find_equipment_by_address(0x23) == "TRACTOR_001"
        assert manager._find_equipment_by_address(0x35) == "IMPLEMENT_001"
        assert manager._find_equipment_by_address(0xFF) is None  # Unknown address

    def test_system_summary(self) -> None:
        """Test complete system summary generation."""
        profiles = [
            AgriculturalEquipmentProfile(
                equipment_id="TRACTOR_001",
                equipment_type=AgriculturalEquipmentType.TRACTOR,
                manufacturer="John Deere",
                model="6M Series",
                serial_number="JD6M001234",
                can_address=0x23,
                function_code=0x00,
                capabilities=[],
            ),
        ]

        manager = AgriculturalCANBusManager(profiles)

        summary = manager.get_system_summary()

        assert "system_status" in summary
        assert "uptime" in summary
        assert "equipment_count" in summary
        assert "active_equipment" in summary
        assert "equipment_summaries" in summary
        assert "overall_system_health" in summary
        assert "agricultural_operations_overview" in summary

        assert summary["equipment_count"] == 1
        assert summary["active_equipment"] == 1
        assert "TRACTOR_001" in summary["equipment_summaries"]

    def test_agricultural_operations_overview(self) -> None:
        """Test agricultural operations overview generation."""
        profiles = [
            AgriculturalEquipmentProfile(
                equipment_id="TRACTOR_001",
                equipment_type=AgriculturalEquipmentType.TRACTOR,
                manufacturer="John Deere",
                model="6M Series",
                serial_number="JD6M001234",
                can_address=0x23,
                function_code=0x00,
                capabilities=[],
            ),
            AgriculturalEquipmentProfile(
                equipment_id="IRRIGATION_001",
                equipment_type=AgriculturalEquipmentType.IRRIGATION,
                manufacturer="Valmont",
                model="Linear Move",
                serial_number="VM001234",
                can_address=0x26,
                function_code=0x09,
                capabilities=[],
            ),
        ]

        manager = AgriculturalCANBusManager(profiles)

        overview = manager._get_agricultural_overview()

        assert "active_operations" in overview
        assert "safety_alerts" in overview
        assert "total_field_operations" in overview

        # Should be lists
        assert isinstance(overview["active_operations"], list)
        assert isinstance(overview["safety_alerts"], list)
        assert isinstance(overview["total_field_operations"], int)


class TestIntegrationScenarios:
    """Test integration scenarios for agricultural CAN operations."""

    @pytest.mark.asyncio
    async def test_multi_equipment_field_operation(self) -> None:
        """Test multi-equipment field operations coordination."""
        # Create multiple equipment profiles
        profiles = [
            AgriculturalEquipmentProfile(
                equipment_id="TRACTOR_001",
                equipment_type=AgriculturalEquipmentType.TRACTOR,
                manufacturer="John Deere",
                model="6M Series",
                serial_number="JD6M001234",
                can_address=0x23,
                function_code=0x00,
                capabilities=[],
            ),
            AgriculturalEquipmentProfile(
                equipment_id="PLANTER_001",
                equipment_type=AgriculturalEquipmentType.PLANTER,
                manufacturer="Kincaid",
                model="Air Seeder",
                serial_number="KS001234",
                can_address=0x24,
                function_code=0x03,
                capabilities=[],
            ),
            AgriculturalEquipmentProfile(
                equipment_id="IRRIGATION_001",
                equipment_type=AgriculturalEquipmentType.IRRIGATION,
                manufacturer="Valmont",
                model="Linear Move",
                serial_number="VM001234",
                can_address=0x26,
                function_code=0x09,
                capabilities=[],
            ),
        ]

        manager = AgriculturalCANBusManager(profiles)

        # Simulate field operations
        operations = [
            (0x23, 0x18EEDF23, b"\x00\x00\x40\x00\x00\x00\x00\x00"),  # Tractor engine data
            (0x24, 0x18EEDF24, b"\x00\x00\x20\x00\x00\x00\x00\x00"),  # Planter speed data
            (0x26, 0x18FEDF26, b"\x00\x64\x00\x00\x00\x00\x00\x00"),  # Irrigation fuel level
        ]

        results = []
        for _address, arbitration_id, data in operations:
            message = can.Message(
                arbitration_id=arbitration_id,
                data=data,
                is_extended_id=True,
                timestamp=time.time(),
            )
            result = await manager.process_message(message)
            results.append(result)

        # Verify all equipment processed messages
        assert len(results) == 3
        for result in results:
            assert len(result) == 1  # Each should have one equipment result

        # Check system overview
        overview = manager._get_agricultural_overview()
        assert overview["total_field_operations"] >= 0

    @pytest.mark.asyncio
    async def test_safety_critical_scenario(self) -> None:
        """Test safety-critical scenario with multiple equipment."""
        profiles = [
            AgriculturalEquipmentProfile(
                equipment_id="TRACTOR_001",
                equipment_type=AgriculturalEquipmentType.TRACTOR,
                manufacturer="John Deere",
                model="6M Series",
                serial_number="JD6M001234",
                can_address=0x23,
                function_code=0x00,
                capabilities=[],
            ),
            AgriculturalEquipmentProfile(
                equipment_id="HARVESTER_001",
                equipment_type=AgriculturalEquipmentType.HARVESTER,
                manufacturer="Case IH",
                model="Combine",
                serial_number="CI001234",
                can_address=0x25,
                function_code=0x06,
                capabilities=[],
            ),
        ]

        manager = AgriculturalCANBusManager(profiles)

        # Send emergency stop message
        emergency_message = can.Message(
            arbitration_id=0x00EEDF23,  # Emergency Stop
            data=b"\x00\x00\x00\x00\x00\x00\x00\x00",
            is_extended_id=True,
            timestamp=time.time(),
        )

        results = await manager.process_message(emergency_message)

        # Should process for tractor
        assert "TRACTOR_001" in results
        tractor_result = results["TRACTOR_001"]
        assert isinstance(tractor_result, AgriculturalCANMessage)

        # Check equipment status after emergency
        status = manager.protocol_handlers["TRACTOR_001"].get_equipment_status()
        assert status["operation_mode"] == "emergency"

    @pytest.mark.asyncio
    async def test_precision_agriculation_scenario(self) -> None:
        """Test precision agriculture scenario with GPS and guidance."""
        profile = AgriculturalEquipmentProfile(
            equipment_id="TRACTOR_001",
            equipment_type=AgriculturalEquipmentType.TRACTOR,
            manufacturer="John Deere",
            model="6M Series",
            serial_number="JD6M001234",
            can_address=0x23,
            function_code=0x00,
            capabilities=["precision_guidance", "auto_steering"],
        )

        config = AgriculturalCANConfig(equipment_profile=profile)
        handler = AgriculturalProtocolHandler(config)

        # Process GPS data for precision agriculture
        lat = int(40.7128 * 1e7)  # Field position
        lon = int(-74.0060 * 1e7)
        # Handle negative longitude by using signed int representation
        gps_data = struct.pack("<ii", lat, lon)
        gps_message = can.Message(
            arbitration_id=0x18FEDF23,
            data=gps_data,
            is_extended_id=True,
            timestamp=time.time(),
        )

        await handler.process_agricultural_message(gps_message)

        # Should update position data and field operations
        assert "latitude" in handler.position_data
        assert "longitude" in handler.position_data
        assert "current_field" in handler.field_operations
        assert handler.position_data["accuracy"] == "high"

        # Get agricultural summary
        summary = handler.get_agricultural_summary()
        assert summary["equipment_health"]["gps"] == "good"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
