"""
Comprehensive ISOBUS protocol handlers for precision agriculture systems.

This module implements the specialized ISOBUS (ISO 11783) protocols required
for advanced agricultural equipment communication, including Transport Protocol,
Address Claim, Task Controller, and diagnostic protocols.

Implementation follows Test-First Development (TDD) GREEN phase.
"""

from __future__ import annotations

import asyncio
import logging
import struct
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import can

from afs_fastapi.core.can_frame_codec import CANFrameCodec
from afs_fastapi.equipment.can_error_handling import CANErrorHandler, CANErrorType

# Configure logging for ISOBUS protocols
logger = logging.getLogger(__name__)


class ISOBUSFunction(Enum):
    """ISOBUS function codes for address claim."""

    TRACTOR = 0
    TILLAGE = 1
    SECONDARY_TILLAGE = 2
    PLANTERS_SEEDERS = 3
    FERTILIZERS = 4
    SPRAYERS = 5
    HARVESTERS = 6
    ROOT_HARVESTERS = 7
    FORAGE_EQUIPMENT = 8
    IRRIGATION = 9
    TRANSPORT_TRAILERS = 10
    FARM_YARD_OPERATIONS = 11
    POWERED_AUXILIARY_DEVICES = 12
    SPECIAL_CROPS = 13
    EARTH_WORK = 14
    ROAD_TRANSPORT = 15


class TPControl(Enum):
    """Transport Protocol control bytes."""

    RTS = 16  # Request to Send
    CTS = 17  # Clear to Send
    EOM = 19  # End of Message
    BAM = 32  # Broadcast Announce Message
    ABORT = 255  # Connection Abort


class DMType(Enum):
    """Diagnostic Message types."""

    DM1 = 0xFECA  # Active Diagnostic Trouble Codes
    DM2 = 0xFECB  # Previously Active Diagnostic Trouble Codes
    DM3 = 0xFECC  # Diagnostic Data Clear/Reset


@dataclass
class ISOBUSDevice:
    """ISOBUS device information."""

    name: str
    address: int
    function: ISOBUSFunction
    manufacturer_code: int
    device_class: int
    device_class_instance: int
    ecu_instance: int
    identity_number: int
    preferred_address: int
    last_seen: datetime = field(default_factory=datetime.now)
    capabilities: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TPSession:
    """Transport Protocol session state."""

    session_id: str
    pgn: int
    source_address: int
    destination_address: int
    total_size: int
    total_packets: int
    max_packets: int
    packets_received: int = 0
    data_buffer: bytearray = field(default_factory=bytearray)
    last_packet_time: datetime = field(default_factory=datetime.now)
    is_bam: bool = False  # Broadcast Announce Message
    complete: bool = False


@dataclass
class TaskControllerObject:
    """Task Controller object definition."""

    object_id: int
    object_type: str
    object_label: str
    parent_object_id: int | None = None
    children: list[int] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class DiagnosticTroubleCode:
    """ISOBUS Diagnostic Trouble Code."""

    spn: int  # Suspect Parameter Number
    fmi: int  # Failure Mode Indicator
    occurrence_count: int
    status: str
    lamp_status: str
    description: str
    timestamp: datetime = field(default_factory=datetime.now)


class AddressClaimHandler:
    """Handles ISOBUS address claim procedure."""

    def __init__(self, codec: CANFrameCodec, error_handler: CANErrorHandler) -> None:
        """Initialize address claim handler.

        Parameters
        ----------
        codec : CANFrameCodec
            CAN frame codec
        error_handler : CANErrorHandler
            Error handling system
        """
        self.codec = codec
        self.error_handler = error_handler

        self.claimed_addresses: dict[int, ISOBUSDevice] = {}  # address -> device
        self.pending_claims: dict[int, ISOBUSDevice] = {}  # address -> device
        self.address_conflicts: list[tuple[int, int]] = []  # (address, timestamp)

        self._claim_callbacks: list[Callable[[ISOBUSDevice], None]] = []

    def add_claim_callback(self, callback: Callable[[ISOBUSDevice], None]) -> None:
        """Add callback for address claim events.

        Parameters
        ----------
        callback : Callable[[ISOBUSDevice], None]
            Callback function
        """
        self._claim_callbacks.append(callback)

    def handle_address_claim(self, message: can.Message) -> ISOBUSDevice | None:
        """Handle incoming address claim message.

        Parameters
        ----------
        message : can.Message
            Address claim message (PGN 60928)

        Returns
        -------
        ISOBUSDevice | None
            Claimed device information
        """
        try:
            if len(message.data) != 8:
                logger.warning("Invalid address claim message length")
                return None

            # Parse NAME field (ISO 11783-5)
            name_bytes = message.data

            # Extract NAME components
            identity_number = struct.unpack("<I", name_bytes[0:4])[0] & 0x1FFFFF  # 21 bits
            manufacturer_code = (struct.unpack("<H", name_bytes[3:5])[0] >> 5) & 0x7FF  # 11 bits
            ecu_instance = (name_bytes[4] >> 3) & 0x07  # 3 bits
            # function_instance = name_bytes[4] & 0x1F  # 5 bits - will be used for instance tracking
            function = ISOBUSFunction(name_bytes[5])  # 8 bits
            device_class = (name_bytes[6] >> 1) & 0x7F  # 7 bits
            device_class_instance = ((name_bytes[6] & 0x01) << 3) | (
                (name_bytes[7] >> 5) & 0x07
            )  # 4 bits
            # industry_group = (name_bytes[7] >> 4) & 0x07  # 3 bits - will be used for classification
            # arbitrary_address_capable = bool(name_bytes[7] & 0x80)  # Will be used for address management

            source_address = message.arbitration_id & 0xFF

            # Create device info
            device = ISOBUSDevice(
                name=f"Device_{source_address:02X}",
                address=source_address,
                function=function,
                manufacturer_code=manufacturer_code,
                device_class=device_class,
                device_class_instance=device_class_instance,
                ecu_instance=ecu_instance,
                identity_number=identity_number,
                preferred_address=source_address,
            )

            # Check for address conflicts
            if source_address in self.claimed_addresses:
                existing_device = self.claimed_addresses[source_address]
                if existing_device.identity_number != identity_number:
                    logger.warning(f"Address conflict at {source_address:02X}")
                    self.address_conflicts.append((source_address, int(time.time())))
                    return None

            # Claim address
            self.claimed_addresses[source_address] = device
            logger.info(f"Address claimed: {source_address:02X} by {function.name}")

            # Notify callbacks
            for callback in self._claim_callbacks:
                try:
                    callback(device)
                except Exception as e:
                    logger.error(f"Address claim callback error: {e}")

            return device

        except Exception as e:
            logger.error(f"Failed to handle address claim: {e}")
            self.error_handler.handle_error(
                CANErrorType.DATA_CORRUPTION,
                f"Address claim parsing error: {e}",
                message.arbitration_id & 0xFF,
            )
            return None

    def create_address_claim_message(self, device: ISOBUSDevice) -> can.Message:
        """Create address claim message for a device.

        Parameters
        ----------
        device : ISOBUSDevice
            Device claiming address

        Returns
        -------
        can.Message
            Address claim message
        """
        # Construct NAME field
        name_bytes = bytearray(8)

        # Identity number (21 bits)
        identity_bytes = struct.pack("<I", device.identity_number & 0x1FFFFF)
        name_bytes[0:3] = identity_bytes[0:3]

        # Manufacturer code (11 bits) + part of identity
        manufacturer_and_identity = (device.manufacturer_code << 5) | (
            (device.identity_number >> 16) & 0x1F
        )
        name_bytes[3:5] = struct.pack("<H", manufacturer_and_identity)

        # ECU instance and function instance
        name_bytes[4] = (device.ecu_instance << 3) | (0 & 0x1F)  # Function instance = 0

        # Function
        name_bytes[5] = device.function.value

        # Device class and device class instance
        name_bytes[6] = (device.device_class << 1) | ((device.device_class_instance >> 3) & 0x01)

        # Industry group and arbitrary address capability
        name_bytes[7] = (
            ((device.device_class_instance & 0x07) << 5) | (0x04 << 4) | 0x80
        )  # Industry group 4, arbitrary address capable

        # Construct CAN message
        can_id = 0x18EEFF00 | device.address  # PGN 60928 (Address Claim)

        return can.Message(
            arbitration_id=can_id,
            data=bytes(name_bytes),
            is_extended_id=True,
        )

    def get_device_by_address(self, address: int) -> ISOBUSDevice | None:
        """Get device information by address.

        Parameters
        ----------
        address : int
            Device address

        Returns
        -------
        ISOBUSDevice | None
            Device information or None
        """
        return self.claimed_addresses.get(address)

    def get_devices_by_function(self, function: ISOBUSFunction) -> list[ISOBUSDevice]:
        """Get devices by function type.

        Parameters
        ----------
        function : ISOBUSFunction
            Function type to search for

        Returns
        -------
        list[ISOBUSDevice]
            List of devices with specified function
        """
        return [device for device in self.claimed_addresses.values() if device.function == function]


class TransportProtocolHandler:
    """Handles ISOBUS Transport Protocol for multi-frame messages."""

    def __init__(self, codec: CANFrameCodec, error_handler: CANErrorHandler) -> None:
        """Initialize transport protocol handler.

        Parameters
        ----------
        codec : CANFrameCodec
            CAN frame codec
        error_handler : CANErrorHandler
            Error handling system
        """
        self.codec = codec
        self.error_handler = error_handler

        self.active_sessions: dict[str, TPSession] = {}  # session_id -> session
        self.completed_messages: list[tuple[int, bytes, datetime]] = []  # (pgn, data, timestamp)

        self._message_callbacks: list[Callable[[int, bytes, int], None]] = (
            []
        )  # (pgn, data, source_address)
        self._session_timeout = 30.0  # seconds

    def add_message_callback(self, callback: Callable[[int, bytes, int], None]) -> None:
        """Add callback for completed multi-frame messages.

        Parameters
        ----------
        callback : Callable[[int, bytes, int], None]
            Callback function (pgn, data, source_address)
        """
        self._message_callbacks.append(callback)

    def handle_tp_cm_message(self, message: can.Message) -> str | None:
        """Handle Transport Protocol Connection Management message.

        Parameters
        ----------
        message : can.Message
            TP.CM message

        Returns
        -------
        str | None
            Session ID if session created
        """
        try:
            if len(message.data) < 8:
                return None

            control_byte = message.data[0]
            source_address = message.arbitration_id & 0xFF
            destination_address = (message.arbitration_id >> 8) & 0xFF

            if control_byte == TPControl.RTS.value:
                # Request to Send
                total_size = struct.unpack("<H", message.data[1:3])[0]
                total_packets = message.data[3]
                max_packets = message.data[4]
                pgn = struct.unpack("<I", message.data[5:8] + b"\x00")[0]

                session_id = f"{source_address:02X}_{destination_address:02X}_{pgn:04X}"

                session = TPSession(
                    session_id=session_id,
                    pgn=pgn,
                    source_address=source_address,
                    destination_address=destination_address,
                    total_size=total_size,
                    total_packets=total_packets,
                    max_packets=max_packets,
                    data_buffer=bytearray(total_size),
                )

                self.active_sessions[session_id] = session
                logger.debug(f"TP RTS: PGN={pgn:04X}, size={total_size}, packets={total_packets}")

                # Send CTS response (simplified - send all packets)
                # cts_response = self._create_cts_message(destination_address, source_address, total_packets, 1)
                # TODO: Actually send the CTS response when interface sending is implemented
                return session_id

            elif control_byte == TPControl.BAM.value:
                # Broadcast Announce Message
                total_size = struct.unpack("<H", message.data[1:3])[0]
                total_packets = message.data[3]
                pgn = struct.unpack("<I", message.data[5:8] + b"\x00")[0]

                session_id = f"BAM_{source_address:02X}_{pgn:04X}"

                session = TPSession(
                    session_id=session_id,
                    pgn=pgn,
                    source_address=source_address,
                    destination_address=255,  # Broadcast
                    total_size=total_size,
                    total_packets=total_packets,
                    max_packets=255,
                    data_buffer=bytearray(total_size),
                    is_bam=True,
                )

                self.active_sessions[session_id] = session
                logger.debug(f"TP BAM: PGN={pgn:04X}, size={total_size}, packets={total_packets}")
                return session_id

            elif control_byte == TPControl.EOM.value:
                # End of Message acknowledgment
                logger.debug("TP EOM received")

            elif control_byte == TPControl.ABORT.value:
                # Connection abort
                pgn = struct.unpack("<I", message.data[5:8] + b"\x00")[0]
                session_id = f"{source_address:02X}_{destination_address:02X}_{pgn:04X}"
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]
                logger.warning(f"TP session aborted: {session_id}")

            return None

        except Exception as e:
            logger.error(f"Failed to handle TP.CM message: {e}")
            return None

    def handle_tp_dt_message(self, message: can.Message) -> bytes | None:
        """Handle Transport Protocol Data Transfer message.

        Parameters
        ----------
        message : can.Message
            TP.DT message

        Returns
        -------
        bytes | None
            Completed message data if session finished
        """
        try:
            if len(message.data) < 1:
                return None

            sequence_number = message.data[0]
            data_bytes = message.data[1:]
            source_address = message.arbitration_id & 0xFF
            destination_address = (message.arbitration_id >> 8) & 0xFF

            # Find matching session
            session = None
            for sess in self.active_sessions.values():
                if sess.source_address == source_address and (
                    sess.destination_address == destination_address or sess.is_bam
                ):
                    session = sess
                    break

            if not session:
                logger.warning(f"No TP session found for data from {source_address:02X}")
                return None

            # Validate sequence number
            expected_seq = session.packets_received + 1
            if sequence_number != expected_seq:
                logger.warning(f"TP sequence error: expected {expected_seq}, got {sequence_number}")
                return None

            # Store data
            start_offset = (sequence_number - 1) * 7
            end_offset = min(start_offset + len(data_bytes), session.total_size)
            actual_data_len = end_offset - start_offset

            session.data_buffer[start_offset:end_offset] = data_bytes[:actual_data_len]
            session.packets_received += 1
            session.last_packet_time = datetime.now()

            logger.debug(
                f"TP data packet {sequence_number}/{session.total_packets} for PGN {session.pgn:04X}"
            )

            # Check if complete
            if session.packets_received >= session.total_packets:
                session.complete = True
                completed_data = bytes(session.data_buffer)

                # Notify callbacks
                for callback in self._message_callbacks:
                    try:
                        callback(session.pgn, completed_data, session.source_address)
                    except Exception as e:
                        logger.error(f"TP message callback error: {e}")

                # Clean up session
                del self.active_sessions[session.session_id]

                # Store in completed messages
                self.completed_messages.append((session.pgn, completed_data, datetime.now()))

                logger.info(
                    f"TP session completed: PGN={session.pgn:04X}, size={len(completed_data)}"
                )
                return completed_data

            return None

        except Exception as e:
            logger.error(f"Failed to handle TP.DT message: {e}")
            return None

    def _create_cts_message(
        self, source: int, dest: int, packets: int, next_packet: int
    ) -> can.Message:
        """Create Clear to Send message.

        Parameters
        ----------
        source : int
            Source address
        dest : int
            Destination address
        packets : int
            Number of packets to send
        next_packet : int
            Next packet sequence number

        Returns
        -------
        can.Message
            CTS message
        """
        data = bytearray(8)
        data[0] = TPControl.CTS.value
        data[1] = min(packets, 255)  # Number of packets
        data[2] = next_packet  # Next packet number
        data[3] = 0xFF  # Reserved
        data[4] = 0xFF  # Reserved

        can_id = 0x18EC0000 | (dest << 8) | source
        return can.Message(arbitration_id=can_id, data=bytes(data), is_extended_id=True)

    async def cleanup_expired_sessions(self) -> None:
        """Clean up expired TP sessions."""
        current_time = datetime.now()
        expired_sessions = []

        for session_id, session in self.active_sessions.items():
            if (current_time - session.last_packet_time).total_seconds() > self._session_timeout:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            logger.warning(f"TP session expired: {session_id}")
            del self.active_sessions[session_id]


class DiagnosticHandler:
    """Handles ISOBUS diagnostic protocols (DM1, DM2, DM3)."""

    def __init__(self, codec: CANFrameCodec, error_handler: CANErrorHandler) -> None:
        """Initialize diagnostic handler.

        Parameters
        ----------
        codec : CANFrameCodec
            CAN frame codec
        error_handler : CANErrorHandler
            Error handling system
        """
        self.codec = codec
        self.error_handler = error_handler

        self.active_dtcs: dict[int, list[DiagnosticTroubleCode]] = {}  # source_address -> DTCs
        self.inactive_dtcs: dict[int, list[DiagnosticTroubleCode]] = {}

        self._diagnostic_callbacks: list[Callable[[int, list[DiagnosticTroubleCode]], None]] = []

    def add_diagnostic_callback(
        self, callback: Callable[[int, list[DiagnosticTroubleCode]], None]
    ) -> None:
        """Add callback for diagnostic events.

        Parameters
        ----------
        callback : Callable[[int, list[DiagnosticTroubleCode]], None]
            Callback function (source_address, dtcs)
        """
        self._diagnostic_callbacks.append(callback)

    def handle_dm1_message(self, message: can.Message) -> list[DiagnosticTroubleCode]:
        """Handle DM1 (Active Diagnostic Trouble Codes) message.

        Parameters
        ----------
        message : can.Message
            DM1 message

        Returns
        -------
        list[DiagnosticTroubleCode]
            List of active DTCs
        """
        try:
            source_address = message.arbitration_id & 0xFF
            data = message.data

            if len(data) < 2:
                return []

            # Parse lamp status
            lamp_status_byte = data[0]
            lamp_status = self._parse_lamp_status(lamp_status_byte)

            # Parse DTCs (4 bytes each after lamp status bytes)
            dtcs = []
            dtc_data = data[2:]  # Skip lamp status bytes

            for i in range(0, len(dtc_data) - 3, 4):
                if i + 4 <= len(dtc_data):
                    dtc_bytes = dtc_data[i : i + 4]
                    dtc = self._parse_dtc(dtc_bytes, lamp_status)
                    if dtc:
                        dtcs.append(dtc)

            # Store active DTCs
            self.active_dtcs[source_address] = dtcs

            # Notify callbacks
            for callback in self._diagnostic_callbacks:
                try:
                    callback(source_address, dtcs)
                except Exception as e:
                    logger.error(f"Diagnostic callback error: {e}")

            logger.info(f"DM1 from {source_address:02X}: {len(dtcs)} active DTCs")
            return dtcs

        except Exception as e:
            logger.error(f"Failed to handle DM1 message: {e}")
            return []

    def handle_dm2_message(self, message: can.Message) -> list[DiagnosticTroubleCode]:
        """Handle DM2 (Previously Active Diagnostic Trouble Codes) message.

        Parameters
        ----------
        message : can.Message
            DM2 message

        Returns
        -------
        list[DiagnosticTroubleCode]
            List of previously active DTCs
        """
        try:
            source_address = message.arbitration_id & 0xFF
            data = message.data

            # Similar parsing to DM1 but for previously active DTCs
            dtcs = []
            dtc_data = data[2:]  # Skip lamp status bytes

            for i in range(0, len(dtc_data) - 3, 4):
                if i + 4 <= len(dtc_data):
                    dtc_bytes = dtc_data[i : i + 4]
                    dtc = self._parse_dtc(dtc_bytes, "Previously Active")
                    if dtc:
                        dtcs.append(dtc)

            # Store inactive DTCs
            self.inactive_dtcs[source_address] = dtcs

            logger.info(f"DM2 from {source_address:02X}: {len(dtcs)} previously active DTCs")
            return dtcs

        except Exception as e:
            logger.error(f"Failed to handle DM2 message: {e}")
            return []

    def _parse_lamp_status(self, lamp_byte: int) -> str:
        """Parse lamp status byte.

        Parameters
        ----------
        lamp_byte : int
            Lamp status byte

        Returns
        -------
        str
            Lamp status description
        """
        status_parts = []

        # Malfunction Indicator Lamp (MIL)
        mil_status = (lamp_byte >> 6) & 0x03
        if mil_status == 0:
            status_parts.append("MIL:OFF")
        elif mil_status == 1:
            status_parts.append("MIL:ON")
        elif mil_status == 2:
            status_parts.append("MIL:RESERVED")
        else:
            status_parts.append("MIL:NOT_AVAILABLE")

        # Red Stop Lamp
        rsl_status = (lamp_byte >> 4) & 0x03
        if rsl_status == 1:
            status_parts.append("RSL:ON")

        # Amber Warning Lamp
        awl_status = (lamp_byte >> 2) & 0x03
        if awl_status == 1:
            status_parts.append("AWL:ON")

        # Protect Lamp
        pl_status = lamp_byte & 0x03
        if pl_status == 1:
            status_parts.append("PL:ON")

        return " ".join(status_parts) if status_parts else "ALL_OFF"

    def _parse_dtc(self, dtc_bytes: bytes, lamp_status: str) -> DiagnosticTroubleCode | None:
        """Parse DTC from 4-byte sequence.

        Parameters
        ----------
        dtc_bytes : bytes
            4-byte DTC data
        lamp_status : str
            Lamp status

        Returns
        -------
        DiagnosticTroubleCode | None
            Parsed DTC or None
        """
        try:
            if len(dtc_bytes) != 4:
                return None

            # Parse SPN (Suspect Parameter Number) - bits 0-18
            spn = dtc_bytes[0] | (dtc_bytes[1] << 8) | ((dtc_bytes[2] & 0x03) << 16)

            # Parse FMI (Failure Mode Indicator) - bits 19-23
            fmi = (dtc_bytes[2] >> 3) & 0x1F

            # Parse occurrence count - byte 4
            occurrence_count = dtc_bytes[3] & 0x7F

            if spn == 0 and fmi == 0:
                return None  # Empty DTC slot

            # Create DTC description
            description = f"SPN {spn}, FMI {fmi}"

            return DiagnosticTroubleCode(
                spn=spn,
                fmi=fmi,
                occurrence_count=occurrence_count,
                status="Active",
                lamp_status=lamp_status,
                description=description,
            )

        except Exception as e:
            logger.debug(f"Failed to parse DTC: {e}")
            return None

    def get_active_dtcs_for_device(self, source_address: int) -> list[DiagnosticTroubleCode]:
        """Get active DTCs for a specific device.

        Parameters
        ----------
        source_address : int
            Device source address

        Returns
        -------
        list[DiagnosticTroubleCode]
            List of active DTCs
        """
        return self.active_dtcs.get(source_address, [])

    def get_all_active_dtcs(self) -> dict[int, list[DiagnosticTroubleCode]]:
        """Get all active DTCs across all devices.

        Returns
        -------
        dict[int, list[DiagnosticTroubleCode]]
            Active DTCs by source address
        """
        return self.active_dtcs.copy()


class ISOBUSProtocolManager:
    """Comprehensive ISOBUS protocol management system."""

    def __init__(
        self,
        codec: CANFrameCodec,
        error_handler: CANErrorHandler | None = None,
    ) -> None:
        """Initialize ISOBUS protocol manager.

        Parameters
        ----------
        codec : CANFrameCodec
            CAN frame codec
        error_handler : CANErrorHandler | None
            Error handling system
        """
        self.codec = codec
        self.error_handler = error_handler or CANErrorHandler()

        # Protocol handlers
        self.address_claim = AddressClaimHandler(codec, self.error_handler)
        self.transport_protocol = TransportProtocolHandler(codec, self.error_handler)
        self.diagnostics = DiagnosticHandler(codec, self.error_handler)

        # Message routing
        self._message_handlers: dict[int, Callable[[can.Message], Any]] = {
            0xEEFF: self.address_claim.handle_address_claim,  # Address Claim
            0xEB00: self.transport_protocol.handle_tp_cm_message,  # TP.CM
            0xEC00: self.transport_protocol.handle_tp_dt_message,  # TP.DT
            0xFECA: self.diagnostics.handle_dm1_message,  # DM1
            0xFECB: self.diagnostics.handle_dm2_message,  # DM2
        }

        # Background tasks
        self._cleanup_task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """Start ISOBUS protocol management."""
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._background_cleanup())
        logger.info("ISOBUS protocol manager started")

    async def stop(self) -> None:
        """Stop ISOBUS protocol management."""
        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("ISOBUS protocol manager stopped")

    def handle_message(self, message: can.Message) -> bool:
        """Handle incoming ISOBUS message.

        Parameters
        ----------
        message : can.Message
            CAN message to process

        Returns
        -------
        bool
            True if message was handled
        """
        try:
            if not message.is_extended_id:
                return False

            # Extract PGN from CAN ID
            # PGN is bits 8-23 of the 29-bit arbitration ID
            pgn_full = (message.arbitration_id >> 8) & 0xFFFF

            pdu_format = (pgn_full >> 8) & 0xFF

            if pdu_format < 0xF0:  # PDU1 format
                pdu_specific = pgn_full & 0xFF
                pgn = (pdu_format << 8) | pdu_specific
            elif pdu_format < 0xFF:  # PDU1 format for diagnostic messages (0xF0-0xFE)
                pdu_specific = pgn_full & 0xFF
                pgn = (pdu_format << 8) | pdu_specific
            else:  # PDU2 format
                pgn = pdu_format << 8

            # Route to appropriate handler
            if pgn in self._message_handlers:
                handler = self._message_handlers[pgn]
                handler(message)
                return True

            # Check for TP messages with different destination addresses
            if pdu_format == 0xEB:  # TP.CM
                self.transport_protocol.handle_tp_cm_message(message)
                return True
            elif pdu_format == 0xEC:  # TP.DT
                self.transport_protocol.handle_tp_dt_message(message)
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to handle ISOBUS message: {e}")
            return False

    async def _background_cleanup(self) -> None:
        """Background cleanup task."""
        while self._running:
            try:
                # Clean up expired TP sessions
                await self.transport_protocol.cleanup_expired_sessions()

                # Clean up old devices (mark as offline after 60 seconds)
                current_time = datetime.now()
                offline_threshold = timedelta(seconds=60)

                for device in list(self.address_claim.claimed_addresses.values()):
                    if current_time - device.last_seen > offline_threshold:
                        logger.info(f"Device {device.address:02X} marked offline")
                        # Could trigger offline callbacks here

                await asyncio.sleep(10.0)  # Cleanup every 10 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Background cleanup error: {e}")
                await asyncio.sleep(10.0)

    def get_network_status(self) -> dict[str, Any]:
        """Get comprehensive ISOBUS network status.

        Returns
        -------
        dict[str, Any]
            Network status information
        """
        return {
            "devices": {
                "total": len(self.address_claim.claimed_addresses),
                "by_function": {
                    func.name: len(self.address_claim.get_devices_by_function(func))
                    for func in ISOBUSFunction
                },
                "conflicts": len(self.address_claim.address_conflicts),
            },
            "transport_protocol": {
                "active_sessions": len(self.transport_protocol.active_sessions),
                "completed_messages": len(self.transport_protocol.completed_messages),
            },
            "diagnostics": {
                "devices_with_active_dtcs": len(self.diagnostics.active_dtcs),
                "total_active_dtcs": sum(
                    len(dtcs) for dtcs in self.diagnostics.active_dtcs.values()
                ),
                "devices_with_inactive_dtcs": len(self.diagnostics.inactive_dtcs),
            },
        }
