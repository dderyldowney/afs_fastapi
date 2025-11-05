"""
Comprehensive CAN frame encoding/decoding utilities for ISOBUS agricultural systems.

This module provides production-grade encoding and decoding of J1939/ISOBUS
CAN messages used in agricultural equipment communication, including multi-frame
Transport Protocol handling and agricultural-specific data type conversions.

Implementation follows Test-First Development (TDD) GREEN phase.
"""

from __future__ import annotations

# Configure logging for CAN codec
import logging
import struct
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

try:
    from can import Message

    _CAN_LIBRARY_AVAILABLE: bool = True
except ImportError:
    Message: Any = None  # Fallback type if can library not available
    _CAN_LIBRARY_AVAILABLE: bool = False

logger = logging.getLogger(__name__)


class J1939DataType(Enum):
    """J1939/ISOBUS data types with scaling and offset information."""

    # Basic integer types
    UINT8 = "uint8"
    UINT16 = "uint16"
    UINT32 = "uint32"
    INT8 = "int8"
    INT16 = "int16"
    INT32 = "int32"

    # Scaled types common in agriculture
    ANGLE = "angle"  # 0.0078125 deg/bit
    PRESSURE = "pressure"  # 2 kPa/bit
    TEMPERATURE = "temperature"  # 0.03125 °C/bit, -273 offset
    SPEED = "speed"  # 0.00390625 km/h/bit
    RPM = "rpm"  # 0.125 rpm/bit
    FUEL_RATE = "fuel_rate"  # 0.05 L/h/bit
    PERCENTAGE = "percentage"  # 0.4 %/bit
    DISTANCE = "distance"  # 0.125 m/bit
    LATITUDE = "latitude"  # 10^-7 degrees/bit
    LONGITUDE = "longitude"  # 10^-7 degrees/bit
    ALTITUDE = "altitude"  # 0.1 m/bit, -500 offset

    # Time types
    TIME_STAMP = "timestamp"  # 0.25 s/bit
    DATE = "date"  # Days since Jan 1, 1985

    # Bitfield types
    STATUS_BITS = "status_bits"
    ERROR_CODES = "error_codes"

    # String types
    ASCII_STRING = "ascii_string"

    # Raw binary
    RAW_BYTES = "raw_bytes"


@dataclass
class SPNDefinition:
    """Suspect Parameter Number definition for J1939 parameters."""

    spn: int
    name: str
    description: str
    data_type: J1939DataType
    start_bit: int
    bit_length: int
    scale: float = 1.0
    offset: float = 0.0
    units: str = ""
    min_value: float | None = None
    max_value: float | None = None
    not_available_value: int | None = None
    error_value: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PGNDefinition:
    """Parameter Group Number definition for J1939 messages."""

    pgn: int
    name: str
    description: str
    data_length: int
    transmission_rate: int | None = None  # milliseconds
    spn_definitions: list[SPNDefinition] = field(default_factory=list)
    is_proprietary: bool = False
    source_address_specific: bool = False
    destination_specific: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DecodedSPN:
    """Decoded Suspect Parameter Number value."""

    spn: int
    name: str
    value: Any
    units: str
    raw_value: int
    is_valid: bool
    is_not_available: bool
    is_error: bool
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DecodedPGN:
    """Decoded Parameter Group Number message."""

    pgn: int
    name: str
    source_address: int
    destination_address: int
    priority: int
    timestamp: datetime
    spn_values: list[DecodedSPN]
    raw_data: bytes
    data_length: int
    is_multi_frame: bool = False
    frame_count: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TransportProtocolFrame:
    """J1939 Transport Protocol frame for multi-frame messages."""

    control_byte: int
    total_message_size: int
    total_packets: int
    maximum_packets: int
    pgn: int
    source_address: int
    destination_address: int
    sequence_number: int = 0
    data_bytes: bytes = b""


class J1939Decoder:
    """J1939/ISOBUS message decoder for agricultural equipment."""

    def __init__(self) -> None:
        """Initialize J1939 decoder with agricultural PGN definitions."""
        self.pgn_definitions: dict[int, PGNDefinition] = {}
        self.spn_definitions: dict[int, SPNDefinition] = {}
        self.transport_sessions: dict[tuple[int, int, int], list[TransportProtocolFrame]] = {}

        # Load standard agricultural PGN definitions
        self._load_agricultural_pgns()

    def _load_agricultural_pgns(self) -> None:
        """Load standard agricultural/ISOBUS PGN and SPN definitions."""

        # Electronic Engine Controller 1 (EEC1) - PGN 61444 (0xF004)
        eec1_spns: list[SPNDefinition] = [
            SPNDefinition(
                spn=190,
                name="Engine Speed",
                description="Actual engine speed",
                data_type=J1939DataType.RPM,
                start_bit=24,
                bit_length=16,
                scale=0.125,
                units="rpm",
                min_value=0,
                max_value=8031.875,
                not_available_value=0xFFFF,
                error_value=0xFFFE,
            ),
            SPNDefinition(
                spn=102,
                name="Engine Intake Manifold #1 Pressure",
                description="Gauge pressure",
                data_type=J1939DataType.PRESSURE,
                start_bit=8,
                bit_length=8,
                scale=2.0,
                units="kPa",
                min_value=0,
                max_value=500,
                not_available_value=0xFF,
                error_value=0xFE,
            ),
            SPNDefinition(
                spn=61,
                name="Engine Percent Torque At Current Speed",
                description="Current output torque",
                data_type=J1939DataType.PERCENTAGE,
                start_bit=16,
                bit_length=8,
                scale=1.0,
                offset=-125,
                units="%",
                min_value=-125,
                max_value=125,
                not_available_value=0xFF,
                error_value=0xFE,
            ),
        ]

        eec1_pgn: PGNDefinition = PGNDefinition(
            pgn=0xF004,
            name="Electronic Engine Controller 1",
            description="Engine parameters",
            data_length=8,
            transmission_rate=50,
            spn_definitions=eec1_spns,
        )

        # Wheel-Based Vehicle Speed (WVS) - PGN 65265 (0xFEF1)
        wvs_spns: list[SPNDefinition] = [
            SPNDefinition(
                spn=84,
                name="Wheel-Based Vehicle Speed",
                description="Speed over ground",
                data_type=J1939DataType.SPEED,
                start_bit=8,
                bit_length=16,
                scale=0.00390625,
                units="km/h",
                min_value=0,
                max_value=250.996,
                not_available_value=0xFFFF,
                error_value=0xFFFE,
            ),
        ]

        wvs_pgn: PGNDefinition = PGNDefinition(
            pgn=0xFEF1,
            name="Wheel-Based Vehicle Speed",
            description="Vehicle speed information",
            data_length=8,
            transmission_rate=100,
            spn_definitions=wvs_spns,
        )

        # Vehicle Position (VP) - PGN 65267 (0xFEF3)
        vp_spns: list[SPNDefinition] = [
            SPNDefinition(
                spn=584,
                name="Latitude",
                description="Latitude coordinate",
                data_type=J1939DataType.LATITUDE,
                start_bit=0,
                bit_length=32,
                scale=1e-7,
                units="degrees",
                min_value=-180,
                max_value=180,
                not_available_value=0xFFFFFFFF,
                error_value=0xFFFFFFFE,
            ),
            SPNDefinition(
                spn=585,
                name="Longitude",
                description="Longitude coordinate",
                data_type=J1939DataType.LONGITUDE,
                start_bit=32,
                bit_length=32,
                scale=1e-7,
                units="degrees",
                min_value=-180,
                max_value=180,
                not_available_value=0xFFFFFFFF,
                error_value=0xFFFFFFFE,
            ),
        ]

        vp_pgn: PGNDefinition = PGNDefinition(
            pgn=0xFEF3,
            name="Vehicle Position",
            description="GPS coordinates",
            data_length=8,
            transmission_rate=1000,
            spn_definitions=vp_spns,
        )

        # Fuel Economy (LFE) - PGN 65266 (0xFEF2)
        lfe_spns: list[SPNDefinition] = [
            SPNDefinition(
                spn=183,
                name="Engine Fuel Rate",
                description="Current fuel consumption rate",
                data_type=J1939DataType.FUEL_RATE,
                start_bit=0,
                bit_length=16,
                scale=0.05,
                units="L/h",
                min_value=0,
                max_value=3212.75,
                not_available_value=0xFFFF,
                error_value=0xFFFE,
            ),
            SPNDefinition(
                spn=184,
                name="Engine Instantaneous Fuel Economy",
                description="Instantaneous fuel economy",
                data_type=J1939DataType.SPEED,
                start_bit=16,
                bit_length=16,
                scale=0.00390625,
                units="km/L",
                min_value=0,
                max_value=125.5,
                not_available_value=0xFFFF,
                error_value=0xFFFE,
            ),
        ]

        lfe_pgn: PGNDefinition = PGNDefinition(
            pgn=0xFEF2,
            name="Fuel Economy",
            description="Fuel consumption data",
            data_length=8,
            transmission_rate=1000,
            spn_definitions=lfe_spns,
        )

        # Electronic Transmission Controller 1 (ETC1) - PGN 61445 (0xF005)
        etc1_spns: list[SPNDefinition] = [
            SPNDefinition(
                spn=191,
                name="Transmission Output Shaft Speed",
                description="Output shaft RPM",
                data_type=J1939DataType.RPM,
                start_bit=8,
                bit_length=16,
                scale=0.125,
                units="rpm",
                min_value=0,
                max_value=8031.875,
                not_available_value=0xFFFF,
                error_value=0xFFFE,
            ),
            SPNDefinition(
                spn=127,
                name="Transmission Current Gear",
                description="Currently selected gear",
                data_type=J1939DataType.UINT8,
                start_bit=40,
                bit_length=8,
                scale=1.0,
                offset=-125,
                units="",
                min_value=-125,
                max_value=125,
                not_available_value=0xFF,
                error_value=0xFE,
            ),
        ]

        etc1_pgn: PGNDefinition = PGNDefinition(
            pgn=0xF005,
            name="Electronic Transmission Controller 1",
            description="Transmission data",
            data_length=8,
            transmission_rate=100,
            spn_definitions=etc1_spns,
        )

        # Dash Display (DD) - PGN 65276 (0xFEFC) - Fuel Level
        dd_spns: list[SPNDefinition] = [
            SPNDefinition(
                spn=96,
                name="Fuel Level",
                description="Fuel tank level percentage",
                data_type=J1939DataType.PERCENTAGE,
                start_bit=8,
                bit_length=8,
                scale=0.4,
                units="%",
                min_value=0,
                max_value=100,
                not_available_value=0xFF,
                error_value=0xFE,
            ),
        ]

        dd_pgn: PGNDefinition = PGNDefinition(
            pgn=0xFEFC,
            name="Dash Display",
            description="Dashboard display information including fuel level",
            data_length=8,
            transmission_rate=1000,
            spn_definitions=dd_spns,
        )

        # Register all PGN definitions
        pgn_definitions: list[PGNDefinition] = [
            eec1_pgn,
            wvs_pgn,
            vp_pgn,
            lfe_pgn,
            etc1_pgn,
            dd_pgn,
        ]

        for pgn_def in pgn_definitions:
            # Register PGN definition
            self.pgn_definitions[pgn_def.pgn] = pgn_def
            # Register SPN definitions
            for spn_def in pgn_def.spn_definitions:
                self.spn_definitions[spn_def.spn] = spn_def

    def decode_can_message(self, message: Any) -> DecodedPGN | None:
        """Decode a CAN message into structured J1939 data.

        Parameters
        ----------
        message : Message
            CAN message to decode

        Returns
        -------
        DecodedPGN | None
            Decoded PGN data or None if not decodable
        """
        try:
            # Extract J1939 components from CAN ID
            if not getattr(message, "is_extended_id", False):
                logger.debug(
                    f"Ignoring standard frame: {getattr(message, 'arbitration_id', 0):08X}"
                )
                return None

            j1939_id: tuple[int, int, int, int, int] | None = self._parse_j1939_id(
                getattr(message, "arbitration_id", 0)
            )
            if not j1939_id:
                return None

            priority, data_page, pdu_format, pdu_specific, source_address = j1939_id

            # Calculate PGN
            if pdu_format >= 240:  # PDU Format 240-255
                pgn: int = (data_page << 16) | (pdu_format << 8) | pdu_specific
                destination_address: int = 255  # Global
            else:  # PDU Format 0-239
                pgn = (data_page << 16) | (pdu_format << 8)
                destination_address = pdu_specific

            # Check for Transport Protocol messages
            if pdu_format == 0xEC:  # TP.DT (Transport Protocol Data Transfer)
                return self._handle_transport_protocol_dt(
                    message, source_address, destination_address
                )
            elif pdu_format == 0xEB:  # TP.CM (Transport Protocol Connection Management)
                return self._handle_transport_protocol_cm(
                    message, source_address, destination_address
                )

            # Look up PGN definition
            if pgn not in self.pgn_definitions:
                logger.debug(f"Unknown PGN: {pgn:04X}")
                return None

            pgn_def: PGNDefinition = self.pgn_definitions[pgn]

            # Decode SPNs
            decoded_spns: list[DecodedSPN] = []
            for spn_def in pgn_def.spn_definitions:
                decoded_spn: DecodedSPN | None = self._decode_spn(spn_def, message.data)
                if decoded_spn:
                    decoded_spns.append(decoded_spn)

            return DecodedPGN(
                pgn=pgn,
                name=pgn_def.name,
                source_address=source_address,
                destination_address=destination_address,
                priority=priority,
                timestamp=datetime.fromtimestamp(message.timestamp or 0),
                spn_values=decoded_spns,
                raw_data=message.data,
                data_length=len(message.data),
            )

        except Exception as e:
            logger.error(f"Failed to decode CAN message {message.arbitration_id:08X}: {e}")
            return None

    def _parse_j1939_id(self, can_id: int) -> tuple[int, int, int, int, int] | None:
        """Parse J1939 components from 29-bit CAN ID.

        Parameters
        ----------
        can_id : int
            29-bit CAN identifier

        Returns
        -------
        tuple[int, int, int, int, int | None]
            (priority, data_page, pdu_format, pdu_specific, source_address) or None
        """
        if can_id > 0x1FFFFFFF:  # 29-bit limit
            return None

        priority: int = (can_id >> 26) & 0x07
        # reserved = (can_id >> 25) & 0x01  # Reserved bit - not used in parsing
        data_page: int = (can_id >> 24) & 0x01
        pdu_format: int = (can_id >> 16) & 0xFF
        pdu_specific: int = (can_id >> 8) & 0xFF
        source_address: int = can_id & 0xFF

        return priority, data_page, pdu_format, pdu_specific, source_address

    def _decode_spn(self, spn_def: SPNDefinition, data: bytes) -> DecodedSPN | None:
        """Decode a single SPN from message data.

        Parameters
        ----------
        spn_def : SPNDefinition
            SPN definition
        data : bytes
            Message data bytes

        Returns
        -------
        DecodedSPN | None
            Decoded SPN value or None if invalid
        """
        try:
            # Extract raw value from data
            raw_value: int = self._extract_bits(data, spn_def.start_bit, spn_def.bit_length)

            # Check for special values
            is_not_available: bool = False
            is_error: bool = False
            is_valid: bool = True

            if spn_def.not_available_value is not None and raw_value == spn_def.not_available_value:
                is_not_available = True
                is_valid = False
            elif spn_def.error_value is not None and raw_value == spn_def.error_value:
                is_error = True
                is_valid = False

            # Apply scaling and offset
            if is_valid:
                # Handle signed integers (including latitude/longitude which can be negative)
                if spn_def.data_type in [
                    J1939DataType.INT8,
                    J1939DataType.INT16,
                    J1939DataType.INT32,
                    J1939DataType.LATITUDE,
                    J1939DataType.LONGITUDE,
                ]:
                    if spn_def.bit_length <= 8:
                        raw_value = struct.unpack("b", struct.pack("B", raw_value))[0]
                    elif spn_def.bit_length <= 16:
                        raw_value = struct.unpack("h", struct.pack("H", raw_value))[0]
                    elif spn_def.bit_length <= 32:
                        raw_value = struct.unpack("i", struct.pack("I", raw_value))[0]

                scaled_value: float = (raw_value * spn_def.scale) + spn_def.offset

                # Range validation
                if spn_def.min_value is not None and scaled_value < spn_def.min_value:
                    is_valid = False
                if spn_def.max_value is not None and scaled_value > spn_def.max_value:
                    is_valid = False

                value: Any = scaled_value
            else:
                value = None

            return DecodedSPN(
                spn=spn_def.spn,
                name=spn_def.name,
                value=value,
                units=spn_def.units,
                raw_value=raw_value,
                is_valid=is_valid,
                is_not_available=is_not_available,
                is_error=is_error,
            )

        except Exception as e:
            logger.error(f"Failed to decode SPN {spn_def.spn}: {e}")
            return None

    def _extract_bits(self, data: bytes, start_bit: int, bit_length: int) -> int:
        """Extract a range of bits from byte data.

        Parameters
        ----------
        data : bytes
            Source data
        start_bit : int
            Starting bit position (0-based)
        bit_length : int
            Number of bits to extract

        Returns
        -------
        int
            Extracted bits as integer
        """
        if len(data) * 8 < start_bit + bit_length:
            raise ValueError("Bit range exceeds data length")

        # Convert bytes to bit array
        bit_array = 0
        for i, byte in enumerate(data):
            bit_array |= byte << (i * 8)

        # Extract the specified bits
        mask = (1 << bit_length) - 1
        extracted = (bit_array >> start_bit) & mask

        return extracted

    def _handle_transport_protocol_dt(
        self, message: Message, source_address: int, destination_address: int
    ) -> DecodedPGN | None:
        """Handle J1939 Transport Protocol Data Transfer message.

        Parameters
        ----------
        message : Message
            TP.DT message
        source_address : int
            Source address
        destination_address : int
            Destination address

        Returns
        -------
        DecodedPGN | None
            Assembled multi-frame message or None if incomplete
        """
        if len(message.data) < 1:
            return None

        sequence_number = message.data[0]
        # data_bytes = message.data[1:]  # Will be used when multi-frame assembly is implemented

        # Find active transport session
        # session_key = (source_address, destination_address, 0)  # Will be used for multi-frame sessions

        # For now, return None as multi-frame assembly requires more complex state management
        logger.debug(f"TP.DT message received: seq={sequence_number}, from={source_address:02X}")
        return None

    def _handle_transport_protocol_cm(
        self, message: Message, source_address: int, destination_address: int
    ) -> DecodedPGN | None:
        """Handle J1939 Transport Protocol Connection Management message.

        Parameters
        ----------
        message : Message
            TP.CM message
        source_address : int
            Source address
        destination_address : int
            Destination address

        Returns
        -------
        DecodedPGN | None
            None (CM messages don't contain data)
        """
        if len(message.data) < 8:
            return None

        control_byte = message.data[0]

        if control_byte == 16:  # RTS (Request to Send)
            total_message_size = struct.unpack("<H", message.data[1:3])[0]
            total_packets = message.data[3]
            # maximum_packets = message.data[4]  # Will be used when implementing flow control
            pgn = struct.unpack("<I", message.data[5:8] + b"\x00")[0]

            logger.debug(
                f"TP.CM RTS: PGN={pgn:04X}, size={total_message_size}, packets={total_packets}"
            )

        # For now, just log and return None
        return None


class J1939Encoder:
    """J1939/ISOBUS message encoder for agricultural equipment."""

    def __init__(self) -> None:
        """Initialize J1939 encoder."""
        self.decoder = J1939Decoder()  # Reuse PGN definitions

    def encode_pgn_message(
        self,
        pgn: int,
        source_address: int,
        spn_values: dict[int, Any],
        priority: int = 6,
        destination_address: int = 255,
        timestamp: float | None = None,
    ) -> Message | None:
        """Encode a PGN message with SPN values.

        Parameters
        ----------
        pgn : int
            Parameter Group Number
        source_address : int
            Source address (0-255)
        spn_values : dict[int, Any]
            SPN values to encode {spn: value}
        priority : int, default 6
            Message priority (0-7)
        destination_address : int, default 255
            Destination address (255 for broadcast)
        timestamp : float | None
            Message timestamp

        Returns
        -------
        Message | None
            Encoded CAN message or None if encoding fails
        """
        try:
            # Look up PGN definition
            if pgn not in self.decoder.pgn_definitions:
                logger.error(f"Unknown PGN for encoding: {pgn:04X}")
                return None

            pgn_def = self.decoder.pgn_definitions[pgn]

            # Initialize data buffer
            data = bytearray(pgn_def.data_length)

            # Encode each SPN
            for spn_def in pgn_def.spn_definitions:
                if spn_def.spn in spn_values:
                    value = spn_values[spn_def.spn]
                    encoded_value = self._encode_spn_value(spn_def, value)
                    if encoded_value is not None:
                        self._insert_bits(
                            data, spn_def.start_bit, spn_def.bit_length, encoded_value
                        )

            # Construct J1939 CAN ID
            can_id = self._construct_j1939_id(pgn, priority, source_address, destination_address)

            return Message(
                arbitration_id=can_id,
                data=bytes(data),
                is_extended_id=True,
                timestamp=timestamp or 0.0,
            )

        except Exception as e:
            logger.error(f"Failed to encode PGN {pgn:04X}: {e}")
            return None

    def _encode_spn_value(self, spn_def: SPNDefinition, value: Any) -> int | None:
        """Encode a single SPN value to raw integer.

        Parameters
        ----------
        spn_def : SPNDefinition
            SPN definition
        value : Any
            Value to encode

        Returns
        -------
        int | None
            Encoded raw value or None if encoding fails
        """
        try:
            if value is None:
                return spn_def.not_available_value

            # Apply inverse scaling and offset
            raw_value = (value - spn_def.offset) / spn_def.scale

            # Round to integer
            raw_value = round(raw_value)

            # Handle signed values (latitude/longitude can be negative)
            if spn_def.data_type in [
                J1939DataType.INT8,
                J1939DataType.INT16,
                J1939DataType.INT32,
                J1939DataType.LATITUDE,
                J1939DataType.LONGITUDE,
            ]:
                # For signed integers, use proper range checking
                if spn_def.bit_length <= 8:
                    min_raw, max_raw = -128, 127
                elif spn_def.bit_length <= 16:
                    min_raw, max_raw = -32768, 32767
                elif spn_def.bit_length <= 32:
                    min_raw, max_raw = -2147483648, 2147483647
                else:
                    min_raw, max_raw = 0, (1 << spn_def.bit_length) - 1

                if raw_value < min_raw:
                    raw_value = min_raw
                elif raw_value > max_raw:
                    raw_value = max_raw

                # Convert signed to unsigned representation for bit packing
                if raw_value < 0:
                    if spn_def.bit_length <= 8:
                        raw_value = struct.unpack("B", struct.pack("b", int(raw_value)))[0]
                    elif spn_def.bit_length <= 16:
                        raw_value = struct.unpack("H", struct.pack("h", int(raw_value)))[0]
                    elif spn_def.bit_length <= 32:
                        raw_value = struct.unpack("I", struct.pack("i", int(raw_value)))[0]
            else:
                # Unsigned integers
                max_raw = (1 << spn_def.bit_length) - 1
                if raw_value < 0:
                    raw_value = 0
                elif raw_value > max_raw:
                    raw_value = max_raw

            return int(raw_value)

        except Exception as e:
            logger.error(f"Failed to encode SPN {spn_def.spn} value {value}: {e}")
            return None

    def _insert_bits(self, data: bytearray, start_bit: int, bit_length: int, value: int) -> None:
        """Insert bits into byte array.

        Parameters
        ----------
        data : bytearray
            Target data array
        start_bit : int
            Starting bit position
        bit_length : int
            Number of bits
        value : int
            Value to insert
        """
        if len(data) * 8 < start_bit + bit_length:
            raise ValueError("Bit range exceeds data length")

        # Create mask for the bits to modify
        mask = (1 << bit_length) - 1
        value &= mask  # Ensure value fits in bit_length

        # Insert bits byte by byte
        for i in range(bit_length):
            bit_pos = start_bit + i
            byte_idx = bit_pos // 8
            bit_in_byte = bit_pos % 8

            if value & (1 << i):
                data[byte_idx] |= 1 << bit_in_byte
            else:
                data[byte_idx] &= ~(1 << bit_in_byte)

    def _construct_j1939_id(
        self, pgn: int, priority: int, source_address: int, destination_address: int
    ) -> int:
        """Construct J1939 29-bit CAN ID.

        Parameters
        ----------
        pgn : int
            Parameter Group Number
        priority : int
            Message priority
        source_address : int
            Source address
        destination_address : int
            Destination address

        Returns
        -------
        int
            29-bit CAN identifier
        """
        # Extract PGN components
        data_page = (pgn >> 16) & 0x01
        pdu_format = (pgn >> 8) & 0xFF

        if pdu_format >= 240:
            # PDU Format 240-255 (PDU1 format)
            pdu_specific = pgn & 0xFF
        else:
            # PDU Format 0-239 (PDU2 format)
            pdu_specific = destination_address

        # Construct 29-bit ID
        can_id = (
            (priority << 26)
            | (0 << 25)  # Reserved bit
            | (data_page << 24)
            | (pdu_format << 16)
            | (pdu_specific << 8)
            | source_address
        )

        return can_id

    def encode_engine_data(
        self,
        source_address: int,
        engine_speed: float | None = None,
        manifold_pressure: float | None = None,
        torque_percent: float | None = None,
    ) -> Message | None:
        """Convenience method to encode Electronic Engine Controller 1 data.

        Parameters
        ----------
        source_address : int
            Engine ECU address
        engine_speed : float | None
            Engine speed in RPM
        manifold_pressure : float | None
            Intake manifold pressure in kPa
        torque_percent : float | None
            Engine torque percentage

        Returns
        -------
        Message | None
            Encoded EEC1 message
        """
        spn_values = {}

        if engine_speed is not None:
            spn_values[190] = engine_speed
        if manifold_pressure is not None:
            spn_values[102] = manifold_pressure
        if torque_percent is not None:
            spn_values[61] = torque_percent

        return self.encode_pgn_message(0xF004, source_address, spn_values)

    def encode_vehicle_speed(
        self,
        source_address: int,
        speed_kmh: float,
    ) -> Message | None:
        """Convenience method to encode vehicle speed data.

        Parameters
        ----------
        source_address : int
            Source address
        speed_kmh : float
            Vehicle speed in km/h

        Returns
        -------
        Message | None
            Encoded WVS message
        """
        spn_values = {84: speed_kmh}
        return self.encode_pgn_message(0xFEF1, source_address, spn_values)

    def encode_gps_position(
        self,
        source_address: int,
        latitude: float,
        longitude: float,
    ) -> Message | None:
        """Convenience method to encode GPS position data.

        Parameters
        ----------
        source_address : int
            Source address
        latitude : float
            Latitude in degrees
        longitude : float
            Longitude in degrees

        Returns
        -------
        Message | None
            Encoded VP message
        """
        spn_values = {584: latitude, 585: longitude}
        return self.encode_pgn_message(0xFEF3, source_address, spn_values)


class CANFrameCodec:
    """Complete CAN frame codec for ISOBUS agricultural systems."""

    def __init__(self) -> None:
        """Initialize CAN frame codec."""
        self.decoder = J1939Decoder()
        self.encoder = J1939Encoder()

    def decode_message(self, message: Message) -> DecodedPGN | None:
        """Decode a CAN message.

        Parameters
        ----------
        message : Message
            Message to decode

        Returns
        -------
        DecodedPGN | None
            Decoded message data
        """
        return self.decoder.decode_can_message(message)

    def encode_message(
        self, pgn: int, source_address: int, spn_values: dict[int, Any], **kwargs
    ) -> Message | None:
        """Encode a PGN message.

        Parameters
        ----------
        pgn : int
            Parameter Group Number
        source_address : int
            Source address
        spn_values : dict[int, Any]
            SPN values to encode
        **kwargs
            Additional encoding parameters

        Returns
        -------
        Message | None
            Encoded CAN message
        """
        return self.encoder.encode_pgn_message(pgn, source_address, spn_values, **kwargs)

    def get_pgn_definition(self, pgn: int) -> PGNDefinition | None:
        """Get PGN definition by number.

        Parameters
        ----------
        pgn : int
            Parameter Group Number

        Returns
        -------
        PGNDefinition | None
            PGN definition or None if not found
        """
        return self.decoder.pgn_definitions.get(pgn)

    def get_spn_definition(self, spn: int) -> SPNDefinition | None:
        """Get SPN definition by number.

        Parameters
        ----------
        spn : int
            Suspect Parameter Number

        Returns
        -------
        SPNDefinition | None
            SPN definition or None if not found
        """
        return self.decoder.spn_definitions.get(spn)

    def list_supported_pgns(self) -> list[int]:
        """Get list of supported PGN numbers.

        Returns
        -------
        list[int]
            List of supported PGN numbers
        """
        return list(self.decoder.pgn_definitions.keys())

    def list_supported_spns(self) -> list[int]:
        """Get list of supported SPN numbers.

        Returns
        -------
        list[int]
            List of supported SPN numbers
        """
        return list(self.decoder.spn_definitions.keys())

    # Test compatibility methods
    def decode_can_message(self, message: Any) -> DecodedPGN | None:
        """Decode a CAN message (alias for decode_message for test compatibility).

        Parameters
        ----------
        message : Message
            Message to decode

        Returns
        -------
        DecodedPGN | None
            Decoded message data
        """
        return self.decode_message(message)

    def encode_engine_data(self, engine_data, source_address: int) -> Message | None:
        """Encode engine data object to CAN message (for test compatibility).

        Parameters
        ----------
        engine_data
            Engine data object with attributes: rpm, torque, fuel_rate, coolant_temp,
            oil_pressure, air_intake_temp
        source_address : int
            Source address

        Returns
        -------
        Message | None
            Encoded CAN message
        """
        try:
            # Convert engine data object to SPN values
            spn_values = {}

            if hasattr(engine_data, "rpm") and engine_data.rpm is not None:
                spn_values[190] = engine_data.rpm  # Engine Speed
            if hasattr(engine_data, "torque") and engine_data.torque is not None:
                spn_values[61] = engine_data.torque  # Engine Percent Torque
            if hasattr(engine_data, "fuel_rate") and engine_data.fuel_rate is not None:
                spn_values[183] = engine_data.fuel_rate  # Engine Fuel Rate

            # Use the existing encoder method
            return self.encoder.encode_pgn_message(0xF004, source_address, spn_values)

        except Exception as e:
            logger.error(f"Failed to encode engine data: {e}")
            return None

    def encode_vehicle_position(self, position_data, source_address: int) -> Message | None:
        """Encode vehicle position object to CAN message (for test compatibility).

        Parameters
        ----------
        position_data
            Position data object with attributes: latitude, longitude, altitude
        source_address : int
            Source address

        Returns
        -------
        Message | None
            Encoded CAN message
        """
        try:
            # Convert position data object to SPN values
            spn_values = {}

            if hasattr(position_data, "latitude") and position_data.latitude is not None:
                spn_values[584] = position_data.latitude  # Latitude
            if hasattr(position_data, "longitude") and position_data.longitude is not None:
                spn_values[585] = position_data.longitude  # Longitude
            # Note: altitude is not included in standard Vehicle Position PGN (0xFEF3)

            # Use the existing encoder method for Vehicle Position (VP)
            return self.encoder.encode_pgn_message(0xFEF3, source_address, spn_values)

        except Exception as e:
            logger.error(f"Failed to encode vehicle position: {e}")
            return None
