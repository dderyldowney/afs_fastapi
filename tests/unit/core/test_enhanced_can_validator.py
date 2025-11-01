"""
Comprehensive tests for enhanced CAN bus communication validator with SAE J1939/ISOBUS compliance.

Tests validate enhanced message validation, error recovery, and agricultural-specific
protocols with strict adherence to agricultural safety standards.
"""

from __future__ import annotations

import struct
import time
from datetime import datetime

import can
import pytest

from afs_fastapi.core.enhanced_can_validator import (
    AgriculturalCANMessage,
    EnhancedCANCommunicationSystem,
    EnhancedCANFrameValidator,
    EnhancedCANRecoveryManager,
    J1939ComplianceLevel,
    ValidationResult,
    ValidationSeverity,
)


class TestEnhancedCANFrameValidator:
    """Test enhanced CAN frame validation for agricultural operations."""

    def test_compliance_levels(self) -> None:
        """Test different compliance level configurations."""
        # Test full compliance
        full_validator = EnhancedCANFrameValidator(J1939ComplianceLevel.FULL_COMPLIANCE)
        assert full_validator.compliance_level == J1939ComplianceLevel.FULL_COMPLIANCE
        assert full_validator.pgn_ranges[J1939ComplianceLevel.FULL_COMPLIANCE] == (0x0000, 0xFFFF)

        # Test basic compliance
        basic_validator = EnhancedCANFrameValidator(J1939ComplianceLevel.BASIC_COMPLIANCE)
        assert basic_validator.compliance_level == J1939ComplianceLevel.BASIC_COMPLIANCE
        assert basic_validator.pgn_ranges[J1939ComplianceLevel.BASIC_COMPLIANCE] == (0x0000, 0xFFFE)

    def test_extended_id_requirement(self) -> None:
        """Test requirement for extended CAN IDs in J1939 compliance."""
        validator = EnhancedCANFrameValidator(J1939ComplianceLevel.FULL_COMPLIANCE)

        # Create message without extended ID
        standard_message = can.Message(
            arbitration_id=0x123,
            data=b"\x01\x02\x03\x04",
            is_extended_id=False,
        )

        result = validator.validate_enhanced_message(standard_message)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.CRITICAL
        assert "29-bit extended identifiers" in result.error_message

    def test_safety_critical_message_validation(self) -> None:
        """Test validation of safety-critical agricultural messages."""
        validator = EnhancedCANFrameValidator(J1939ComplianceLevel.FULL_COMPLIANCE)

        # Create valid emergency stop message (0x00E00123 = PGN 0xE001 Emergency Stop)
        emergency_message = can.Message(
            arbitration_id=0x00E00123,  # Emergency Stop PGN + address
            data=b"\x00\x00\x00\x00\x00\x00\x00\x00",
            is_extended_id=True,
            timestamp=time.time(),
        )

        result = validator.validate_enhanced_message(emergency_message)
        assert result.is_valid is True
        assert result.severity == ValidationSeverity.CRITICAL
        assert result.metadata["safety_critical"] is True

    def test_invalid_pgn_handling(self) -> None:
        """Test handling of invalid Parameter Group Numbers."""
        validator = EnhancedCANFrameValidator(J1939ComplianceLevel.FULL_COMPLIANCE)

        # Create message with invalid PGN
        invalid_message = can.Message(
            arbitration_id=0x1FFFFFFF,  # Invalid PGN
            data=b"\x01\x02\x03\x04",
            is_extended_id=True,
        )

        result = validator.validate_enhanced_message(invalid_message)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.HIGH

    def test_agricultural_data_validation(self) -> None:
        """Test validation of agricultural equipment data ranges."""
        validator = EnhancedCANFrameValidator(J1939ComplianceLevel.FULL_COMPLIANCE)

        # Test engine RPM validation (0-F004)
        high_rpm_data = struct.pack("<H", 65000)  # 65000 * 0.125 = 8125 RPM (too high)
        engine_message = can.Message(
            arbitration_id=0x00F00423,  # Engine Controller PGN + address
            data=high_rpm_data + b"\x00\x00\x00\x00\x00\x00",  # 8 bytes total
            is_extended_id=True,
        )

        result = validator.validate_enhanced_message(engine_message)
        assert result.is_valid is False
        assert result.severity == ValidationSeverity.HIGH

        # Test valid engine RPM
        time.sleep(0.1)  # Add small delay to avoid rate limiting
        valid_rpm_data = struct.pack("<H", 20000)  # 20000 * 0.125 = 2500 RPM (valid)
        valid_engine_message = can.Message(
            arbitration_id=0x00F00423,
            data=valid_rpm_data + b"\x00\x00\x00\x00\x00\x00",  # 8 bytes total
            is_extended_id=True,
        )

        valid_result = validator.validate_enhanced_message(valid_engine_message)
        assert valid_result.is_valid is True

    def test_gps_position_validation(self) -> None:
        """Test validation of GPS position data for agricultural navigation."""
        validator = EnhancedCANFrameValidator(J1939ComplianceLevel.FULL_COMPLIANCE)

        # Test valid GPS coordinates
        valid_lat = int(40.7128 * 1e7)  # New York latitude
        valid_lon = int((360 - 74.0060) * 1e7)  # New York longitude (normalized to 0-360 range)
        gps_data = struct.pack("<II", valid_lat, valid_lon)
        gps_message = can.Message(
            arbitration_id=0x0CFEF323,  # Vehicle Position PGN + address
            data=gps_data,
            is_extended_id=True,
        )

        result = validator.validate_enhanced_message(gps_message)
        assert result.is_valid is True

        # Test invalid GPS coordinates (outside 0-360 range for longitude)
        time.sleep(1.1)  # Add delay to avoid rate limiting (GPS PGN has 1000ms limit)
        invalid_lat = int(200.0 * 1e7)  # Invalid latitude
        invalid_lon = int(400.0 * 1e7)  # Invalid longitude (>360)
        invalid_gps_data = struct.pack("<II", invalid_lat, invalid_lon)
        invalid_gps_message = can.Message(
            arbitration_id=0x0CFEF323,
            data=invalid_gps_data,
            is_extended_id=True,
        )

        invalid_result = validator.validate_enhanced_message(invalid_gps_message)
        assert invalid_result.is_valid is False
        assert invalid_result.severity == ValidationSeverity.HIGH

    def test_message_rate_limiting(self) -> None:
        """Test message rate limiting for agricultural operations."""
        validator = EnhancedCANFrameValidator(J1939ComplianceLevel.FULL_COMPLIANCE)

        # Create engine data message
        engine_message = can.Message(
            arbitration_id=0x00F00423,
            data=b"\x00\x40\x00\x00\x00\x00\x00\x00",  # 2000 RPM at bytes 0-1
            is_extended_id=True,
        )

        # First message should be valid
        result1 = validator.validate_enhanced_message(engine_message)
        assert result1.is_valid is True

        # Send same message immediately (should be rate limited)
        result2 = validator.validate_enhanced_message(engine_message)
        assert result2.is_valid is False
        assert result2.severity == ValidationSeverity.MEDIUM
        assert "rate exceeded" in result2.error_message


class TestEnhancedCANRecoveryManager:
    """Test enhanced error recovery manager for agricultural CAN communications."""

    def test_recovery_strategy_selection(self) -> None:
        """Test recovery strategy selection based on message type."""
        from afs_fastapi.equipment.can_error_handling import CANErrorHandler, ISOBUSErrorLogger

        error_handler = CANErrorHandler()
        error_logger = ISOBUSErrorLogger()
        recovery_manager = EnhancedCANRecoveryManager(error_handler, error_logger)

        # Test safety-critical message recovery
        safety_message = can.Message(
            arbitration_id=0x00E00123,  # Emergency Stop
            data=b"\x00\x00\x00\x00\x00\x00\x00\x00",
            is_extended_id=True,
        )

        result = recovery_manager.create_enhanced_recovery_plan(
            ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.CRITICAL,
                compliance_level=J1939ComplianceLevel.FULL_COMPLIANCE,
            ),
            safety_message,
        )

        assert result["strategy"] == "safety_critical"
        assert result["max_retries"] == 5
        assert "emergency_stop" in result["actions"]

    def test_engine_data_recovery(self) -> None:
        """Test engine data recovery strategies."""
        from afs_fastapi.equipment.can_error_handling import CANErrorHandler, ISOBUSErrorLogger

        error_handler = CANErrorHandler()
        error_logger = ISOBUSErrorLogger()
        recovery_manager = EnhancedCANRecoveryManager(error_handler, error_logger)

        # Test engine data recovery
        engine_message = can.Message(
            arbitration_id=0x00F00423,
            data=b"\x00\x40\x00\x00\x00\x00\x00\x00",
            is_extended_id=True,
        )

        result = recovery_manager.create_enhanced_recovery_plan(
            ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.HIGH,
                compliance_level=J1939ComplianceLevel.FULL_COMPLIANCE,
            ),
            engine_message,
        )

        assert result["strategy"] == "engine_data"
        assert result["max_retries"] == 3
        assert "use_cached_value" in result["actions"]

    def test_recovery_attempt_tracking(self) -> None:
        """Test recovery attempt tracking for agricultural operations."""
        from afs_fastapi.equipment.can_error_handling import CANErrorHandler, ISOBUSErrorLogger

        error_handler = CANErrorHandler()
        error_logger = ISOBUSErrorLogger()
        recovery_manager = EnhancedCANRecoveryManager(error_handler, error_logger)

        # Create recovery plan
        message = can.Message(
            arbitration_id=0x00F00423,
            data=b"\x00\x40\x00\x00\x00\x00\x00\x00",
            is_extended_id=True,
        )

        validation_result = ValidationResult(
            is_valid=False,
            severity=ValidationSeverity.MEDIUM,
            compliance_level=J1939ComplianceLevel.FULL_COMPLIANCE,
        )

        recovery_plan = recovery_manager.create_enhanced_recovery_plan(validation_result, message)

        # Execute recovery
        recovery_result = recovery_manager.execute_recovery_action(
            recovery_plan, message, validation_result
        )

        # Verify attempt tracking
        assert recovery_manager.recovery_attempts["61440_medium"] == 1

    def test_safety_considerations(self) -> None:
        """Test safety considerations for recovery operations."""
        from afs_fastapi.equipment.can_error_handling import CANErrorHandler, ISOBUSErrorLogger

        error_handler = CANErrorHandler()
        error_logger = ISOBUSErrorLogger()
        recovery_manager = EnhancedCANRecoveryManager(error_handler, error_logger)

        # Test safety message considerations
        safety_message = can.Message(
            arbitration_id=0x00E00123,
            data=b"\x00\x00\x00\x00\x00\x00\x00\x00",
            is_extended_id=True,
        )

        considerations = recovery_manager._get_safety_considerations(
            0xE001, ValidationSeverity.CRITICAL
        )
        assert "immediate_stop_required" in considerations
        assert "operator_notification" in considerations

        # Test non-safety considerations
        engine_considerations = recovery_manager._get_safety_considerations(
            0xF000, ValidationSeverity.HIGH
        )
        assert "operator_warning" in engine_considerations


class TestEnhancedCANCommunicationSystem:
    """Test complete enhanced CAN communication system."""

    def test_system_initialization(self) -> None:
        """Test system initialization with different compliance levels."""
        # Test full compliance system
        full_system = EnhancedCANCommunicationSystem(J1939ComplianceLevel.FULL_COMPLIANCE)
        assert full_system.compliance_level == J1939ComplianceLevel.FULL_COMPLIANCE
        assert full_system.validator.compliance_level == J1939ComplianceLevel.FULL_COMPLIANCE

        # Test minimal compliance system
        minimal_system = EnhancedCANCommunicationSystem(J1939ComplianceLevel.MINIMAL_COMPLIANCE)
        assert minimal_system.compliance_level == J1939ComplianceLevel.MINIMAL_COMPLIANCE

    def test_message_processing(self) -> None:
        """Test complete message processing with validation and recovery."""
        system = EnhancedCANCommunicationSystem(J1939ComplianceLevel.FULL_COMPLIANCE)

        # Create valid engine data message
        rpm_data = struct.pack("<H", 20000)  # 2500 RPM
        engine_message = can.Message(
            arbitration_id=0x00F00423,
            data=rpm_data + b"\x00\x00\x00\x00\x00",
            is_extended_id=True,
            timestamp=time.time(),
        )

        # Process message
        result = system.process_enhanced_message(engine_message)

        assert isinstance(result, AgriculturalCANMessage)
        assert result.is_valid is True
        assert len(result.validation_results) > 0
        assert result.validation_results[0].is_valid is True

    def test_invalid_message_processing(self) -> None:
        """Test processing of invalid messages with recovery attempts."""
        system = EnhancedCANCommunicationSystem(J1939ComplianceLevel.FULL_COMPLIANCE)

        # Create invalid GPS message
        invalid_lat = int(200.0 * 1e7)  # Invalid latitude
        invalid_gps_data = struct.pack("<Ii", invalid_lat, int(-74.0060 * 1e7))
        gps_message = can.Message(
            arbitration_id=0x0CFEF323,
            data=invalid_gps_data,
            is_extended_id=True,
            timestamp=time.time(),
        )

        # Process message
        result = system.process_enhanced_message(gps_message)

        assert isinstance(result, AgriculturalCANMessage)
        assert result.is_valid is False
        assert len(result.validation_results) > 0
        assert result.validation_results[0].is_valid is False

    def test_system_statistics(self) -> None:
        """Test system statistics and monitoring."""
        system = EnhancedCANCommunicationSystem(J1939ComplianceLevel.FULL_COMPLIANCE)

        # Process some messages
        for i in range(5):
            rpm_data = struct.pack("<H", 20000 + i * 1000)
            message = can.Message(
                arbitration_id=0x00F00423,
                data=rpm_data + b"\x00\x00\x00\x00\x00",
                is_extended_id=True,
                timestamp=time.time(),
            )
            system.process_enhanced_message(message)

        # Get system status
        status = system.get_system_status()

        assert "compliance_level" in status
        assert "validation_statistics" in status
        assert "recovery_statistics" in status
        assert "total_messages_processed" in status
        assert status["total_messages_processed"] == 5

    def test_validation_report(self) -> None:
        """Test validation report generation for agricultural operations."""
        system = EnhancedCANCommunicationSystem(J1939ComplianceLevel.FULL_COMPLIANCE)

        # Process some messages
        for i in range(3):
            rpm_data = struct.pack("<H", 20000 + i * 1000)
            message = can.Message(
                arbitration_id=0x00F00423,
                data=rpm_data + b"\x00\x00\x00\x00\x00",
                is_extended_id=True,
                timestamp=time.time(),
            )
            system.process_enhanced_message(message)
            time.sleep(0.06)  # Add 60ms delay to avoid rate limiting (50ms limit for engine data)

        # Generate report
        report = system.export_validation_report(time_window_hours=1)

        assert "report_period" in report
        assert "total_messages" in report
        assert "valid_messages" in report
        assert "invalid_messages" in report
        assert "validation_success_rate" in report
        assert "agricultural_summary" in report
        assert "recommendations" in report

        assert report["total_messages"] == 3
        assert report["valid_messages"] == 3
        assert report["validation_success_rate"] == 1.0

    def test_agricultural_recommendations(self) -> None:
        """Test agricultural-specific recommendations generation."""
        system = EnhancedCANCommunicationSystem(J1939ComplianceLevel.FULL_COMPLIANCE)

        # Process some messages to trigger recommendations (need >10 for upgrade recommendation)
        for i in range(15):  # Generate timeout errors to trigger upgrade recommendations
            # Create messages that will generate TIMEOUT errors
            timeout_message = can.Message(
                arbitration_id=0x00F00423,
                data=b"\x00\x00\x00\x00\x00\x00\x00\x00",  # Valid data format
                is_extended_id=True,
                timestamp=time.time(),
            )

            # Process the message and manually add timeout results
            system.process_enhanced_message(timeout_message)

            # Manually add timeout results to trigger recommendation
            from afs_fastapi.core.enhanced_can_validator import (
                CANErrorType,
                ValidationResult,
                ValidationSeverity,
            )

            timeout_result = ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.MEDIUM,
                compliance_level=J1939ComplianceLevel.FULL_COMPLIANCE,
                error_type=CANErrorType.TIMEOUT,
                error_message="Simulated timeout for testing",
                recovery_action=None,
            )

            # Add timeout results to the last processed message
            if system.processed_messages:
                system.processed_messages[-1].validation_results.append(timeout_result)

        # Generate report
        report = system.export_validation_report(time_window_hours=1)

        # Should generate equipment recommendation
        recommendations = report["recommendations"]
        assert len(recommendations) > 0
        assert any("hardware" in rec.lower() for rec in recommendations)

    def test_safety_critical_handling(self) -> None:
        """Test safety-critical message handling for agricultural operations."""
        system = EnhancedCANCommunicationSystem(J1939ComplianceLevel.FULL_COMPLIANCE)

        # Create emergency stop message
        emergency_message = can.Message(
            arbitration_id=0x00E00123,
            data=b"\x00\x00\x00\x00\x00\x00\x00\x00",
            is_extended_id=True,
            timestamp=time.time(),
        )

        # Process emergency message
        result = system.process_enhanced_message(emergency_message)

        # Should be processed but with critical severity
        assert isinstance(result, AgriculturalCANMessage)
        assert result.pgn == 0xE001
        assert result.validation_results[0].severity == ValidationSeverity.CRITICAL


class TestAgriculturalCANMessage:
    """Test agricultural CAN message structure and functionality."""

    def test_agricultural_message_creation(self) -> None:
        """Test creation of agricultural CAN messages."""
        message = can.Message(
            arbitration_id=0x00F00423,
            data=b"\x00\x40\x00\x00\x00\x00\x00\x00",
            is_extended_id=True,
            timestamp=time.time(),
        )

        ag_message = AgriculturalCANMessage(
            message=message,
            pgn=0xF004,
            source_address=0x23,
            destination_address=0xFF,
            priority=3,
            timestamp=datetime.now(),
            agricultural_function="engine_control",
            equipment_type="tractor",
            operation_context="field_work",
            is_safety_critical=False,
        )

        assert ag_message.pgn == 0xF004
        assert ag_message.source_address == 0x23
        assert ag_message.priority == 3
        assert ag_message.agricultural_function == "engine_control"
        assert ag_message.equipment_type == "tractor"

    def test_validation_results_association(self) -> None:
        """Test association of validation results with agricultural messages."""
        message = can.Message(
            arbitration_id=0x00F00423,
            data=b"\x00\x40\x00\x00\x00\x00\x00\x00",
            is_extended_id=True,
            timestamp=time.time(),
        )

        validation_result = ValidationResult(
            is_valid=True,
            severity=ValidationSeverity.INFO,
            compliance_level=J1939ComplianceLevel.FULL_COMPLIANCE,
            error_message="Valid agricultural message",
        )

        ag_message = AgriculturalCANMessage(
            message=message,
            pgn=0xF004,
            source_address=0x23,
            destination_address=0xFF,
            priority=3,
            timestamp=datetime.now(),
            validation_results=[validation_result],
        )

        assert len(ag_message.validation_results) == 1
        assert ag_message.validation_results[0].is_valid is True


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_message_data(self) -> None:
        """Test handling of empty message data."""
        system = EnhancedCANCommunicationSystem(J1939ComplianceLevel.FULL_COMPLIANCE)

        empty_message = can.Message(
            arbitration_id=0x00F00423,
            data=b"",
            is_extended_id=True,
            timestamp=time.time(),
        )

        result = system.process_enhanced_message(empty_message)
        assert isinstance(result, AgriculturalCANMessage)

    def test_corrupted_message_data(self) -> None:
        """Test handling of corrupted message data."""
        system = EnhancedCANCommunicationSystem(J1939ComplianceLevel.FULL_COMPLIANCE)

        # Create message with corrupted length
        corrupted_message = can.Message(
            arbitration_id=0x00F00423,
            data=b"\x00\x00\x40\x00",  # Only 4 bytes instead of 8
            is_extended_id=True,
            timestamp=time.time(),
        )

        result = system.process_enhanced_message(corrupted_message)
        assert isinstance(result, AgriculturalCANMessage)
        # Should fail validation due to incorrect data length

    def test_extreme_values(self) -> None:
        """Test handling of extreme values in agricultural data."""
        system = EnhancedCANCommunicationSystem(J1939ComplianceLevel.FULL_COMPLIANCE)

        # Test extreme RPM values
        max_rpm_data = struct.pack("<H", 0xFFFF)  # Maximum possible RPM
        extreme_message = can.Message(
            arbitration_id=0x00F00423,
            data=max_rpm_data + b"\x00\x00\x00\x00\x00",
            is_extended_id=True,
            timestamp=time.time(),
        )

        result = system.process_enhanced_message(extreme_message)
        assert isinstance(result, AgriculturalCANMessage)
        # Should likely fail validation due to extreme values

    def test_compliance_level_transition(self) -> None:
        """Test compliance level transitions for different equipment."""
        # Test with minimal compliance
        minimal_system = EnhancedCANCommunicationSystem(J1939ComplianceLevel.MINIMAL_COMPLIANCE)

        message = can.Message(
            arbitration_id=0x00F00423,
            data=b"\x00\x40\x00\x00\x00\x00\x00\x00",
            is_extended_id=True,
            timestamp=time.time(),
        )

        result = minimal_system.process_enhanced_message(message)
        assert isinstance(result, AgriculturalCANMessage)
        assert minimal_system.compliance_level == J1939ComplianceLevel.MINIMAL_COMPLIANCE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
