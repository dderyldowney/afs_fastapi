"""
Test suite for ISOBUS protocol handlers.

Tests comprehensive ISOBUS (ISO 11783) protocol implementations including
Address Claim, Transport Protocol, Diagnostic protocols, and integrated
protocol management for precision agriculture systems.
"""

from __future__ import annotations

import struct
from datetime import datetime, timedelta

import can
import pytest

from afs_fastapi.core.can_frame_codec import CANFrameCodec
from afs_fastapi.equipment.can_error_handling import CANErrorHandler
from afs_fastapi.protocols.isobus_handlers import (
    AddressClaimHandler,
    DiagnosticHandler,
    DiagnosticTroubleCode,
    ISOBUSDevice,
    ISOBUSFunction,
    ISOBUSProtocolManager,
    TPControl,
    TPSession,
    TransportProtocolHandler,
)


class TestAddressClaimHandler:
    """Test ISOBUS address claim functionality."""

    @pytest.fixture
    def codec(self) -> CANFrameCodec:
        """Create CAN frame codec."""
        return CANFrameCodec()

    @pytest.fixture
    def error_handler(self) -> CANErrorHandler:
        """Create error handler."""
        return CANErrorHandler()

    @pytest.fixture
    def address_claim_handler(
        self,
        codec: CANFrameCodec,
        error_handler: CANErrorHandler,
    ) -> AddressClaimHandler:
        """Create address claim handler."""
        return AddressClaimHandler(codec, error_handler)

    def test_handler_initialization(self, address_claim_handler: AddressClaimHandler) -> None:
        """Test address claim handler initialization."""
        assert len(address_claim_handler.claimed_addresses) == 0
        assert len(address_claim_handler.pending_claims) == 0
        assert len(address_claim_handler.address_conflicts) == 0

    def test_handle_tractor_address_claim(self, address_claim_handler: AddressClaimHandler) -> None:
        """Test handling tractor address claim message."""
        # Create tractor address claim message
        # NAME field: Identity=12345, Manufacturer=123, Function=TRACTOR, etc.
        name_data = bytearray(8)

        # Identity number (21 bits): 12345
        identity_number = 12345  # Explicitly define identity_number for clarity in this section
        identity_bytes = struct.pack("<I", identity_number)
        name_data[0:3] = identity_bytes[0:3]

        # Manufacturer code (11 bits) at bits 21-31: 123
        # The manufacturer code is part of the 16-bit field spanning name_data[3] and name_data[4].
        # It occupies bits 5-15 of this 16-bit field.
        # The lower 5 bits (0-4) of this 16-bit field are part of the identity number.
        manufacturer_and_identity = (123 << 5) | ((identity_number >> 16) & 0x1F)
        packed_manufacturer = struct.pack("<H", manufacturer_and_identity)
        name_data[3] = packed_manufacturer[0]
        name_data[4] = packed_manufacturer[1]

        # Function: TRACTOR (0)
        name_data[5] = ISOBUSFunction.TRACTOR.value

        # Device class: 0
        name_data[6] = 0x00

        # Industry group and arbitrary address capability
        name_data[7] = 0x80  # Arbitrary address capable

        message = can.Message(
            arbitration_id=0x18EEFF00,  # Address claim from address 0x00
            data=bytes(name_data),
            is_extended_id=True,
        )

        device = address_claim_handler.handle_address_claim(message)

        assert device is not None
        assert device.address == 0x00
        assert device.function == ISOBUSFunction.TRACTOR
        assert device.identity_number == 12345
        assert device.manufacturer_code == 123

        # Verify device is stored
        assert 0x00 in address_claim_handler.claimed_addresses
        stored_device = address_claim_handler.claimed_addresses[0x00]
        assert stored_device.identity_number == 12345

    def test_handle_address_conflict(self, address_claim_handler: AddressClaimHandler) -> None:
        """Test handling address conflicts."""
        # First device claims address
        name_data1 = bytearray(8)
        struct.pack_into("<I", name_data1, 0, 11111)  # Identity 11111
        name_data1[5] = ISOBUSFunction.TRACTOR.value

        message1 = can.Message(
            arbitration_id=0x18EEFF25,  # Address 0x25
            data=bytes(name_data1),
            is_extended_id=True,
        )

        device1 = address_claim_handler.handle_address_claim(message1)
        assert device1 is not None
        assert device1.address == 0x25

        # Second device tries to claim same address with different identity
        name_data2 = bytearray(8)
        struct.pack_into("<I", name_data2, 0, 22222)  # Different identity
        name_data2[5] = ISOBUSFunction.SPRAYERS.value

        message2 = can.Message(
            arbitration_id=0x18EEFF25,  # Same address 0x25
            data=bytes(name_data2),
            is_extended_id=True,
        )

        device2 = address_claim_handler.handle_address_claim(message2)
        assert device2 is None  # Should reject due to conflict

        # Verify conflict recorded
        assert len(address_claim_handler.address_conflicts) == 1
        assert address_claim_handler.address_conflicts[0][0] == 0x25

    def test_create_address_claim_message(self, address_claim_handler: AddressClaimHandler) -> None:
        """Test creating address claim message."""
        device = ISOBUSDevice(
            name="Test Tractor",
            address=0x25,
            function=ISOBUSFunction.TRACTOR,
            manufacturer_code=456,
            device_class=0,
            device_class_instance=0,
            ecu_instance=0,
            identity_number=54321,
            preferred_address=0x25,
        )

        message = address_claim_handler.create_address_claim_message(device)

        assert message.arbitration_id == 0x18EEFF25
        assert message.is_extended_id is True
        assert len(message.data) == 8

        # Verify NAME field construction
        identity = struct.unpack("<I", message.data[0:4])[0] & 0x1FFFFF
        assert identity == 54321

        assert message.data[5] == ISOBUSFunction.TRACTOR.value

    def test_get_devices_by_function(self, address_claim_handler: AddressClaimHandler) -> None:
        """Test retrieving devices by function."""
        # Add tractor device
        tractor_device = ISOBUSDevice(
            name="Tractor",
            address=0x00,
            function=ISOBUSFunction.TRACTOR,
            manufacturer_code=100,
            device_class=0,
            device_class_instance=0,
            ecu_instance=0,
            identity_number=1000,
            preferred_address=0x00,
        )
        address_claim_handler.claimed_addresses[0x00] = tractor_device

        # Add sprayer device
        sprayer_device = ISOBUSDevice(
            name="Sprayer",
            address=0x01,
            function=ISOBUSFunction.SPRAYERS,
            manufacturer_code=200,
            device_class=0,
            device_class_instance=0,
            ecu_instance=0,
            identity_number=2000,
            preferred_address=0x01,
        )
        address_claim_handler.claimed_addresses[0x01] = sprayer_device

        # Test function filtering
        tractors = address_claim_handler.get_devices_by_function(ISOBUSFunction.TRACTOR)
        assert len(tractors) == 1
        assert tractors[0].function == ISOBUSFunction.TRACTOR

        sprayers = address_claim_handler.get_devices_by_function(ISOBUSFunction.SPRAYERS)
        assert len(sprayers) == 1
        assert sprayers[0].function == ISOBUSFunction.SPRAYERS

        harvesters = address_claim_handler.get_devices_by_function(ISOBUSFunction.HARVESTERS)
        assert len(harvesters) == 0

    def test_address_claim_callbacks(self, address_claim_handler: AddressClaimHandler) -> None:
        """Test address claim event callbacks."""
        callback_calls = []

        def test_callback(device: ISOBUSDevice) -> None:
            callback_calls.append(device)

        address_claim_handler.add_claim_callback(test_callback)

        # Trigger address claim
        name_data = bytearray(8)
        struct.pack_into("<I", name_data, 0, 99999)
        name_data[5] = ISOBUSFunction.PLANTERS_SEEDERS.value

        message = can.Message(
            arbitration_id=0x18EEFF30,
            data=bytes(name_data),
            is_extended_id=True,
        )

        device = address_claim_handler.handle_address_claim(message)

        assert len(callback_calls) == 1
        assert callback_calls[0] == device


class TestTransportProtocolHandler:
    """Test ISOBUS Transport Protocol functionality."""

    @pytest.fixture
    def codec(self) -> CANFrameCodec:
        """Create CAN frame codec."""
        return CANFrameCodec()

    @pytest.fixture
    def error_handler(self) -> CANErrorHandler:
        """Create error handler."""
        return CANErrorHandler()

    @pytest.fixture
    def tp_handler(
        self,
        codec: CANFrameCodec,
        error_handler: CANErrorHandler,
    ) -> TransportProtocolHandler:
        """Create transport protocol handler."""
        return TransportProtocolHandler(codec, error_handler)

    def test_handler_initialization(self, tp_handler: TransportProtocolHandler) -> None:
        """Test transport protocol handler initialization."""
        assert len(tp_handler.active_sessions) == 0
        assert len(tp_handler.completed_messages) == 0

    def test_handle_rts_message(self, tp_handler: TransportProtocolHandler) -> None:
        """Test handling Request to Send message."""
        # Create RTS message
        # Control byte (RTS), total size (20 bytes), packets (3), max packets (3), PGN
        rts_data = bytearray(8)
        rts_data[0] = TPControl.RTS.value
        rts_data[1:3] = struct.pack("<H", 20)  # Total size
        rts_data[3] = 3  # Total packets
        rts_data[4] = 3  # Max packets per CTS
        rts_data[5:8] = struct.pack("<I", 0x1234)[0:3]  # PGN

        message = can.Message(
            arbitration_id=0x18EB2500,  # TP.CM from 0x00 to 0x25
            data=bytes(rts_data),
            is_extended_id=True,
        )

        session_id = tp_handler.handle_tp_cm_message(message)

        assert session_id is not None
        assert session_id in tp_handler.active_sessions

        session = tp_handler.active_sessions[session_id]
        assert session.pgn == 0x1234
        assert session.source_address == 0x00
        assert session.destination_address == 0x25
        assert session.total_size == 20
        assert session.total_packets == 3

    def test_handle_bam_message(self, tp_handler: TransportProtocolHandler) -> None:
        """Test handling Broadcast Announce Message."""
        # Create BAM message
        bam_data = bytearray(8)
        bam_data[0] = TPControl.BAM.value
        bam_data[1:3] = struct.pack("<H", 15)  # Total size
        bam_data[3] = 3  # Total packets
        bam_data[4] = 0xFF  # Reserved
        bam_data[5:8] = struct.pack("<I", 0x5678)[0:3]  # PGN

        message = can.Message(
            arbitration_id=0x18EBFF00,  # TP.CM broadcast from 0x00
            data=bytes(bam_data),
            is_extended_id=True,
        )

        session_id = tp_handler.handle_tp_cm_message(message)

        assert session_id is not None
        assert session_id.startswith("BAM_")

        session = tp_handler.active_sessions[session_id]
        assert session.is_bam is True
        assert session.pgn == 0x5678
        assert session.destination_address == 255

    def test_handle_data_transfer_complete_session(
        self, tp_handler: TransportProtocolHandler
    ) -> None:
        """Test handling data transfer messages to complete a session."""
        # First, create a session with RTS
        rts_data = bytearray(8)
        rts_data[0] = TPControl.RTS.value
        rts_data[1:3] = struct.pack("<H", 10)  # 10 bytes total
        rts_data[3] = 2  # 2 packets
        rts_data[4] = 2
        rts_data[5:8] = struct.pack("<I", 0xABCD)[0:3]

        rts_message = can.Message(
            arbitration_id=0x18EB2500,
            data=bytes(rts_data),
            is_extended_id=True,
        )

        session_id = tp_handler.handle_tp_cm_message(rts_message)
        assert session_id is not None

        # Track completed messages
        completed_messages = []

        def message_callback(pgn: int, data: bytes, source_address: int) -> None:
            completed_messages.append((pgn, data, source_address))

        tp_handler.add_message_callback(message_callback)

        # Send first data packet
        dt1_data = bytearray(8)
        dt1_data[0] = 1  # Sequence number
        dt1_data[1:8] = b"1234567"  # 7 bytes of data

        dt1_message = can.Message(
            arbitration_id=0x18EC2500,  # TP.DT from 0x00 to 0x25
            data=bytes(dt1_data),
            is_extended_id=True,
        )

        result1 = tp_handler.handle_tp_dt_message(dt1_message)
        assert result1 is None  # Not complete yet

        # Send second data packet
        dt2_data = bytearray(8)
        dt2_data[0] = 2  # Sequence number
        dt2_data[1:4] = b"890"  # 3 bytes to complete 10 total

        dt2_message = can.Message(
            arbitration_id=0x18EC2500,
            data=bytes(dt2_data),
            is_extended_id=True,
        )

        result2 = tp_handler.handle_tp_dt_message(dt2_message)
        assert result2 is not None  # Should be complete
        assert len(result2) == 10
        assert result2 == b"1234567890"

        # Verify callback was called
        assert len(completed_messages) == 1
        assert completed_messages[0][0] == 0xABCD  # PGN
        assert completed_messages[0][1] == b"1234567890"  # Data
        assert completed_messages[0][2] == 0x00  # Source address

        # Session should be cleaned up
        assert session_id not in tp_handler.active_sessions

    def test_handle_sequence_error(self, tp_handler: TransportProtocolHandler) -> None:
        """Test handling sequence number errors."""
        # Create session
        rts_data = bytearray(8)
        rts_data[0] = TPControl.RTS.value
        rts_data[1:3] = struct.pack("<H", 7)
        rts_data[3] = 1
        rts_data[4] = 1
        rts_data[5:8] = struct.pack("<I", 0x1111)[0:3]

        rts_message = can.Message(
            arbitration_id=0x18EB2500,
            data=bytes(rts_data),
            is_extended_id=True,
        )

        tp_handler.handle_tp_cm_message(rts_message)

        # Send packet with wrong sequence number
        dt_data = bytearray(8)
        dt_data[0] = 3  # Wrong sequence (should be 1)
        dt_data[1:8] = b"ABCDEFG"

        dt_message = can.Message(
            arbitration_id=0x18EC2500,
            data=bytes(dt_data),
            is_extended_id=True,
        )

        result = tp_handler.handle_tp_dt_message(dt_message)
        assert result is None  # Should reject due to sequence error

    @pytest.mark.asyncio
    async def test_session_cleanup(self, tp_handler: TransportProtocolHandler) -> None:
        """Test cleanup of expired sessions."""
        # Create a session
        session = TPSession(
            session_id="test_session",
            pgn=0x1234,
            source_address=0x00,
            destination_address=0x25,
            total_size=10,
            total_packets=2,
            max_packets=2,
            last_packet_time=datetime.now() - timedelta(seconds=60),  # Old timestamp
        )

        tp_handler.active_sessions["test_session"] = session

        # Run cleanup
        await tp_handler.cleanup_expired_sessions()

        # Session should be removed
        assert "test_session" not in tp_handler.active_sessions


class TestDiagnosticHandler:
    """Test ISOBUS diagnostic protocol functionality."""

    @pytest.fixture
    def codec(self) -> CANFrameCodec:
        """Create CAN frame codec."""
        return CANFrameCodec()

    @pytest.fixture
    def error_handler(self) -> CANErrorHandler:
        """Create error handler."""
        return CANErrorHandler()

    @pytest.fixture
    def diagnostic_handler(
        self,
        codec: CANFrameCodec,
        error_handler: CANErrorHandler,
    ) -> DiagnosticHandler:
        """Create diagnostic handler."""
        return DiagnosticHandler(codec, error_handler)

    def test_handler_initialization(self, diagnostic_handler: DiagnosticHandler) -> None:
        """Test diagnostic handler initialization."""
        assert len(diagnostic_handler.active_dtcs) == 0
        assert len(diagnostic_handler.inactive_dtcs) == 0

    def test_handle_dm1_with_dtcs(self, diagnostic_handler: DiagnosticHandler) -> None:
        """Test handling DM1 message with DTCs."""
        # Create DM1 message with lamp status and 2 DTCs
        dm1_data = bytearray(8)

        # Lamp status: MIL ON, RSL OFF, AWL ON, PL OFF
        dm1_data[0] = 0x44  # MIL ON (01), AWL ON (01)
        dm1_data[1] = 0xFF  # Reserved

        # First DTC: SPN 110, FMI 3, occurrence count 5
        # SPN 110 = 0x006E, FMI 3, packed format
        dtc1_spn = 110
        dtc1_fmi = 3
        dtc1_data = dtc1_spn | ((dtc1_fmi & 0x1F) << 19)
        dm1_data[2:6] = struct.pack("<I", dtc1_data)
        dm1_data[6] = 5  # Occurrence count

        # Second DTC: SPN 190, FMI 1, occurrence count 2
        dm1_data[7] = 2  # Occurrence count for second DTC (simplified)

        message = can.Message(
            arbitration_id=0x18FECA00,  # DM1 from address 0x00
            data=bytes(dm1_data),
            is_extended_id=True,
        )

        dtcs = diagnostic_handler.handle_dm1_message(message)

        assert len(dtcs) >= 1  # Should have at least one DTC

        # Check first DTC
        dtc = dtcs[0]
        assert dtc.spn == 110
        assert dtc.fmi == 3
        assert dtc.status == "Active"

        # Verify stored in active DTCs
        assert 0x00 in diagnostic_handler.active_dtcs
        stored_dtcs = diagnostic_handler.active_dtcs[0x00]
        assert len(stored_dtcs) >= 1

    def test_handle_dm1_no_dtcs(self, diagnostic_handler: DiagnosticHandler) -> None:
        """Test handling DM1 message with no DTCs."""
        # DM1 with no active DTCs (all zeros after lamp status)
        dm1_data = bytearray(8)
        dm1_data[0] = 0x00  # All lamps off
        dm1_data[1] = 0xFF  # Reserved
        # Remaining bytes are zeros (no DTCs)

        message = can.Message(
            arbitration_id=0x18FECA25,  # DM1 from address 0x25
            data=bytes(dm1_data),
            is_extended_id=True,
        )

        dtcs = diagnostic_handler.handle_dm1_message(message)

        assert len(dtcs) == 0  # No DTCs
        assert 0x25 in diagnostic_handler.active_dtcs
        assert len(diagnostic_handler.active_dtcs[0x25]) == 0

    def test_diagnostic_callbacks(self, diagnostic_handler: DiagnosticHandler) -> None:
        """Test diagnostic event callbacks."""
        callback_calls = []

        def diagnostic_callback(source_address: int, dtcs: list[DiagnosticTroubleCode]) -> None:
            callback_calls.append((source_address, len(dtcs)))

        diagnostic_handler.add_diagnostic_callback(diagnostic_callback)

        # Trigger DM1 with DTCs
        dm1_data = bytearray(8)
        dm1_data[0] = 0x40  # MIL ON
        dm1_data[1] = 0xFF
        # Add simple DTC
        dm1_data[2:6] = struct.pack("<I", 100 | (2 << 19))  # SPN 100, FMI 2
        dm1_data[6] = 1

        message = can.Message(
            arbitration_id=0x18FECA30,
            data=bytes(dm1_data),
            is_extended_id=True,
        )

        diagnostic_handler.handle_dm1_message(message)

        assert len(callback_calls) == 1
        assert callback_calls[0][0] == 0x30  # Source address
        assert callback_calls[0][1] >= 1  # Number of DTCs

    def test_get_active_dtcs_for_device(self, diagnostic_handler: DiagnosticHandler) -> None:
        """Test retrieving active DTCs for specific device."""
        # Add some test DTCs
        test_dtc = DiagnosticTroubleCode(
            spn=110,
            fmi=3,
            occurrence_count=5,
            status="Active",
            lamp_status="MIL:ON",
            description="Test DTC",
        )

        diagnostic_handler.active_dtcs[0x25] = [test_dtc]

        # Test retrieval
        dtcs = diagnostic_handler.get_active_dtcs_for_device(0x25)
        assert len(dtcs) == 1
        assert dtcs[0].spn == 110

        # Test non-existent device
        no_dtcs = diagnostic_handler.get_active_dtcs_for_device(0x99)
        assert len(no_dtcs) == 0

    def test_get_all_active_dtcs(self, diagnostic_handler: DiagnosticHandler) -> None:
        """Test retrieving all active DTCs."""
        # Add DTCs for multiple devices
        dtc1 = DiagnosticTroubleCode(
            spn=110, fmi=3, occurrence_count=1, status="Active", lamp_status="", description=""
        )
        dtc2 = DiagnosticTroubleCode(
            spn=190, fmi=1, occurrence_count=2, status="Active", lamp_status="", description=""
        )

        diagnostic_handler.active_dtcs[0x25] = [dtc1]
        diagnostic_handler.active_dtcs[0x30] = [dtc2]

        all_dtcs = diagnostic_handler.get_all_active_dtcs()

        assert len(all_dtcs) == 2
        assert 0x25 in all_dtcs
        assert 0x30 in all_dtcs
        assert len(all_dtcs[0x25]) == 1
        assert len(all_dtcs[0x30]) == 1


class TestISOBUSProtocolManager:
    """Test integrated ISOBUS protocol management."""

    @pytest.fixture
    def codec(self) -> CANFrameCodec:
        """Create CAN frame codec."""
        return CANFrameCodec()

    @pytest.fixture
    def protocol_manager(self, codec: CANFrameCodec) -> ISOBUSProtocolManager:
        """Create ISOBUS protocol manager."""
        return ISOBUSProtocolManager(codec)

    @pytest.mark.asyncio
    async def test_manager_lifecycle(self, protocol_manager: ISOBUSProtocolManager) -> None:
        """Test protocol manager start/stop lifecycle."""
        assert protocol_manager._running is False

        # Start manager
        await protocol_manager.start()
        assert protocol_manager._running is True
        assert protocol_manager._cleanup_task is not None

        # Stop manager
        await protocol_manager.stop()
        assert protocol_manager._running is False

    def test_message_routing_address_claim(self, protocol_manager: ISOBUSProtocolManager) -> None:
        """Test message routing for address claim."""
        # Create address claim message
        name_data = bytearray(8)
        struct.pack_into("<I", name_data, 0, 12345)
        name_data[5] = ISOBUSFunction.TRACTOR.value

        message = can.Message(
            arbitration_id=0x18EEFF25,
            data=bytes(name_data),
            is_extended_id=True,
        )

        handled = protocol_manager.handle_message(message)
        assert handled is True

        # Verify device was added
        device = protocol_manager.address_claim.get_device_by_address(0x25)
        assert device is not None
        assert device.function == ISOBUSFunction.TRACTOR

    def test_message_routing_tp_cm(self, protocol_manager: ISOBUSProtocolManager) -> None:
        """Test message routing for Transport Protocol CM."""
        # Create RTS message
        rts_data = bytearray(8)
        rts_data[0] = TPControl.RTS.value
        rts_data[1:3] = struct.pack("<H", 20)
        rts_data[3] = 3
        rts_data[4] = 3
        rts_data[5:8] = struct.pack("<I", 0x1234)[0:3]

        message = can.Message(
            arbitration_id=0x18EB2500,
            data=bytes(rts_data),
            is_extended_id=True,
        )

        handled = protocol_manager.handle_message(message)
        assert handled is True

        # Verify session was created
        assert len(protocol_manager.transport_protocol.active_sessions) == 1

    def test_message_routing_diagnostic(self, protocol_manager: ISOBUSProtocolManager) -> None:
        """Test message routing for diagnostic messages."""
        # Create DM1 message
        dm1_data = bytearray(8)
        dm1_data[0] = 0x40  # MIL ON
        dm1_data[1] = 0xFF

        message = can.Message(
            arbitration_id=0x18FECA25,
            data=bytes(dm1_data),
            is_extended_id=True,
        )

        handled = protocol_manager.handle_message(message)
        assert handled is True

        # Verify DTCs were processed
        assert 0x25 in protocol_manager.diagnostics.active_dtcs

    def test_message_routing_unknown(self, protocol_manager: ISOBUSProtocolManager) -> None:
        """Test message routing for unknown messages."""
        # Create unknown message
        message = can.Message(
            arbitration_id=0x18DEAD25,
            data=b"\x01\x02\x03\x04",
            is_extended_id=True,
        )

        handled = protocol_manager.handle_message(message)
        assert handled is False

    def test_standard_frame_ignored(self, protocol_manager: ISOBUSProtocolManager) -> None:
        """Test that standard CAN frames are ignored."""
        message = can.Message(
            arbitration_id=0x123,
            data=b"\x01\x02\x03\x04",
            is_extended_id=False,  # Standard frame
        )

        handled = protocol_manager.handle_message(message)
        assert handled is False

    def test_get_network_status(self, protocol_manager: ISOBUSProtocolManager) -> None:
        """Test getting comprehensive network status."""
        # Add some test data
        test_device = ISOBUSDevice(
            name="Test",
            address=0x25,
            function=ISOBUSFunction.TRACTOR,
            manufacturer_code=100,
            device_class=0,
            device_class_instance=0,
            ecu_instance=0,
            identity_number=1000,
            preferred_address=0x25,
        )
        protocol_manager.address_claim.claimed_addresses[0x25] = test_device

        test_dtc = DiagnosticTroubleCode(
            spn=110, fmi=3, occurrence_count=1, status="Active", lamp_status="", description=""
        )
        protocol_manager.diagnostics.active_dtcs[0x25] = [test_dtc]

        status = protocol_manager.get_network_status()

        assert "devices" in status
        assert "transport_protocol" in status
        assert "diagnostics" in status

        # Check device status
        assert status["devices"]["total"] == 1
        assert status["devices"]["by_function"]["TRACTOR"] == 1

        # Check diagnostic status
        assert status["diagnostics"]["devices_with_active_dtcs"] == 1
        assert status["diagnostics"]["total_active_dtcs"] == 1


class TestIntegrationScenarios:
    """Test real-world ISOBUS integration scenarios."""

    @pytest.mark.asyncio
    async def test_complete_tractor_implement_communication(self) -> None:
        """Test complete tractor-implement ISOBUS communication scenario."""
        codec = CANFrameCodec()
        manager = ISOBUSProtocolManager(codec)

        await manager.start()

        try:
            # 1. Tractor claims address
            tractor_name = bytearray(8)
            struct.pack_into("<I", tractor_name, 0, 11111)
            tractor_name[5] = ISOBUSFunction.TRACTOR.value

            tractor_claim = can.Message(
                arbitration_id=0x18EEFF00,  # Tractor at address 0x00
                data=bytes(tractor_name),
                is_extended_id=True,
            )

            handled = manager.handle_message(tractor_claim)
            assert handled is True

            # 2. Implement claims address
            implement_name = bytearray(8)
            struct.pack_into("<I", implement_name, 0, 22222)
            implement_name[5] = ISOBUSFunction.SPRAYERS.value

            implement_claim = can.Message(
                arbitration_id=0x18EEFF25,  # Implement at address 0x25
                data=bytes(implement_name),
                is_extended_id=True,
            )

            handled = manager.handle_message(implement_claim)
            assert handled is True

            # 3. Implement sends diagnostic information (DM1)
            dm1_data = bytearray(8)
            dm1_data[0] = 0x44  # Amber warning lamp on
            dm1_data[1] = 0xFF
            dm1_data[2:6] = struct.pack("<I", 190 | (3 << 19))  # SPN 190, FMI 3
            dm1_data[6] = 1

            dm1_message = can.Message(
                arbitration_id=0x18FECA25,  # DM1 from implement
                data=bytes(dm1_data),
                is_extended_id=True,
            )

            handled = manager.handle_message(dm1_message)
            assert handled is True

            # 4. Verify network state
            status = manager.get_network_status()

            assert status["devices"]["total"] == 2
            assert status["devices"]["by_function"]["TRACTOR"] == 1
            assert status["devices"]["by_function"]["SPRAYERS"] == 1
            assert status["diagnostics"]["devices_with_active_dtcs"] == 1

            # 5. Verify device lookup
            tractor = manager.address_claim.get_device_by_address(0x00)
            implement = manager.address_claim.get_device_by_address(0x25)

            assert tractor is not None
            assert tractor.function == ISOBUSFunction.TRACTOR
            assert implement is not None
            assert implement.function == ISOBUSFunction.SPRAYERS

            # 6. Check diagnostic state
            implement_dtcs = manager.diagnostics.get_active_dtcs_for_device(0x25)
            assert len(implement_dtcs) >= 1

        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_transport_protocol_large_message(self) -> None:
        """Test Transport Protocol with large multi-frame message."""
        codec = CANFrameCodec()
        manager = ISOBUSProtocolManager(codec)

        await manager.start()

        try:
            # Track completed messages
            completed_messages = []

            def message_callback(pgn: int, data: bytes, source_address: int) -> None:
                completed_messages.append((pgn, data, source_address))

            manager.transport_protocol.add_message_callback(message_callback)

            # 1. Send RTS for 25-byte message (4 packets)
            rts_data = bytearray(8)
            rts_data[0] = TPControl.RTS.value
            rts_data[1:3] = struct.pack("<H", 25)  # 25 bytes
            rts_data[3] = 4  # 4 packets
            rts_data[4] = 3  # Max 3 packets per CTS
            rts_data[5:8] = struct.pack("<I", 0xABCD)[0:3]  # PGN

            rts_message = can.Message(
                arbitration_id=0x18EB0025,  # From 0x25 to 0x00
                data=bytes(rts_data),
                is_extended_id=True,
            )

            handled = manager.handle_message(rts_message)
            assert handled is True

            # 2. Send 4 data packets
            test_data = b"ABCDEFGHIJKLMNOPQRSTUVWXY"  # 25 bytes

            for packet_num in range(1, 5):
                dt_data = bytearray(8)
                dt_data[0] = packet_num

                start_idx = (packet_num - 1) * 7
                end_idx = min(start_idx + 7, len(test_data))
                packet_data = test_data[start_idx:end_idx]

                dt_data[1 : 1 + len(packet_data)] = packet_data

                dt_message = can.Message(
                    arbitration_id=0x18EC0025,  # TP.DT from 0x25 to 0x00
                    data=bytes(dt_data),
                    is_extended_id=True,
                )

                handled = manager.handle_message(dt_message)
                assert handled is True

            # 3. Verify message completion
            assert len(completed_messages) == 1
            assert completed_messages[0][0] == 0xABCD  # PGN
            assert completed_messages[0][1] == test_data  # Complete data
            assert completed_messages[0][2] == 0x25  # Source address

        finally:
            await manager.stop()

    def test_address_conflict_resolution(self) -> None:
        """Test ISOBUS address conflict detection and handling."""
        codec = CANFrameCodec()
        manager = ISOBUSProtocolManager(codec)

        # Device 1 claims address 0x25
        name1 = bytearray(8)
        struct.pack_into("<I", name1, 0, 11111)
        name1[5] = ISOBUSFunction.TRACTOR.value

        claim1 = can.Message(
            arbitration_id=0x18EEFF25,
            data=bytes(name1),
            is_extended_id=True,
        )

        handled1 = manager.handle_message(claim1)
        assert handled1 is True

        # Verify device 1 claimed address
        device1 = manager.address_claim.get_device_by_address(0x25)
        assert device1 is not None
        assert device1.identity_number == 11111

        # Device 2 tries to claim same address with different identity
        name2 = bytearray(8)
        struct.pack_into("<I", name2, 0, 22222)  # Different identity
        name2[5] = ISOBUSFunction.SPRAYERS.value

        claim2 = can.Message(
            arbitration_id=0x18EEFF25,  # Same address
            data=bytes(name2),
            is_extended_id=True,
        )

        handled2 = manager.handle_message(claim2)
        assert handled2 is True  # Message is handled, but conflict detected

        # Verify conflict was detected
        assert len(manager.address_claim.address_conflicts) == 1
        assert manager.address_claim.address_conflicts[0][0] == 0x25

        # Original device should still own the address
        current_device = manager.address_claim.get_device_by_address(0x25)
        assert current_device is not None
        assert current_device.identity_number == 11111  # Original device retained
