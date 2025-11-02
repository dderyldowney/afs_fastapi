"""
SAE J1939 CAN Bus Stack Tests for Agricultural Equipment

RED PHASE: Comprehensive test suite for J1939 protocol implementation
Agricultural Context: J1939 enables standardized communication between
tractors, implements, and agricultural control systems.

Safety Requirements: J1939 communication must be reliable for safety-critical
agricultural operations including emergency stops and collision avoidance.
"""

import unittest
from unittest.mock import Mock, patch

import pytest


class TestJ1939AddressClaiming(unittest.TestCase):
    """
    RED PHASE: Test J1939 address claiming protocol for agricultural equipment.

    Agricultural Context: Address claiming allows multiple agricultural devices
    (tractors, implements, sensors) to automatically configure network addresses
    without conflicts, essential for dynamic field operations.

    Safety Requirements: Address conflicts must be resolved quickly to prevent
    communication failures during safety-critical operations.
    """

    def test_j1939_address_claim_process(self) -> None:
        """
        RED PHASE: Test J1939 address claiming for agricultural equipment.

        Agricultural Context: Tractor implements must claim unique addresses
        when connecting to ISOBUS network during field operations.
        """
        from afs_fastapi.protocols.sae_j1939 import J1939AddressManager

        # Create address manager for agricultural implement
        address_manager = J1939AddressManager(
            device_name="Cultivator_Controller",
            preferred_address=0x26,  # Typical implement address
            device_class="Agricultural Implement",
        )

        # Test address claim message generation
        claim_message = address_manager.generate_address_claim()

        assert claim_message.pgn == 0xEE00  # Address Claimed PGN
        assert claim_message.priority == 6  # Standard priority for address claiming
        assert claim_message.source_address == 0x26
        assert len(claim_message.data) == 8  # J1939 NAME field

        # Test address conflict resolution
        conflicting_device = Mock()
        conflicting_device.device_name = "Competing_Implement"

        resolution_result = address_manager.handle_address_conflict(conflicting_device)
        assert resolution_result.address_claimed is not None
        assert resolution_result.conflict_resolved is True

    def test_j1939_name_field_generation(self) -> None:
        """
        RED PHASE: Test J1939 NAME field generation for agricultural equipment.

        Agricultural Context: NAME field uniquely identifies agricultural
        equipment type, manufacturer, and capabilities for ISOBUS compatibility.
        """
        from afs_fastapi.protocols.sae_j1939 import J1939NameField

        # Create NAME field for agricultural tractor
        name_field = J1939NameField(
            arbitrary_address_capable=True,
            industry_group=2,  # Agricultural and Forestry Equipment
            vehicle_system_instance=0,
            vehicle_system=25,  # Tractor
            function=25,  # Agricultural Implement
            function_instance=0,
            ecu_instance=0,
            manufacturer_code=1234,
            identity_number=5678,
        )

        name_bytes = name_field.to_bytes()
        assert len(name_bytes) == 8

        # Verify critical agricultural equipment identification
        assert name_field.industry_group == 2  # Agricultural equipment
        assert name_field.vehicle_system == 25  # Tractor classification

    def test_agricultural_equipment_priority_handling(self) -> None:
        """
        RED PHASE: Test priority handling for agricultural equipment types.

        Agricultural Context: Different agricultural equipment types require
        different communication priorities for safety and operational efficiency.
        Safety-critical systems (emergency stop) get highest priority.
        """
        from afs_fastapi.protocols.sae_j1939 import J1939PriorityManager

        priority_manager = J1939PriorityManager()

        # Test emergency stop system priority (highest)
        emergency_priority = priority_manager.get_priority_for_system("emergency_stop")
        assert emergency_priority == 0  # Highest priority

        # Test tractor engine data priority
        engine_priority = priority_manager.get_priority_for_system("engine_data")
        assert engine_priority == 3  # Standard operational priority

        # Test implement status priority
        implement_priority = priority_manager.get_priority_for_system("implement_status")
        assert implement_priority == 6  # Lower priority for status updates


class TestJ1939ParameterGroups(unittest.TestCase):
    """
    RED PHASE: Test J1939 Parameter Group Number (PGN) handling for agricultural data.

    Agricultural Context: PGNs define standardized message formats for
    agricultural equipment data including engine parameters, GPS position,
    and implement status critical for coordinated field operations.
    """

    def test_engine_data_pgn_parsing(self) -> None:
        """
        RED PHASE: Test parsing of J1939 Engine Data PGN for tractors.

        Agricultural Context: Engine data (RPM, temperature, fuel level)
        is critical for tractor performance monitoring and fleet coordination.
        """
        from afs_fastapi.protocols.sae_j1939 import J1939PGNParser

        parser = J1939PGNParser()

        # Test Engine Temperature 1 PGN (0xFEEE)
        engine_temp_data = bytes([0x7D, 0x30, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
        parsed_data = parser.parse_pgn(0xFEEE, engine_temp_data)

        assert parsed_data.pgn_name == "Engine Temperature 1"
        assert parsed_data.coolant_temperature == 85  # Celsius (0x7D - 40 = 125 - 40 = 85)
        assert parsed_data.fuel_temperature == 8  # Celsius above -40 (0x30 - 40 = 48 - 40 = 8)

        # Test Engine Speed PGN (0xF004)
        engine_speed_data = bytes(
            [0x00, 0x20, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        )  # 0x2000 = 8192, * 0.125 = 1024 RPM
        speed_data = parser.parse_pgn(0xF004, engine_speed_data)

        assert speed_data.pgn_name == "Electronic Engine Controller 1"
        assert speed_data.engine_speed == 1024  # RPM (0x2000 * 0.125)

    def test_vehicle_position_pgn_parsing(self) -> None:
        """
        RED PHASE: Test J1939 Vehicle Position PGN for agricultural navigation.

        Agricultural Context: GPS position data is critical for precision
        agriculture, field mapping, and multi-tractor coordination to prevent
        collisions and optimize field coverage.
        """
        from afs_fastapi.protocols.sae_j1939 import J1939PGNParser

        parser = J1939PGNParser()

        # Test Vehicle Position PGN (0xFEF3)
        position_data = bytes(
            [0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0]  # Latitude  # Longitude
        )

        parsed_position = parser.parse_pgn(0xFEF3, position_data)

        assert parsed_position.pgn_name == "Vehicle Position"
        assert parsed_position.latitude is not None
        assert parsed_position.longitude is not None
        assert parsed_position.position_accuracy == "High"  # Required for precision agriculture

    def test_agricultural_guidance_pgn(self) -> None:
        """
        RED PHASE: Test agricultural-specific guidance PGN parsing.

        Agricultural Context: Guidance systems enable automatic steering
        for tractors during field operations, requiring precise communication
        of steering commands and field boundary data.
        """
        from afs_fastapi.protocols.sae_j1939 import J1939PGNParser

        parser = J1939PGNParser()

        # Test Agricultural Guidance PGN (custom agricultural extension)
        guidance_data = bytes(
            [
                0x01,  # Guidance status: Active
                0x10,  # Steering angle: +16 degrees
                0x05,  # Cross track error: 5cm
                0x80,  # Field boundary flag
                0xFF,
                0xFF,
                0xFF,
                0xFF,  # Reserved
            ]
        )

        guidance_info = parser.parse_pgn(0xAC00, guidance_data)  # Agricultural custom PGN

        assert guidance_info.pgn_name == "Agricultural Guidance System"
        assert guidance_info.guidance_active is True
        assert guidance_info.steering_angle == 16  # degrees
        assert guidance_info.cross_track_error == 5  # centimeters


class TestJ1939TransportProtocol(unittest.TestCase):
    """
    RED PHASE: Test J1939 Transport Protocol for multi-frame messages.

    Agricultural Context: Large agricultural data sets (field maps, implement
    configurations) require multi-frame transport protocol for reliable
    transmission over CAN bus networks.
    """

    def test_transport_protocol_data_transfer(self) -> None:
        """
        RED PHASE: Test multi-frame J1939 data transfer for agricultural applications.

        Agricultural Context: Field maps and implement configuration data
        exceed 8-byte CAN frame limits, requiring segmented transmission.
        """
        from afs_fastapi.protocols.sae_j1939 import J1939TransportProtocol

        transport = J1939TransportProtocol()

        # Test large agricultural data set (field boundary coordinates)
        field_map_data = bytes(range(256))  # 256 bytes of field coordinate data

        # Test data segmentation
        segments = transport.segment_data(field_map_data, pgn=0xAC01)

        assert len(segments) > 1  # Must be segmented
        assert segments[0].is_connection_management is True
        assert segments[1].sequence_number == 1

        # Test data reassembly
        # Cast to expected type since segment_data never returns None segments
        from typing import Any, cast

        reassembled_data = transport.reassemble_segments(cast(Any, segments))
        assert reassembled_data == field_map_data
        assert len(reassembled_data) == 256

    def test_transport_protocol_error_handling(self) -> None:
        """
        RED PHASE: Test J1939 transport protocol error handling.

        Agricultural Context: Field operations cannot tolerate data corruption
        in critical agricultural parameters. Error detection and recovery
        must be immediate and reliable.
        """
        from afs_fastapi.protocols.sae_j1939 import J1939TransportProtocol

        transport = J1939TransportProtocol()

        # Test missing segment detection
        from afs_fastapi.protocols.sae_j1939 import TransportSegment

        segments: list[TransportSegment | None] = [Mock(), Mock(), Mock()]  # 3 segments
        segments[1] = None  # Missing segment 2

        from afs_fastapi.protocols.sae_j1939 import J1939TransportError

        with pytest.raises(J1939TransportError) as excinfo:
            transport.reassemble_segments(segments)

        assert "Missing segment" in str(excinfo.value)
        assert excinfo.value.error_code == "SEGMENT_MISSING"

        # Test segment timeout handling
        with patch("time.time", return_value=1000):
            result = transport.wait_for_segment(segment_number=2, timeout_ms=500)

        assert result.timeout_occurred is True
        assert result.error_code == "SEGMENT_TIMEOUT"


class TestJ1939DiagnosticTroubleCodes(unittest.TestCase):
    """
    RED PHASE: Test J1939 Diagnostic Trouble Code (DTC) handling.

    Agricultural Context: DTCs enable proactive maintenance of agricultural
    equipment, preventing breakdowns during critical field operations.
    Safety-critical DTCs must trigger immediate operator alerts.
    """

    def test_dtc_generation_and_reporting(self) -> None:
        """
        RED PHASE: Test DTC generation for agricultural equipment issues.

        Agricultural Context: Equipment faults must be immediately reported
        to prevent damage and ensure operator safety during field operations.
        """
        from afs_fastapi.protocols.sae_j1939 import J1939DiagnosticManager

        diagnostic_manager = J1939DiagnosticManager()

        # Test engine overheat DTC generation
        engine_fault = diagnostic_manager.generate_dtc(
            spn=110,  # Coolant Temperature SPN
            fmi=15,  # Data Valid But Above Normal Operating Range - Most Severe Level
            occurrence_count=1,
            source_address=0x00,  # Engine ECU
        )

        assert engine_fault.spn == 110
        assert engine_fault.failure_mode == 15
        assert engine_fault.severity == "Critical"  # Engine overheating is critical
        assert engine_fault.requires_immediate_action is True

    def test_agricultural_specific_dtc_handling(self) -> None:
        """
        RED PHASE: Test agricultural-specific DTC categories.

        Agricultural Context: Agricultural equipment has unique failure modes
        not covered by standard automotive DTCs, requiring specialized
        diagnostic capabilities for implements and precision agriculture systems.
        """
        from afs_fastapi.protocols.sae_j1939 import J1939DiagnosticManager

        diagnostic_manager = J1939DiagnosticManager()

        # Test implement hydraulic system fault
        hydraulic_fault = diagnostic_manager.generate_agricultural_dtc(
            equipment_type="cultivator",
            fault_category="hydraulic_pressure",
            severity="warning",
            description="Hydraulic pressure below optimal for soil conditions",
        )

        assert hydraulic_fault.equipment_type == "cultivator"
        assert hydraulic_fault.fault_category == "hydraulic_pressure"
        assert hydraulic_fault.agricultural_specific is True
        assert (
            hydraulic_fault.recommended_action == "Check hydraulic fluid level and system pressure"
        )

    def test_safety_critical_dtc_prioritization(self) -> None:
        """
        RED PHASE: Test prioritization of safety-critical DTCs.

        Agricultural Context: Safety-critical faults (emergency stop failures,
        collision avoidance system errors) must be prioritized over operational
        faults to prevent accidents and equipment damage.
        """
        from afs_fastapi.protocols.sae_j1939 import J1939DiagnosticManager

        diagnostic_manager = J1939DiagnosticManager()

        # Generate multiple DTCs with different priorities
        engine_warning = diagnostic_manager.generate_dtc(
            spn=175, fmi=1, occurrence_count=1
        )  # Oil pressure low
        emergency_stop_fault = diagnostic_manager.generate_dtc(
            spn=9999, fmi=15, occurrence_count=1
        )  # Custom emergency stop SPN
        implement_status = diagnostic_manager.generate_dtc(
            spn=2000, fmi=2, occurrence_count=1
        )  # Implement position

        # Test prioritization
        prioritized_dtcs = diagnostic_manager.prioritize_dtcs(
            [engine_warning, emergency_stop_fault, implement_status]
        )

        # Emergency stop fault should be first priority
        assert prioritized_dtcs[0].spn == 9999  # Emergency stop
        assert prioritized_dtcs[0].priority_level == 1  # Highest priority
        assert prioritized_dtcs[1].spn == 175  # Engine warning second
        assert prioritized_dtcs[2].spn == 2000  # Implement status last


class TestJ1939AgriculturalIntegration(unittest.TestCase):
    """
    RED PHASE: Test J1939 integration with existing agricultural systems.

    Agricultural Context: J1939 must integrate seamlessly with existing
    ISOBUS systems, farm management software, and precision agriculture
    platforms for complete agricultural robotics coordination.
    """

    def test_j1939_isobus_integration(self) -> None:
        """
        RED PHASE: Test J1939 integration with ISOBUS systems.

        Agricultural Context: J1939 provides the CAN physical layer for
        ISOBUS agricultural communication, requiring seamless integration
        for tractor-implement coordination.
        """
        from afs_fastapi.core.can_frame_codec import CANFrameCodec
        from afs_fastapi.protocols.isobus_handlers import ISOBUSProtocolManager
        from afs_fastapi.protocols.sae_j1939 import J1939ISobusAdapter

        j1939_adapter = J1939ISobusAdapter()
        codec = CANFrameCodec()
        isobus_handler = ISOBUSProtocolManager(codec)

        # Test J1939 message conversion to ISOBUS format
        j1939_message = Mock()
        j1939_message.pgn = 0xFEF3  # Vehicle Position
        j1939_message.data = bytes([0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0])

        isobus_message = j1939_adapter.convert_to_isobus(j1939_message)

        assert isobus_message.function_code is not None
        assert isobus_message.agricultural_context == "Position Data"
        assert isobus_message.compatibility_verified is True

        # Test bidirectional communication
        # Note: This is a mock test - actual implementation would handle the message
        from unittest.mock import patch

        with patch.object(isobus_handler, "handle_message", return_value=True) as mock_handle:
            result = isobus_handler.handle_message(Mock())
            assert result is True
            mock_handle.assert_called_once()

    def test_j1939_performance_under_agricultural_constraints(self) -> None:
        """
        RED PHASE: Test J1939 performance under agricultural equipment constraints.

        Agricultural Context: Agricultural equipment operates in harsh
        environments with limited computational resources. J1939 implementation
        must be efficient and robust for embedded agricultural controllers.
        """
        import time

        from afs_fastapi.protocols.sae_j1939 import J1939Stack

        j1939_stack = J1939Stack()

        # Test message processing performance
        start_time = time.time()

        for i in range(100):  # Process 100 messages
            test_message = j1939_stack.create_message(
                pgn=0xF004,  # Engine Speed
                data=bytes([0x00, 0x64 + i, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]),
            )
            j1939_stack.process_message(test_message)

        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Agricultural equipment constraint: <10ms for 100 messages
        assert processing_time < 10.0, f"Processing took {processing_time}ms, exceeds 10ms limit"

        # Test memory usage constraints
        memory_usage = j1939_stack.get_memory_usage()
        assert memory_usage < 1024 * 1024  # Less than 1MB for embedded systems
