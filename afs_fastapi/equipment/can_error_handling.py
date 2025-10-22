"""
CAN message error handling framework for production agricultural operations.

This module provides comprehensive error handling for corrupted, malformed, and
invalid ISOBUS/CAN messages in real-world tractor communication scenarios.

Implementation follows Test-First Development (TDD) GREEN phase.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from afs_fastapi.equipment.farm_tractors import ISOBUSMessage

# Configure logging for CAN error handling
logger = logging.getLogger(__name__)


class CANErrorType(Enum):
    """Types of CAN/ISOBUS communication errors."""

    DATA_CORRUPTION = "data_corruption"
    INVALID_PGN = "invalid_pgn"
    INVALID_ADDRESS = "invalid_address"
    CHECKSUM_MISMATCH = "checksum_mismatch"
    TIMEOUT = "timeout"
    MALFORMED_MESSAGE = "malformed_message"
    BUFFER_OVERFLOW = "buffer_overflow"
    NETWORK_CONGESTION = "network_congestion"


class ErrorRecoveryAction(Enum):
    """Recovery actions for CAN errors."""

    NONE = "none"
    DISCARD_MESSAGE = "discard_message"
    REQUEST_RETRANSMISSION = "request_retransmission"
    FALLBACK_MODE = "fallback_mode"
    ESCALATE_ERROR = "escalate_error"
    RESET_INTERFACE = "reset_interface"


@dataclass
class CANValidationResult:
    """Result of CAN frame validation."""

    is_valid: bool
    error_type: CANErrorType | None = None
    error_message: str = ""
    recovery_action: ErrorRecoveryAction = ErrorRecoveryAction.NONE
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorRecord:
    """Structured error record for agricultural compliance."""

    error_type: CANErrorType
    timestamp: datetime
    message: str
    equipment_id: str | None = None
    field_id: str | None = None
    operation_type: str | None = None
    severity: str = "MEDIUM"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CriticalErrorResult:
    """Result of critical message error handling."""

    requires_immediate_action: bool
    escalation_level: str
    recovery_action: ErrorRecoveryAction
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryPlan:
    """Recovery plan for failed messages."""

    action: ErrorRecoveryAction
    max_retry_attempts: int = 3
    backoff_strategy: str = "exponential"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorPatternAnalysis:
    """Analysis of error patterns for predictive maintenance."""

    total_errors: int
    dominant_error_type: CANErrorType
    requires_maintenance_alert: bool
    time_window_hours: float = 1.0
    equipment_id: str | None = None


class MalformedMessageException(Exception):
    """Exception raised for malformed ISOBUS messages."""

    def __init__(self, message: str) -> None:
        """Initialize malformed message exception."""
        super().__init__(f"Malformed message: {message}")


class CANFrameValidator:
    """Validates CAN frames for production agricultural operations."""

    def __init__(self) -> None:
        """Initialize CAN frame validator with ISOBUS standards."""
        # ISOBUS/ISO 11783 specifications
        self.max_can_data_length: int = 8  # Standard CAN frame limit
        self.valid_pgn_range: tuple[int, int] = (0x0000, 0xFFFF)  # 16-bit PGN range
        self.valid_address_range: tuple[int, int] = (0x00, 0xFF)  # 8-bit address range

        # Agricultural-specific PGN ranges
        self.critical_pgns: set[int] = {0xE001, 0xE002, 0xE003}  # Emergency, safety, collision
        self.telemetry_pgns: set[int] = {0xE004, 0xE005, 0xE006}  # Tractor telemetry

    def validate_frame(self, message: ISOBUSMessage) -> CANValidationResult:
        """Validate ISOBUS message frame for production use.

        Parameters
        ----------
        message : ISOBUSMessage
            Message to validate

        Returns
        -------
        CANValidationResult
            Validation result with error details
        """
        # Check data length (CAN frame limit)
        if len(message.data) > self.max_can_data_length:
            return CANValidationResult(
                is_valid=False,
                error_type=CANErrorType.DATA_CORRUPTION,
                error_message=f"Data length {len(message.data)} exceeds maximum {self.max_can_data_length}",
                recovery_action=ErrorRecoveryAction.DISCARD_MESSAGE,
                metadata={"data_length": len(message.data)},
            )

        # Check PGN validity
        if not (self.valid_pgn_range[0] <= message.pgn <= self.valid_pgn_range[1]):
            return CANValidationResult(
                is_valid=False,
                error_type=CANErrorType.INVALID_PGN,
                error_message=f"PGN {message.pgn:04X} outside valid range",
                recovery_action=ErrorRecoveryAction.DISCARD_MESSAGE,
                metadata={"pgn": message.pgn},
            )

        # Check source address validity
        if not (
            self.valid_address_range[0] <= message.source_address <= self.valid_address_range[1]
        ):
            return CANValidationResult(
                is_valid=False,
                error_type=CANErrorType.INVALID_ADDRESS,
                error_message=f"Source address {message.source_address} outside valid range",
                recovery_action=ErrorRecoveryAction.DISCARD_MESSAGE,
                metadata={"source_address": message.source_address},
            )

        # Check destination address validity
        if not (
            self.valid_address_range[0]
            <= message.destination_address
            <= self.valid_address_range[1]
        ):
            return CANValidationResult(
                is_valid=False,
                error_type=CANErrorType.INVALID_ADDRESS,
                error_message=f"Destination address {message.destination_address} outside valid range",
                recovery_action=ErrorRecoveryAction.DISCARD_MESSAGE,
                metadata={"destination_address": message.destination_address},
            )

        # All checks passed
        return CANValidationResult(
            is_valid=True,
            error_type=None,
            error_message="",
            recovery_action=ErrorRecoveryAction.NONE,
        )


class CANErrorHandler:
    """Comprehensive CAN error handling for agricultural operations."""

    def __init__(
        self,
        max_error_count: int = 100,
        error_window_seconds: int = 300,
        enable_recovery: bool = True,
        critical_pgns: list[int] | None = None,
    ) -> None:
        """Initialize CAN error handler.

        Parameters
        ----------
        max_error_count : int, default 100
            Maximum errors allowed in time window
        error_window_seconds : int, default 300
            Time window for error rate limiting (seconds)
        enable_recovery : bool, default True
            Whether to attempt error recovery
        critical_pgns : list[int], optional
            PGNs requiring special handling
        """
        self.max_error_count = max_error_count
        self.error_window_seconds = error_window_seconds
        self.enable_recovery = enable_recovery
        self.critical_pgns = set(critical_pgns or [0xE001, 0xE002])

        # Error tracking
        self.total_errors_handled: int = 0
        self.error_timestamps: list[float] = []
        self.is_fallback_mode: bool = False
        self.fallback_operations: list[str] = []

        # Initialize validator
        self.validator = CANFrameValidator()

    def handle_error(
        self,
        error_type: CANErrorType,
        message: str,
        source_address: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Handle CAN error with rate limiting.

        Parameters
        ----------
        error_type : CANErrorType
            Type of error encountered
        message : str
            Error description
        source_address : int, optional
            Source address of problematic message
        metadata : dict, optional
            Additional error context
        """
        current_time: float = time.time()
        self.error_timestamps.append(current_time)
        self.total_errors_handled += 1

        # Clean old timestamps outside window
        cutoff_time: float = current_time - self.error_window_seconds
        self.error_timestamps = [ts for ts in self.error_timestamps if ts > cutoff_time]

        logger.warning(
            f"CAN Error [{error_type.value}]: {message} "
            f"(Total: {self.total_errors_handled}, Recent: {len(self.error_timestamps)})"
        )

    def is_rate_limited(self) -> bool:
        """Check if error rate limiting is active.

        Returns
        -------
        bool
            True if rate limited
        """
        return len(self.error_timestamps) >= self.max_error_count

    def process_malformed_message(self, malformed_data: Any) -> None:
        """Process malformed message data.

        Parameters
        ----------
        malformed_data : Any
            Malformed message data

        Raises
        ------
        MalformedMessageException
            When message cannot be processed
        """
        self.handle_error(
            error_type=CANErrorType.MALFORMED_MESSAGE,
            message="Received malformed message data",
            metadata={"data_type": type(malformed_data).__name__},
        )

        raise MalformedMessageException("Unable to parse malformed message data")

    def handle_critical_message_error(self, message: ISOBUSMessage) -> CriticalErrorResult:
        """Handle errors in safety-critical messages.

        Parameters
        ----------
        message : ISOBUSMessage
            Critical message with errors

        Returns
        -------
        CriticalErrorResult
            Critical error handling result
        """
        if message.pgn in self.critical_pgns:
            # Safety-critical message requires immediate action
            return CriticalErrorResult(
                requires_immediate_action=True,
                escalation_level="CRITICAL",
                recovery_action=ErrorRecoveryAction.REQUEST_RETRANSMISSION,
                metadata={"pgn": message.pgn, "source": message.source_address},
            )

        return CriticalErrorResult(
            requires_immediate_action=False,
            escalation_level="STANDARD",
            recovery_action=ErrorRecoveryAction.DISCARD_MESSAGE,
        )

    def create_recovery_plan(
        self,
        error_type: CANErrorType,
        original_message: ISOBUSMessage,
    ) -> RecoveryPlan:
        """Create recovery plan for failed message.

        Parameters
        ----------
        error_type : CANErrorType
            Type of error encountered
        original_message : ISOBUSMessage
            Original failed message

        Returns
        -------
        RecoveryPlan
            Recovery plan for the error
        """
        if error_type == CANErrorType.CHECKSUM_MISMATCH:
            return RecoveryPlan(
                action=ErrorRecoveryAction.REQUEST_RETRANSMISSION,
                max_retry_attempts=3,
                backoff_strategy="exponential",
                metadata={"original_pgn": original_message.pgn},
            )

        return RecoveryPlan(
            action=ErrorRecoveryAction.DISCARD_MESSAGE,
            max_retry_attempts=0,
            backoff_strategy="none",
        )

    def enter_fallback_mode(
        self,
        reason: str,
        reduced_functionality: list[str],
        estimated_duration_minutes: int,
    ) -> None:
        """Enter fallback communication mode.

        Parameters
        ----------
        reason : str
            Reason for entering fallback mode
        reduced_functionality : list[str]
            List of allowed operations
        estimated_duration_minutes : int
            Estimated duration of fallback mode
        """
        self.is_fallback_mode = True
        self.fallback_operations = reduced_functionality.copy()

        logger.warning(
            f"Entering fallback mode: {reason} "
            f"(Duration: {estimated_duration_minutes}min, "
            f"Operations: {reduced_functionality})"
        )

    def is_in_fallback_mode(self) -> bool:
        """Check if currently in fallback mode.

        Returns
        -------
        bool
            True if in fallback mode
        """
        return self.is_fallback_mode

    def get_allowed_operations(self) -> list[str]:
        """Get list of allowed operations in current mode.

        Returns
        -------
        list[str]
            List of allowed operations
        """
        return self.fallback_operations.copy()


class ISOBUSErrorLogger:
    """Error logging for agricultural compliance and diagnostics."""

    def __init__(
        self,
        log_level: str = "INFO",
        include_telemetry: bool = True,
        archive_errors: bool = True,
        compliance_reporting: bool = True,
    ) -> None:
        """Initialize ISOBUS error logger.

        Parameters
        ----------
        log_level : str, default "INFO"
            Logging level
        include_telemetry : bool, default True
            Include telemetry in logs
        archive_errors : bool, default True
            Archive errors for analysis
        compliance_reporting : bool, default True
            Generate compliance reports
        """
        self.log_level = log_level
        self.include_telemetry = include_telemetry
        self.archive_errors = archive_errors
        self.compliance_reporting = compliance_reporting

        # Error storage for analysis
        self.error_records: list[ErrorRecord] = []

    def log_can_error(
        self,
        error_type: CANErrorType,
        message: str,
        equipment_id: str | None = None,
        field_id: str | None = None,
        operation_type: str | None = None,
        severity: str = "MEDIUM",
        metadata: dict[str, Any] | None = None,
    ) -> ErrorRecord:
        """Log CAN error with agricultural context.

        Parameters
        ----------
        error_type : CANErrorType
            Type of error
        message : str
            Error message
        equipment_id : str, optional
            Equipment identifier
        field_id : str, optional
            Field identifier
        operation_type : str, optional
            Type of operation
        severity : str, default "MEDIUM"
            Error severity level
        metadata : dict, optional
            Additional error metadata

        Returns
        -------
        ErrorRecord
            Created error record
        """
        error_record: ErrorRecord = ErrorRecord(
            error_type=error_type,
            timestamp=datetime.now(),
            message=message,
            equipment_id=equipment_id,
            field_id=field_id,
            operation_type=operation_type,
            severity=severity,
            metadata=metadata or {},
        )

        if self.archive_errors:
            self.error_records.append(error_record)

        logger.log(
            getattr(logging, self.log_level),
            f"CAN Error [{error_type.value}] {severity}: {message} "
            f"(Equipment: {equipment_id}, Field: {field_id})",
        )

        return error_record

    def analyze_error_patterns(
        self,
        time_window_hours: float = 1.0,
        equipment_id: str | None = None,
    ) -> ErrorPatternAnalysis:
        """Analyze error patterns for predictive maintenance.

        Parameters
        ----------
        time_window_hours : float, default 1.0
            Time window for analysis (hours)
        equipment_id : str, optional
            Specific equipment to analyze

        Returns
        -------
        ErrorPatternAnalysis
            Error pattern analysis result
        """
        cutoff_time: datetime = datetime.now() - timedelta(hours=time_window_hours)

        # Filter relevant error records
        relevant_errors: list[ErrorRecord] = [
            record
            for record in self.error_records
            if record.timestamp > cutoff_time
            and (equipment_id is None or record.equipment_id == equipment_id)
        ]

        if not relevant_errors:
            return ErrorPatternAnalysis(
                total_errors=0,
                dominant_error_type=CANErrorType.DATA_CORRUPTION,  # Default
                requires_maintenance_alert=False,
                time_window_hours=time_window_hours,
                equipment_id=equipment_id,
            )

        # Find dominant error type
        error_counts: dict[CANErrorType, int] = {}
        for record in relevant_errors:
            error_counts[record.error_type] = error_counts.get(record.error_type, 0) + 1

        dominant_error: CANErrorType = max(error_counts.keys(), key=lambda k: error_counts[k])

        # Determine if maintenance alert needed (>5 errors or critical error types)
        requires_maintenance: bool = len(relevant_errors) > 5 or any(
            record.severity == "CRITICAL" for record in relevant_errors
        )

        return ErrorPatternAnalysis(
            total_errors=len(relevant_errors),
            dominant_error_type=dominant_error,
            requires_maintenance_alert=requires_maintenance,
            time_window_hours=time_window_hours,
            equipment_id=equipment_id,
        )
