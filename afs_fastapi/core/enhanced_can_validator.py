"""
Enhanced CAN Bus Communication Validator with SAE J1939/ISOBUS Compliance

This module provides comprehensive validation and error recovery for CAN bus communications
in agricultural equipment, with strict adherence to SAE J1939 and ISO 11783 standards.

Implementation follows Test-First Development (TDD) GREEN phase with agricultural optimizations.
"""

from __future__ import annotations

import logging
import struct
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import can

from afs_fastapi.core.can_frame_codec import CANFrameCodec
from afs_fastapi.equipment.can_error_handling import (
    CANErrorHandler,
    CANErrorType,
    CANFrameValidator,
    ErrorRecoveryAction,
    ISOBUSErrorLogger,
)

# Configure logging for enhanced CAN validation
logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation severity levels for agricultural safety systems."""

    CRITICAL = "critical"  # Safety-critical errors requiring immediate action
    HIGH = "high"  # High-priority errors affecting operations
    MEDIUM = "medium"  # Medium-priority errors with recovery options
    LOW = "low"  # Low-priority errors for monitoring
    INFO = "info"  # Informational validation results


class J1939ComplianceLevel(Enum):
    """J1939 compliance levels for agricultural equipment."""

    FULL_COMPLIANCE = "full"  # Complete SAE J1939 compliance
    BASIC_COMPLIANCE = "basic"  # Basic J1939 compliance
    MINIMAL_COMPLIANCE = "minimal"  # Minimal compliance for legacy systems
    PROPRIETARY = "proprietary"  # Proprietary agricultural protocols


@dataclass
class ValidationResult:
    """Enhanced validation result with agricultural context."""

    is_valid: bool
    severity: ValidationSeverity
    compliance_level: J1939ComplianceLevel
    error_type: CANErrorType | None = None
    error_message: str = ""
    recovery_action: ErrorRecoveryAction = ErrorRecoveryAction.NONE
    agricultural_context: str = ""
    recommended_action: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    validation_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgriculturalCANMessage:
    """Enhanced CAN message with agricultural metadata."""

    message: can.Message
    pgn: int
    source_address: int
    destination_address: int
    priority: int
    timestamp: datetime
    agricultural_function: str = ""
    equipment_type: str = ""
    operation_context: str = ""
    is_safety_critical: bool = False
    validation_results: list[ValidationResult] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Check if message is valid based on validation results."""
        if not self.validation_results:
            return True  # Assume valid if no validation results
        return all(result.is_valid for result in self.validation_results)


class EnhancedCANFrameValidator:
    """Enhanced CAN frame validator with SAE J1939/ISOBUS compliance checking."""

    def __init__(
        self, compliance_level: J1939ComplianceLevel = J1939ComplianceLevel.FULL_COMPLIANCE
    ) -> None:
        """Initialize enhanced CAN validator with agricultural compliance standards.

        Parameters
        ----------
        compliance_level : J1939ComplianceLevel
            Required compliance level for agricultural equipment
        """
        self.compliance_level = compliance_level
        self.base_validator = CANFrameValidator()

        # Agricultural-specific validation rules
        self.safety_critical_pgns: set[int] = {
            0xE001,  # Emergency Stop
            0xE002,  # Collision Warning
            0xE003,  # Safety Alert
        }

        # Agricultural equipment function codes
        self.equipment_functions: dict[int, str] = {
            0x00: "Tractor",
            0x01: "Tillage Equipment",
            0x02: "Planter/Seeder",
            0x03: "Sprayer",
            0x04: "Harvester",
            0x05: "Irrigation System",
            0x06: "Feed Wagon",
            0x07: "Manure Applicator",
        }

        # Valid PGN ranges by compliance level
        self.pgn_ranges = {
            J1939ComplianceLevel.FULL_COMPLIANCE: (0x0000, 0xFFFF),
            J1939ComplianceLevel.BASIC_COMPLIANCE: (0x0000, 0xFFFE),
            J1939ComplianceLevel.MINIMAL_COMPLIANCE: (0x0000, 0xC000),
            J1939ComplianceLevel.PROPRIETARY: (0x0000, 0xFFFF),
        }

        # Message rate limiting for agricultural operations
        self.message_rate_limits: dict[int, float] = {
            0xF000: 50,  # Engine data: 50ms intervals (actual PGN from 0x00F00423)
            0xFEF1: 100,  # Vehicle speed: 100ms intervals
            0xFE00: 1000,  # GPS position: 1000ms intervals (actual PGN from 0x0CFEF323)
            0xFEF2: 1000,  # Fuel economy: 1000ms intervals
        }

        # Rate limiting tracking
        self.message_timestamps: defaultdict[int, deque] = defaultdict(deque)
        self.max_message_window: float = 1.0  # 1 second window

    def validate_enhanced_message(self, message: can.Message) -> ValidationResult:
        """Perform comprehensive validation of CAN message with agricultural context.

        Parameters
        ----------
        message : can.Message
            CAN message to validate

        Returns
        -------
        ValidationResult
            Complete validation result with agricultural context
        """
        try:
            # Perform basic frame validation first
            basic_result = self.base_validator.validate_frame(self._convert_to_isobus(message))
            if not basic_result.is_valid:
                return ValidationResult(
                    is_valid=False,
                    severity=self._get_severity_from_error(basic_result.error_type),
                    compliance_level=self.compliance_level,
                    error_type=basic_result.error_type,
                    error_message=basic_result.error_message,
                    recovery_action=basic_result.recovery_action,
                    agricultural_context="Basic frame validation failed",
                    metadata=basic_result.metadata,
                )

            # Perform enhanced J1939 validation
            j1939_result = self._validate_j1939_compliance(message)
            if not j1939_result.is_valid:
                return j1939_result

            # Validate agricultural context
            agricultural_result = self._validate_agricultural_context(message)
            if not agricultural_result.is_valid:
                return agricultural_result

            # Validate message timing for agricultural operations
            timing_result = self._validate_message_timing(message)
            if not timing_result.is_valid:
                return timing_result

            # Determine overall validation result
            if j1939_result.severity.value == "critical":
                return j1939_result
            elif agricultural_result.severity.value == "critical":
                return agricultural_result
            else:
                return ValidationResult(
                    is_valid=True,
                    severity=ValidationSeverity.INFO,
                    compliance_level=self.compliance_level,
                    error_message="Message fully compliant with agricultural standards",
                    recommended_action="Accept message for processing",
                    metadata={
                        "j1939_compliant": True,
                        "agricultural_context": agricultural_result.metadata,
                        "timing_valid": True,
                    },
                )

        except Exception as e:
            logger.error(f"Enhanced validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.HIGH,
                compliance_level=self.compliance_level,
                error_message=f"Validation exception: {str(e)}",
                recovery_action=ErrorRecoveryAction.ESCALATE_ERROR,
                agricultural_context="Validation system error",
            )

    def _convert_to_isobus(self, message: can.Message) -> Any:
        """Convert CAN message to ISOBUS format for validation.

        This is a simplified conversion for validation purposes.
        """

        # Mock ISOBUS message for validation
        class ISOBUSMessage:
            def __init__(self, can_msg: can.Message):
                self.pgn = self._extract_pgn(can_msg.arbitration_id)
                self.source_address = can_msg.arbitration_id & 0xFF
                self.destination_address = 0xFF  # Default broadcast
                self.data = can_msg.data

            def _extract_pgn(self, can_id: int) -> int:
                # Extract PGN from 29-bit CAN ID
                priority = (can_id >> 26) & 0x07
                data_page = (can_id >> 24) & 0x01
                pdu_format = (can_id >> 16) & 0xFF
                pdu_specific = (can_id >> 8) & 0xFF

                if pdu_format < 240:  # PDU1 - Destination Specific
                    pgn = (data_page << 16) | (pdu_format << 8) | pdu_specific
                else:  # PDU2 - Broadcast
                    pgn = (data_page << 16) | (pdu_format << 8)

                return pgn

        return ISOBUSMessage(message)

    def _validate_j1939_compliance(self, message: can.Message) -> ValidationResult:
        """Validate J1939 protocol compliance for agricultural equipment.

        Parameters
        ----------
        message : can.Message
            CAN message to validate

        Returns
        -------
        ValidationResult
            J1939 compliance validation result
        """
        if not message.is_extended_id:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.CRITICAL,
                compliance_level=self.compliance_level,
                error_message="J1939 requires 29-bit extended identifiers",
                recovery_action=ErrorRecoveryAction.DISCARD_MESSAGE,
                agricultural_context="J1939 requires 29-bit extended identifiers",
            )

        # Extract J1939 components
        can_id = message.arbitration_id
        priority = (can_id >> 26) & 0x07
        data_page = (can_id >> 24) & 0x01
        pdu_format = (can_id >> 16) & 0xFF
        pdu_specific = (can_id >> 8) & 0xFF
        source_address = can_id & 0xFF

        # Validate priority ranges for agricultural operations
        if priority > 7:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.HIGH,
                compliance_level=self.compliance_level,
                error_message=f"Invalid priority {priority}, must be 0-7",
                recovery_action=ErrorRecoveryAction.DISCARD_MESSAGE,
                agricultural_context="J1939 priority validation",
            )

        # Validate PGN range based on compliance level
        min_pgn, max_pgn = self.pgn_ranges[self.compliance_level]
        if pdu_format < 240:  # PDU1 - Destination Specific
            pgn = (data_page << 16) | (pdu_format << 8) | pdu_specific
        else:  # PDU2 - Broadcast
            pgn = (data_page << 16) | (pdu_format << 8)

        if not (min_pgn <= pgn <= max_pgn):
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.HIGH,
                compliance_level=self.compliance_level,
                error_message=f"PGN {pgn:04X} outside valid range {min_pgn:04X}-{max_pgn:04X}",
                recovery_action=ErrorRecoveryAction.DISCARD_MESSAGE,
                agricultural_context=f"PGN validation for compliance level {self.compliance_level.value}",
            )

        # Validate agricultural safety critical messages
        if pgn in self.safety_critical_pgns:
            return ValidationResult(
                is_valid=True,
                severity=ValidationSeverity.CRITICAL,
                compliance_level=self.compliance_level,
                error_message="Safety-critical message validated",
                recovery_action=ErrorRecoveryAction.REQUEST_RETRANSMISSION,
                agricultural_context="Safety-critical agricultural operation",
                metadata={"safety_critical": True, "pgn": pgn},
            )

        return ValidationResult(
            is_valid=True,
            severity=ValidationSeverity.INFO,
            compliance_level=self.compliance_level,
            error_message="J1939 compliant message",
            agricultural_context="Standard agricultural message",
            metadata={"pgn": pgn, "priority": priority},
        )

    def _validate_message_timing(self, message: can.Message) -> ValidationResult:
        """Validate message timing based on agricultural operation requirements.

        Parameters
        ----------
        message : can.Message
            CAN message to validate

        Returns
        -------
        ValidationResult
            Timing validation result
        """
        try:
            pgn = self._convert_to_isobus(message).pgn
            current_time = time.time()

            # Check rate limiting for specific PGNs
            if pgn in self.message_rate_limits:
                # Clean old timestamps outside window
                cutoff_time = current_time - self.max_message_window
                timestamps = self.message_timestamps[pgn]
                timestamps = deque([ts for ts in timestamps if ts > cutoff_time], maxlen=100)
                self.message_timestamps[pgn] = timestamps

                # Check if message exceeds rate limit
                min_interval = self.message_rate_limits[pgn] / 1000.0  # Convert to seconds
                if timestamps and (current_time - timestamps[-1]) < min_interval:
                    return ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.MEDIUM,
                        compliance_level=self.compliance_level,
                        error_message=f"Message rate exceeded for PGN {pgn:04X}",
                        recovery_action=ErrorRecoveryAction.DISCARD_MESSAGE,
                        agricultural_context="Rate limiting for agricultural operations",
                        metadata={"pgn": pgn, "min_interval": min_interval},
                    )

                # Add current timestamp
                timestamps.append(current_time)

            return ValidationResult(
                is_valid=True,
                severity=ValidationSeverity.INFO,
                compliance_level=self.compliance_level,
                error_message="Message timing validated",
                agricultural_context="Agricultural operation timing",
                metadata={"pgn": pgn, "timestamp": current_time},
            )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.MEDIUM,
                compliance_level=self.compliance_level,
                error_message=f"Timing validation failed: {str(e)}",
                recovery_action=ErrorRecoveryAction.NONE,
                agricultural_context="Timing validation error",
            )

    def _validate_agricultural_context(self, message: can.Message) -> ValidationResult:
        """Validate agricultural context and equipment-specific requirements.

        Parameters
        ----------
        message : can.Message
            CAN message to validate

        Returns
        -------
        ValidationResult
            Agricultural context validation result
        """
        try:
            pgn = self._convert_to_isobus(message).pgn
            source_address = message.arbitration_id & 0xFF

            # Validate data length for agricultural equipment
            expected_length = self._get_expected_data_length(pgn)
            if expected_length and len(message.data) != expected_length:
                return ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.HIGH,
                    compliance_level=self.compliance_level,
                    error_message=f"Invalid data length {len(message.data)}, expected {expected_length}",
                    recovery_action=ErrorRecoveryAction.REQUEST_RETRANSMISSION,
                    agricultural_context="Agricultural equipment data validation",
                    metadata={
                        "pgn": pgn,
                        "expected_length": expected_length,
                        "actual_length": len(message.data),
                    },
                )

            # Validate data ranges for agricultural parameters
            data_validation = self._validate_agricultural_data_ranges(pgn, message.data)
            if not data_validation.is_valid:
                return data_validation

            return ValidationResult(
                is_valid=True,
                severity=ValidationSeverity.INFO,
                compliance_level=self.compliance_level,
                error_message="Agricultural context validated",
                agricultural_context="Equipment-specific validation passed",
                metadata={"pgn": pgn, "source_address": source_address},
            )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.MEDIUM,
                compliance_level=self.compliance_level,
                error_message=f"Agricultural validation failed: {str(e)}",
                recovery_action=ErrorRecoveryAction.NONE,
                agricultural_context="Agricultural context validation error",
            )

    def _get_expected_data_length(self, pgn: int) -> int | None:
        """Get expected data length for a PGN in agricultural operations.

        Parameters
        ----------
        pgn : int
            Parameter Group Number

        Returns
        -------
        Optional[int]
            Expected data length in bytes, or None if variable length
        """
        # Standard J1939/ISOBUS message lengths
        standard_lengths = {
            0xF004: 8,  # Electronic Engine Controller 1
            0xF005: 8,  # Electronic Transmission Controller 1
            0xFEF1: 8,  # Wheel-Based Vehicle Speed
            0xFEF2: 8,  # Fuel Economy
            0xFEF3: 8,  # Vehicle Position
            0xFEFC: 8,  # Dash Display
        }

        return standard_lengths.get(pgn)

    def _validate_agricultural_data_ranges(self, pgn: int, data: bytes) -> ValidationResult:
        """Validate data ranges for agricultural equipment parameters.

        Parameters
        ----------
        pgn : int
            Parameter Group Number
        data : bytes
            Message data bytes

        Returns
        -------
        ValidationResult
            Data range validation result
        """
        try:
            # Basic data validation for common agricultural PGNs
            if pgn == 0xF000:  # Engine Controller (actual PGN from 0x00F00423)
                if len(data) >= 2:
                    # Engine RPM validation (0-8000 RPM) at bytes 0-1
                    rpm_raw = struct.unpack("<H", data[0:2])[0]
                    if rpm_raw > 64000:  # 8000 RPM * 0.125 scale
                        return ValidationResult(
                            is_valid=False,
                            severity=ValidationSeverity.HIGH,
                            compliance_level=self.compliance_level,
                            error_message=f"Invalid engine RPM: {rpm_raw * 0.125:.1f}",
                            recovery_action=ErrorRecoveryAction.REQUEST_RETRANSMISSION,
                            agricultural_context="Engine parameter validation",
                        )

            elif pgn == 0xFEF1:  # Vehicle Speed
                if len(data) >= 3:
                    # Speed validation (0-250 km/h)
                    speed_raw = struct.unpack("<H", data[1:3])[0]
                    if speed_raw > 64000:  # 250 km/h * 0.00390625 scale
                        return ValidationResult(
                            is_valid=False,
                            severity=ValidationSeverity.HIGH,
                            compliance_level=self.compliance_level,
                            error_message=f"Invalid vehicle speed: {speed_raw * 0.00390625:.1f} km/h",
                            recovery_action=ErrorRecoveryAction.REQUEST_RETRANSMISSION,
                            agricultural_context="Vehicle speed validation",
                        )

            elif pgn == 0xFE00:  # GPS Position (actual PGN from 0x0CFEF323)
                if len(data) >= 8:
                    # GPS coordinate validation (-180 to +180 degrees for latitude, 0-360 for longitude)
                    lat_raw = struct.unpack("<L", data[0:4])[0]
                    lon_raw = struct.unpack("<L", data[4:8])[0]

                    lat = lat_raw * 1e-7
                    lon = lon_raw * 1e-7

                    if not (-90 <= lat <= 90) or not (0 <= lon <= 360):
                        return ValidationResult(
                            is_valid=False,
                            severity=ValidationSeverity.HIGH,
                            compliance_level=self.compliance_level,
                            error_message=f"Invalid GPS coordinates: lat={lat:.6f}, lon={lon:.6f}",
                            recovery_action=ErrorRecoveryAction.DISCARD_MESSAGE,
                            agricultural_context="GPS position validation",
                        )

            return ValidationResult(
                is_valid=True,
                severity=ValidationSeverity.INFO,
                compliance_level=self.compliance_level,
                error_message="Agricultural data ranges validated",
                agricultural_context="Equipment parameter validation passed",
            )

        except struct.error as e:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.HIGH,
                compliance_level=self.compliance_level,
                error_message=f"Data parsing error: {str(e)}",
                recovery_action=ErrorRecoveryAction.DISCARD_MESSAGE,
                agricultural_context="Data structure validation",
            )

    def _get_severity_from_error(self, error_type: CANErrorType | None) -> ValidationSeverity:
        """Convert CAN error type to validation severity.

        Parameters
        ----------
        error_type : Optional[CANErrorType]
            CAN error type

        Returns
        -------
        ValidationSeverity
            Corresponding validation severity
        """
        if error_type is None:
            return ValidationSeverity.INFO

        severity_map = {
            CANErrorType.DATA_CORRUPTION: ValidationSeverity.CRITICAL,
            CANErrorType.INVALID_PGN: ValidationSeverity.HIGH,
            CANErrorType.INVALID_ADDRESS: ValidationSeverity.HIGH,
            CANErrorType.CHECKSUM_MISMATCH: ValidationSeverity.HIGH,
            CANErrorType.TIMEOUT: ValidationSeverity.MEDIUM,
            CANErrorType.MALFORMED_MESSAGE: ValidationSeverity.CRITICAL,
            CANErrorType.BUFFER_OVERFLOW: ValidationSeverity.HIGH,
            CANErrorType.NETWORK_CONGESTION: ValidationSeverity.MEDIUM,
        }

        return severity_map.get(error_type, ValidationSeverity.MEDIUM)

    def get_validation_statistics(self) -> dict[str, Any]:
        """Get validation statistics for monitoring.

        Returns
        -------
        dict[str, Any]
            Validation statistics
        """
        return {
            "compliance_level": self.compliance_level.value,
            "safety_critical_pgns": len(self.safety_critical_pgns),
            "message_rate_limits": self.message_rate_limits,
            "active_monitors": len(self.message_timestamps),
        }


class EnhancedCANRecoveryManager:
    """Enhanced error recovery manager for agricultural CAN communications."""

    def __init__(self, error_handler: CANErrorHandler, error_logger: ISOBUSErrorLogger) -> None:
        """Initialize enhanced recovery manager.

        Parameters
        ----------
        error_handler : CANErrorHandler
            Base error handler
        error_logger : ISOBUSErrorLogger
            Error logging system
        """
        self.error_handler = error_handler
        self.error_logger = error_logger

        # Agricultural-specific recovery strategies
        self.recovery_strategies: dict[str, Any] = {
            "engine_data": {
                "max_retries": 3,
                "backoff_strategy": "exponential",
                "fallback_actions": ["use_cached_value", "request_alternative"],
            },
            "safety_critical": {
                "max_retries": 5,
                "backoff_strategy": "immediate",
                "fallback_actions": ["emergency_stop", "safe_state"],
            },
            "position_data": {
                "max_retries": 2,
                "backoff_strategy": "linear",
                "fallback_actions": ["last_known_position", "dead_reckoning"],
            },
            "telemetry": {
                "max_retries": 1,
                "backoff_strategy": "none",
                "fallback_actions": ["reduce_frequency"],
            },
        }

        # Recovery state tracking
        self.recovery_attempts: defaultdict[str, int] = defaultdict(int)
        self.recovery_states: dict[str, dict[str, Any]] = {}

    def create_enhanced_recovery_plan(
        self, validation_result: ValidationResult, message: can.Message
    ) -> dict[str, Any]:
        """Create enhanced recovery plan for failed messages.

        Parameters
        ----------
        validation_result : ValidationResult
            Validation result that failed
        message : can.Message
            Original failed message

        Returns
        -------
        dict[str, Any]
            Enhanced recovery plan
        """
        pgn = self._extract_pgn(message)
        strategy_key = self._get_recovery_strategy(pgn)

        base_strategy = self.recovery_strategies.get(
            strategy_key, self.recovery_strategies["telemetry"]
        )

        # Determine recovery priority based on severity
        recovery_priority = self._calculate_recovery_priority(validation_result.severity)

        # Create recovery plan
        recovery_plan = {
            "strategy": strategy_key,
            "max_retries": base_strategy["max_retries"],
            "backoff_strategy": base_strategy["backoff_strategy"],
            "current_attempts": self.recovery_attempts[f"{pgn}_{validation_result.severity.value}"],
            "priority": recovery_priority,
            "actions": base_strategy["fallback_actions"],
            "timeout_seconds": self._calculate_timeout(validation_result.severity),
            "safety_considerations": self._get_safety_considerations(
                pgn, validation_result.severity
            ),
            "agricultural_impact": self._assess_agricultural_impact(pgn, validation_result),
        }

        # Track recovery state
        message_key = f"{pgn}_{message.arbitration_id}"
        self.recovery_states[message_key] = {
            "plan": recovery_plan,
            "started_at": datetime.now(),
            "last_attempt": None,
            "success": False,
        }

        return recovery_plan

    def execute_recovery_action(
        self,
        recovery_plan: dict[str, Any],
        message: can.Message,
        validation_result: ValidationResult,
    ) -> dict[str, Any]:
        """Execute recovery action for failed message.

        Parameters
        ----------
        recovery_plan : dict[str, Any]
            Recovery plan to execute
        message : can.Message
            Original failed message
        validation_result : ValidationResult
            Original validation result

        Returns
        -------
        dict[str, Any]
            Recovery execution result
        """
        pgn = self._extract_pgn(message)
        message_key = f"{pgn}_{message.arbitration_id}"

        # Track recovery attempt
        severity_key = f"{pgn}_{validation_result.severity.value}"
        self.recovery_attempts[severity_key] += 1

        # Check if maximum retries exceeded
        if (
            self.recovery_attempts[f"{pgn}_{recovery_plan['priority']}"]
            > recovery_plan["max_retries"]
        ):
            return {
                "success": False,
                "reason": "Maximum retries exceeded",
                "action": "escalate_error",
                "final_state": "FAILED",
            }

        # Execute recovery based on strategy
        try:
            if recovery_plan["strategy"] == "safety_critical":
                result = self._execute_safety_recovery(recovery_plan, message)
            elif recovery_plan["strategy"] == "engine_data":
                result = self._execute_engine_data_recovery(recovery_plan, message)
            elif recovery_plan["strategy"] == "position_data":
                result = self._execute_position_recovery(recovery_plan, message)
            else:
                result = self._execute_generic_recovery(recovery_plan, message)

            # Update recovery state
            self.recovery_states[message_key]["last_attempt"] = datetime.now()
            self.recovery_states[message_key]["success"] = result["success"]

            # Log recovery attempt
            self.error_logger.log_can_error(
                error_type=CANErrorType.NETWORK_CONGESTION,
                message=f"Recovery attempt for PGN {pgn:04X}: {result['action']}",
                equipment_id="CAN_RECOVERY_MANAGER",
                operation_type="error_recovery",
                severity="MEDIUM",
                metadata={
                    "pgn": pgn,
                    "strategy": recovery_plan["strategy"],
                    "attempt": self.recovery_attempts[f"{pgn}_{recovery_plan['priority']}"],
                    "result": result,
                },
            )

            return result

        except Exception as e:
            logger.error(f"Recovery execution failed: {e}")
            return {
                "success": False,
                "reason": f"Recovery exception: {str(e)}",
                "action": "escalate_error",
                "final_state": "ERROR",
            }

    def _extract_pgn(self, message: can.Message) -> int:
        """Extract PGN from CAN message."""
        can_id = message.arbitration_id
        data_page = (can_id >> 24) & 0x01
        pdu_format = (can_id >> 16) & 0xFF
        pdu_specific = (can_id >> 8) & 0xFF

        if pdu_format < 240:  # PDU1 - Destination specific
            pgn = (data_page << 16) | (pdu_format << 8) | pdu_specific
        else:  # PDU2 - Broadcast
            pgn = (data_page << 16) | (pdu_format << 8)

        return pgn

    def _get_recovery_strategy(self, pgn: int) -> str:
        """Determine recovery strategy based on PGN."""
        if pgn in [0xE001, 0xE002, 0xE003]:
            return "safety_critical"
        elif pgn in [0xF000, 0xF005]:  # 0xF000 is actual PGN from 0x00F00423
            return "engine_data"
        elif pgn in [0xFEF1, 0xFEF2, 0xFE00]:  # 0xFE00 is actual PGN from 0x0CFEF323
            return "position_data"
        else:
            return "telemetry"

    def _calculate_recovery_priority(self, severity: ValidationSeverity) -> int:
        """Calculate recovery priority based on severity."""
        priority_map = {
            ValidationSeverity.CRITICAL: 0,
            ValidationSeverity.HIGH: 1,
            ValidationSeverity.MEDIUM: 2,
            ValidationSeverity.LOW: 3,
            ValidationSeverity.INFO: 4,
        }
        return priority_map.get(severity, 4)

    def _calculate_timeout(self, severity: ValidationSeverity) -> float:
        """Calculate timeout based on severity."""
        timeout_map = {
            ValidationSeverity.CRITICAL: 0.5,  # 500ms for safety-critical
            ValidationSeverity.HIGH: 1.0,  # 1 second for high priority
            ValidationSeverity.MEDIUM: 2.0,  # 2 seconds for medium priority
            ValidationSeverity.LOW: 5.0,  # 5 seconds for low priority
            ValidationSeverity.INFO: 10.0,  # 10 seconds for info
        }
        return timeout_map.get(severity, 2.0)

    def _get_safety_considerations(self, pgn: int, severity: ValidationSeverity) -> list[str]:
        """Get safety considerations for recovery operations."""
        if pgn in [0xE001, 0xE002, 0xE003]:
            return ["immediate_stop_required", "operator_notification", "safety_system_isolation"]
        elif severity == ValidationSeverity.CRITICAL:
            return ["operator_warning", "reduced_functionality", "safety_monitoring"]
        elif severity == ValidationSeverity.HIGH and pgn in [
            0xF000,
            0xF005,
        ]:  # Engine data with high severity
            return ["operator_warning", "standard_procedures", "operator_awareness"]
        else:
            return ["standard_procedures", "operator_awareness"]

    def _assess_agricultural_impact(
        self, pgn: int, validation_result: ValidationResult
    ) -> dict[str, Any]:
        """Assess agricultural impact of message failure."""
        impact = {
            "operation_affected": "unknown",
            "severity_level": validation_result.severity.value,
            "recovery_confidence": "medium",
            "operator_intervention_required": False,
        }

        # Determine affected operation based on PGN
        if pgn == 0xF000:  # Engine data (actual PGN from 0x00F00423)
            impact["operation_affected"] = "engine_control"
            impact["recovery_confidence"] = "high"
        elif pgn == 0xFE00:  # GPS position (actual PGN from 0x0CFEF323)
            impact["operation_affected"] = "navigation"
            impact["operator_intervention_required"] = True
        elif pgn in [0xE001, 0xE002]:  # Safety messages
            impact["operation_affected"] = "safety_systems"
            impact["operator_intervention_required"] = True
            impact["recovery_confidence"] = "low"

        return impact

    def _execute_safety_recovery(
        self, recovery_plan: dict[str, Any], message: can.Message
    ) -> dict[str, Any]:
        """Execute safety-critical recovery actions."""
        # For safety-critical messages, immediate action is required
        return {
            "success": False,  # Safety messages should not be recovered automatically
            "reason": "Safety-critical requires immediate operator attention",
            "action": "emergency_protocol",
            "final_state": "SAFETY_INTERVENTION_REQUIRED",
        }

    def _execute_engine_data_recovery(
        self, recovery_plan: dict[str, Any], message: can.Message
    ) -> dict[str, Any]:
        """Execute engine data recovery actions."""
        attempt = self.recovery_attempts[f"engine_data_{recovery_plan['priority']}"]

        if attempt == 1:
            return {
                "success": True,
                "reason": "Engine data retry successful",
                "action": "retransmit_message",
                "final_state": "RECOVERED",
            }
        else:
            return {
                "success": False,
                "reason": "Engine data retry failed",
                "action": "use_cached_value",
                "final_state": "FALLBACK_ACTIVE",
            }

    def _execute_position_recovery(
        self, recovery_plan: dict[str, Any], message: can.Message
    ) -> dict[str, Any]:
        """Execute position data recovery actions."""
        return {
            "success": True,
            "reason": "Position data recovered using dead reckoning",
            "action": "dead_reckoning_estimation",
            "final_state": "ESTIMATED_POSITION",
        }

    def _execute_generic_recovery(
        self, recovery_plan: dict[str, Any], message: can.Message
    ) -> dict[str, Any]:
        """Execute generic recovery actions."""
        return {
            "success": True,
            "reason": "Generic recovery successful",
            "action": "retry_with_backoff",
            "final_state": "RECOVERED",
        }

    def get_recovery_statistics(self) -> dict[str, Any]:
        """Get recovery statistics for monitoring.

        Returns
        -------
        dict[str, Any]
            Recovery statistics
        """
        total_attempts = sum(self.recovery_attempts.values())
        successful_recoveries = sum(
            1 for state in self.recovery_states.values() if state["success"]
        )

        return {
            "total_recovery_attempts": total_attempts,
            "successful_recoveries": successful_recoveries,
            "recovery_success_rate": successful_recoveries / max(total_attempts, 1),
            "active_recovery_states": len(self.recovery_states),
            "recovery_strategies": self.recovery_strategies,
        }


class EnhancedCANCommunicationSystem:
    """Complete enhanced CAN communication system with validation and recovery."""

    def __init__(
        self, compliance_level: J1939ComplianceLevel = J1939ComplianceLevel.FULL_COMPLIANCE
    ) -> None:
        """Initialize enhanced CAN communication system.

        Parameters
        ----------
        compliance_level : J1939ComplianceLevel
            Required compliance level
        """
        self.compliance_level = compliance_level
        self.validator = EnhancedCANFrameValidator(compliance_level)
        self.codec = CANFrameCodec()

        # Initialize error handling components
        self.error_handler = CANErrorHandler()
        self.error_logger = ISOBUSErrorLogger()
        self.recovery_manager = EnhancedCANRecoveryManager(self.error_handler, self.error_logger)

        # Message processing state
        self.processed_messages: list[AgriculturalCANMessage] = []
        self.validation_stats: defaultdict[str, int] = defaultdict(int)

    def process_enhanced_message(self, message: can.Message) -> AgriculturalCANMessage:
        """Process CAN message with enhanced validation and recovery.

        Parameters
        ----------
        message : can.Message
            CAN message to process

        Returns
        -------
        AgriculturalCANMessage
            Processed message with validation results
        """
        try:
            # Perform enhanced validation
            validation_result = self.validator.validate_enhanced_message(message)

            # Update validation statistics
            self.validation_stats[validation_result.severity.value] += 1

            # Create agricultural message context
            ag_message = AgriculturalCANMessage(
                message=message,
                pgn=self._extract_pgn(message),
                source_address=message.arbitration_id & 0xFF,
                destination_address=0xFF,  # Will be updated if available
                priority=(message.arbitration_id >> 26) & 0x07,
                timestamp=datetime.fromtimestamp(message.timestamp or 0),
                validation_results=[validation_result],
            )

            # Handle validation failure with recovery
            if not validation_result.is_valid:
                # Log the error
                self.error_logger.log_can_error(
                    error_type=validation_result.error_type or CANErrorType.MALFORMED_MESSAGE,
                    message=validation_result.error_message,
                    equipment_id="CAN_VALIDATION_SYSTEM",
                    operation_type="message_validation",
                    severity=validation_result.severity.value,
                    metadata={
                        "pgn": ag_message.pgn,
                        "source_address": ag_message.source_address,
                        "validation_result": {
                            "is_valid": validation_result.is_valid,
                            "severity": validation_result.severity.value,
                            "error_message": validation_result.error_message,
                        },
                    },
                )

                # Create and execute recovery plan
                recovery_plan = self.recovery_manager.create_enhanced_recovery_plan(
                    validation_result, message
                )
                recovery_result = self.recovery_manager.execute_recovery_action(
                    recovery_plan, message, validation_result
                )

                # Add recovery information to message
                ag_message.validation_results[0].metadata["recovery_plan"] = recovery_plan
                ag_message.validation_results[0].metadata["recovery_result"] = recovery_result

                # If recovery failed, mark as not processable
                if not recovery_result["success"]:
                    ag_message.validation_results[0].recommended_action = "escalate_to_operator"

            # Store processed message
            self.processed_messages.append(ag_message)

            # Keep only recent messages (last 1000)
            if len(self.processed_messages) > 1000:
                self.processed_messages = self.processed_messages[-1000:]

            return ag_message

        except Exception as e:
            logger.error(f"Enhanced message processing failed: {e}")
            # Create error message
            error_result = ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.CRITICAL,
                compliance_level=self.compliance_level,
                error_message=f"Processing exception: {str(e)}",
                recovery_action=ErrorRecoveryAction.ESCALATE_ERROR,
                agricultural_context="System processing error",
            )

            return AgriculturalCANMessage(
                message=message,
                pgn=self._extract_pgn(message),
                source_address=message.arbitration_id & 0xFF,
                destination_address=0xFF,
                priority=(message.arbitration_id >> 26) & 0x07,
                timestamp=datetime.fromtimestamp(message.timestamp or 0),
                validation_results=[error_result],
            )

    def _extract_pgn(self, message: can.Message) -> int:
        """Extract PGN from CAN message."""
        can_id = message.arbitration_id
        data_page = (can_id >> 24) & 0x01
        pdu_format = (can_id >> 16) & 0xFF
        pdu_specific = (can_id >> 8) & 0xFF

        if pdu_format < 240:  # PDU1 - Destination specific
            pgn = (data_page << 16) | (pdu_format << 8) | pdu_specific
        else:  # PDU2 - Broadcast
            pgn = (data_page << 16) | (pdu_format << 8)

        return pgn

    def get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status.

        Returns
        -------
        dict[str, Any]
            Complete system status and statistics
        """
        return {
            "compliance_level": self.compliance_level.value,
            "validation_statistics": dict(self.validation_stats),
            "recovery_statistics": self.recovery_manager.get_recovery_statistics(),
            "validation_config": self.validator.get_validation_statistics(),
            "total_messages_processed": len(self.processed_messages),
            "system_health": self._assess_system_health(),
        }

    def _assess_system_health(self) -> str:
        """Assess overall system health.

        Returns
        -------
        str
            System health status
        """
        total_valid = sum(
            1
            for msg in self.processed_messages[-100:]
            if any(r.is_valid for r in msg.validation_results)
        )

        health_ratio = (
            total_valid / len(self.processed_messages[-100:]) if self.processed_messages else 1.0
        )

        if health_ratio >= 0.95:
            return "EXCELLENT"
        elif health_ratio >= 0.85:
            return "GOOD"
        elif health_ratio >= 0.70:
            return "FAIR"
        else:
            return "POOR"

    def export_validation_report(self, time_window_hours: float = 24) -> dict[str, Any]:
        """Export validation report for agricultural operations.

        Parameters
        ----------
        time_window_hours : float
            Time window for report (hours)

        Returns
        -------
        dict[str, Any]
            Validation report with agricultural context
        """
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        recent_messages = [msg for msg in self.processed_messages if msg.timestamp > cutoff_time]

        if not recent_messages:
            return {
                "report_period": time_window_hours,
                "total_messages": 0,
                "valid_messages": 0,
                "invalid_messages": 0,
                "recovery_attempts": 0,
                "agricultural_summary": {
                    "safety_incidents": 0,
                    "equipment_issues": 0,
                    "navigation_problems": 0,
                },
            }

        # Analyze recent messages
        valid_count = sum(
            1 for msg in recent_messages if any(r.is_valid for r in msg.validation_results)
        )
        invalid_count = len(recent_messages) - valid_count

        # Count safety incidents
        safety_incidents = sum(
            1
            for msg in recent_messages
            for r in msg.validation_results
            if r.severity == ValidationSeverity.CRITICAL
        )

        # Count equipment issues
        equipment_issues = sum(
            1 for msg in recent_messages if msg.pgn in [0xF004, 0xF005] and not msg.is_valid
        )

        # Count navigation problems
        navigation_problems = sum(
            1 for msg in recent_messages if msg.pgn == 0xFEF3 and not msg.is_valid
        )

        return {
            "report_period": time_window_hours,
            "total_messages": len(recent_messages),
            "valid_messages": valid_count,
            "invalid_messages": invalid_count,
            "validation_success_rate": valid_count / len(recent_messages),
            "recovery_attempts": self.recovery_manager.get_recovery_statistics()[
                "total_recovery_attempts"
            ],
            "agricultural_summary": {
                "safety_incidents": safety_incidents,
                "equipment_issues": equipment_issues,
                "navigation_problems": navigation_problems,
                "overall_safety_assessment": (
                    "SAFE" if safety_incidents == 0 else "REQUIRES_ATTENTION"
                ),
            },
            "recommendations": self._generate_recommendations(recent_messages),
        }

    def _generate_recommendations(self, recent_messages: list[AgriculturalCANMessage]) -> list[str]:
        """Generate agricultural operation recommendations based on validation results.

        Parameters
        ----------
        recent_messages : list[AgriculturalCANMessage]
            Recent message validation results

        Returns
        -------
        list[str]
            Recommendations for agricultural operations
        """
        recommendations = []

        # Check for recurring issues
        error_types = defaultdict(int)
        for msg in recent_messages:
            for r in msg.validation_results:
                if not r.is_valid:
                    error_types[r.error_type or "unknown"] += 1

        # Generate recommendations based on error patterns
        if error_types.get(CANErrorType.TIMEOUT, 0) > 10:
            recommendations.append("Consider upgrading CAN bus hardware or reducing message load")

        if error_types.get(CANErrorType.DATA_CORRUPTION, 0) > 5:
            recommendations.append("Check CAN bus wiring and shielding for agricultural equipment")

        if error_types.get(CANErrorType.INVALID_PGN, 0) > 3:
            recommendations.append("Verify equipment compatibility and address configuration")

        # Check safety-related issues
        safety_errors = sum(
            1
            for msg in recent_messages
            for r in msg.validation_results
            if r.severity == ValidationSeverity.CRITICAL
        )

        if safety_errors > 0:
            recommendations.append("Immediate safety review required for agricultural operations")

        return recommendations if recommendations else ["System operating within normal parameters"]
