"""
Test CAN message error handling framework for production agricultural operations.

This module tests comprehensive error handling for corrupted, malformed, and
invalid ISOBUS/CAN messages in real-world tractor communication scenarios.

Implementation follows Test-First Development (TDD) RED phase.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from afs_fastapi.equipment.can_error_handling import (
    CANErrorHandler,
    CANErrorType,
    CANFrameValidator,
    ErrorRecoveryAction,
    ISOBUSErrorLogger,
    MalformedMessageException,
)
from afs_fastapi.equipment.farm_tractors import ISOBUSMessage


class TestCANFrameValidation:
    """Test CAN frame validation for production agricultural operations."""

    def test_valid_can_frame_validation(self) -> None:
        """Test validation of properly formatted CAN frames."""
        # RED: Test valid ISOBUS message passes validation

        validator = CANFrameValidator()

        # Create valid ISOBUS message
        valid_message = ISOBUSMessage(
            pgn=0xE004,  # Valid tractor telemetry PGN
            source_address=0x23,
            destination_address=0xFF,
            data=b"\x12\x34\x56\x78\x9A\xBC\xDE\xF0",  # 8 bytes of valid data
            timestamp=datetime.now(),
        )

        # Should pass validation without errors
        validation_result = validator.validate_frame(valid_message)

        assert validation_result.is_valid is True
        assert validation_result.error_type is None
        assert validation_result.error_message == ""
        assert validation_result.recovery_action == ErrorRecoveryAction.NONE

    def test_corrupted_data_detection(self) -> None:
        """Test detection of corrupted CAN message data."""
        # RED: Test corrupted data payload detection

        validator = CANFrameValidator()

        # Create message with corrupted data (too long for CAN frame)
        corrupted_message = ISOBUSMessage(
            pgn=0xE004,
            source_address=0x23,
            destination_address=0xFF,
            data=b"\x12" * 20,  # 20 bytes - exceeds CAN 8-byte limit
            timestamp=datetime.now(),
        )

        validation_result = validator.validate_frame(corrupted_message)

        assert validation_result.is_valid is False
        assert validation_result.error_type == CANErrorType.DATA_CORRUPTION
        assert "exceeds maximum" in validation_result.error_message.lower()
        assert validation_result.recovery_action == ErrorRecoveryAction.DISCARD_MESSAGE

    def test_invalid_pgn_detection(self) -> None:
        """Test detection of invalid Parameter Group Numbers."""
        # RED: Test invalid PGN handling

        validator = CANFrameValidator()

        # Create message with invalid PGN (outside valid range)
        invalid_pgn_message = ISOBUSMessage(
            pgn=0xFFFFFF,  # Invalid PGN - too large
            source_address=0x23,
            destination_address=0xFF,
            data=b"\x12\x34\x56\x78",
            timestamp=datetime.now(),
        )

        validation_result = validator.validate_frame(invalid_pgn_message)

        assert validation_result.is_valid is False
        assert validation_result.error_type == CANErrorType.INVALID_PGN
        assert validation_result.recovery_action == ErrorRecoveryAction.DISCARD_MESSAGE

    def test_invalid_address_detection(self) -> None:
        """Test detection of invalid ISOBUS addresses."""
        # RED: Test invalid source/destination address handling

        validator = CANFrameValidator()

        # Create message with invalid source address
        invalid_address_message = ISOBUSMessage(
            pgn=0xE004,
            source_address=0x300,  # Invalid - exceeds 8-bit limit
            destination_address=0xFF,
            data=b"\x12\x34\x56\x78",
            timestamp=datetime.now(),
        )

        validation_result = validator.validate_frame(invalid_address_message)

        assert validation_result.is_valid is False
        assert validation_result.error_type == CANErrorType.INVALID_ADDRESS
        assert validation_result.recovery_action == ErrorRecoveryAction.DISCARD_MESSAGE


class TestCANErrorHandling:
    """Test comprehensive CAN error handling for agricultural operations."""

    def test_error_handler_initialization(self) -> None:
        """Test error handler initialization with agricultural configuration."""
        # RED: Test error handler setup for farm operations

        error_handler = CANErrorHandler(
            max_error_count=100,
            error_window_seconds=300,  # 5 minutes
            enable_recovery=True,
            critical_pgns=[0xE001, 0xE002],  # Emergency and safety PGNs
        )

        assert error_handler.max_error_count == 100
        assert error_handler.error_window_seconds == 300
        assert error_handler.enable_recovery is True
        assert 0xE001 in error_handler.critical_pgns
        assert error_handler.total_errors_handled == 0

    def test_malformed_message_handling(self) -> None:
        """Test handling of malformed ISOBUS messages."""
        # RED: Test malformed message recovery

        error_handler = CANErrorHandler()

        # Simulate malformed message data
        malformed_data = {
            "invalid_field": "bad_data",
            "missing_pgn": True,
        }

        # Should handle malformed message gracefully
        with pytest.raises(MalformedMessageException) as exc_info:
            error_handler.process_malformed_message(malformed_data)

        assert "malformed message" in str(exc_info.value).lower()
        assert error_handler.total_errors_handled == 1

    def test_error_rate_limiting(self) -> None:
        """Test error rate limiting for production stability."""
        # RED: Test error burst protection

        error_handler = CANErrorHandler(
            max_error_count=5,
            error_window_seconds=10,
        )

        # Generate burst of errors
        for i in range(10):
            error_handler.handle_error(
                error_type=CANErrorType.DATA_CORRUPTION,
                message=f"Test error {i}",
                source_address=0x23,
            )

        # Should trigger rate limiting
        assert error_handler.is_rate_limited() is True
        assert error_handler.total_errors_handled >= 5

    def test_critical_message_error_handling(self) -> None:
        """Test special handling for safety-critical message errors."""
        # RED: Test emergency message error escalation

        error_handler = CANErrorHandler(
            critical_pgns=[0xE001],  # Emergency stop PGN
        )

        # Create corrupted emergency message
        emergency_message = ISOBUSMessage(
            pgn=0xE001,  # Emergency stop
            source_address=0x23,
            destination_address=0xFF,
            data=b"",  # Empty data - corrupted
            timestamp=datetime.now(),
        )

        result = error_handler.handle_critical_message_error(emergency_message)

        assert result.requires_immediate_action is True
        assert result.escalation_level == "CRITICAL"
        assert result.recovery_action == ErrorRecoveryAction.REQUEST_RETRANSMISSION


class TestISOBUSErrorLogging:
    """Test error logging for agricultural compliance and diagnostics."""

    def test_error_logger_initialization(self) -> None:
        """Test agricultural-specific error logger setup."""
        # RED: Test error logging with farm operation context

        logger = ISOBUSErrorLogger(
            log_level="INFO",
            include_telemetry=True,
            archive_errors=True,
            compliance_reporting=True,
        )

        assert logger.log_level == "INFO"
        assert logger.include_telemetry is True
        assert logger.archive_errors is True
        assert logger.compliance_reporting is True

    def test_structured_error_logging(self) -> None:
        """Test structured logging for error analysis."""
        # RED: Test comprehensive error record creation

        logger = ISOBUSErrorLogger()

        # Log CAN error with agricultural context
        error_record = logger.log_can_error(
            error_type=CANErrorType.DATA_CORRUPTION,
            message="Corrupted tractor telemetry data",
            equipment_id="TRACTOR_FIELD_01",
            field_id="NORTH_SECTION_A",
            operation_type="cultivation",
            severity="HIGH",
            metadata={
                "pgn": 0xE004,
                "source_address": 0x23,
                "data_length": 12,
                "expected_length": 8,
            },
        )

        assert error_record.error_type == CANErrorType.DATA_CORRUPTION
        assert error_record.equipment_id == "TRACTOR_FIELD_01"
        assert error_record.field_id == "NORTH_SECTION_A"
        assert error_record.severity == "HIGH"
        assert error_record.metadata["pgn"] == 0xE004

    def test_error_pattern_analysis(self) -> None:
        """Test error pattern detection for predictive maintenance."""
        # RED: Test error trend analysis for farm equipment

        logger = ISOBUSErrorLogger()

        # Generate pattern of errors from same equipment
        for i in range(10):
            logger.log_can_error(
                error_type=CANErrorType.TIMEOUT,
                message=f"Communication timeout {i}",
                equipment_id="TRACTOR_FIELD_01",
                field_id="SOUTH_SECTION_B",
            )

        # Analyze error patterns
        analysis = logger.analyze_error_patterns(
            time_window_hours=1,
            equipment_id="TRACTOR_FIELD_01",
        )

        assert analysis.total_errors == 10
        assert analysis.dominant_error_type == CANErrorType.TIMEOUT
        assert analysis.requires_maintenance_alert is True


class TestErrorRecoveryActions:
    """Test automated error recovery for agricultural operations."""

    def test_retransmission_recovery(self) -> None:
        """Test message retransmission for recoverable errors."""
        # RED: Test automatic retransmission logic

        error_handler = CANErrorHandler()

        # Create recoverable error scenario
        failed_message = ISOBUSMessage(
            pgn=0xE004,
            source_address=0x23,
            destination_address=0xFF,
            data=b"\x12\x34\x56\x78",
            timestamp=datetime.now(),
        )

        recovery_plan = error_handler.create_recovery_plan(
            error_type=CANErrorType.CHECKSUM_MISMATCH,
            original_message=failed_message,
        )

        assert recovery_plan.action == ErrorRecoveryAction.REQUEST_RETRANSMISSION
        assert recovery_plan.max_retry_attempts == 3
        assert recovery_plan.backoff_strategy == "exponential"

    def test_fallback_communication_mode(self) -> None:
        """Test fallback to reduced functionality during errors."""
        # RED: Test graceful degradation for farm operations

        error_handler = CANErrorHandler()

        # Simulate sustained communication errors
        error_handler.enter_fallback_mode(
            reason="Sustained CAN bus errors",
            reduced_functionality=["telemetry_only", "emergency_only"],
            estimated_duration_minutes=15,
        )

        assert error_handler.is_in_fallback_mode() is True
        assert "telemetry_only" in error_handler.get_allowed_operations()
        assert "emergency_only" in error_handler.get_allowed_operations()
