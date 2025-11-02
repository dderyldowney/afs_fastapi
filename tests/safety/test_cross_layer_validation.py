"""
Test suite for Cross-Layer Safety Validation between J1939 and ISO 25119.

Tests the integration and validation of safety-critical messages across
protocol boundaries for agricultural equipment safety compliance.
"""

from __future__ import annotations

import can
import pytest

from afs_fastapi.safety.cross_layer_validation import (
    CrossLayerSafetyValidator,
    J1939SafetyProtocolMapper,
    SafetyCriticalityLevel,
)
from afs_fastapi.safety.iso25119 import (
    DynamicSafetyConditions,
    DynamicSafetyMonitor,
    SafetyAuditLogger,
    SafetyHeartbeatMonitor,
    SafetyPerformanceMonitor,
)


class TestJ1939SafetyProtocolMapper:
    """Test J1939 to ISO 25119 safety protocol mapping."""

    @pytest.fixture
    def protocol_mapper(self) -> J1939SafetyProtocolMapper:
        """Create protocol mapper."""
        return J1939SafetyProtocolMapper()

    def test_mapper_initialization(self, protocol_mapper: J1939SafetyProtocolMapper) -> None:
        """Test protocol mapper initialization."""
        assert len(protocol_mapper.safety_mappings) > 0
        assert 0xFECA in protocol_mapper.safety_mappings  # DM1
        assert 0xEF00 in protocol_mapper.safety_mappings  # Emergency Stop

    def test_emergency_stop_mapping(self, protocol_mapper: J1939SafetyProtocolMapper) -> None:
        """Test emergency stop message mapping."""
        mapping = protocol_mapper.get_safety_mapping(0xEF00)

        assert mapping is not None
        assert mapping.pgn_name == "Emergency Stop Command"
        assert mapping.criticality_level == SafetyCriticalityLevel.SAFETY_CRITICAL
        assert mapping.required_sil == "SIL 3"
        assert mapping.max_response_time_ms == 50.0
        assert "emergency_stop" in mapping.safety_functions

    def test_diagnostic_message_mapping(self, protocol_mapper: J1939SafetyProtocolMapper) -> None:
        """Test diagnostic message (DM1) mapping."""
        mapping = protocol_mapper.get_safety_mapping(0xFECA)

        assert mapping is not None
        assert mapping.pgn_name == "Diagnostic Message 1"
        assert mapping.criticality_level == SafetyCriticalityLevel.HIGH_CRITICAL
        assert mapping.required_sil == "SIL 2"
        assert "diagnostic_monitoring" in mapping.safety_functions

    def test_vehicle_position_mapping(self, protocol_mapper: J1939SafetyProtocolMapper) -> None:
        """Test vehicle position message mapping."""
        mapping = protocol_mapper.get_safety_mapping(0xFEF3)

        assert mapping is not None
        assert mapping.pgn_name == "Vehicle Position"
        assert mapping.criticality_level == SafetyCriticalityLevel.HIGH_CRITICAL
        assert mapping.required_sil == "SIL 2"
        assert "position_monitoring" in mapping.safety_functions

    def test_safety_critical_detection(self, protocol_mapper: J1939SafetyProtocolMapper) -> None:
        """Test safety critical message detection."""
        # Emergency stop should be safety critical
        assert protocol_mapper.is_safety_critical(0xEF00) is True

        # Vehicle position should be safety critical
        assert protocol_mapper.is_safety_critical(0xFEF3) is True

        # Vehicle speed should not be safety critical (medium critical)
        assert protocol_mapper.is_safety_critical(0xFEF1) is False

        # Unknown PGN should not be safety critical
        assert protocol_mapper.is_safety_critical(0xDEAD) is False

    def test_required_sil_retrieval(self, protocol_mapper: J1939SafetyProtocolMapper) -> None:
        """Test required SIL level retrieval."""
        # Emergency stop requires SIL 3
        assert protocol_mapper.get_required_sil(0xEF00) == "SIL 3"

        # Engine controller requires SIL 1
        assert protocol_mapper.get_required_sil(0xF004) == "SIL 1"

        # Unknown PGN returns None
        assert protocol_mapper.get_required_sil(0xDEAD) is None


class TestCrossLayerSafetyValidator:
    """Test cross-layer safety validation functionality."""

    @pytest.fixture
    def validator_components(self):
        """Create integrated safety components for testing."""
        dynamic_monitor = DynamicSafetyMonitor()
        heartbeat_monitor = SafetyHeartbeatMonitor(timeout_ms=500)
        performance_monitor = SafetyPerformanceMonitor()
        audit_logger = SafetyAuditLogger(max_events=1000)

        validator = CrossLayerSafetyValidator(
            dynamic_monitor, heartbeat_monitor, performance_monitor, audit_logger
        )

        return {
            "validator": validator,
            "dynamic_monitor": dynamic_monitor,
            "heartbeat_monitor": heartbeat_monitor,
            "performance_monitor": performance_monitor,
            "audit_logger": audit_logger,
        }

    def test_validator_initialization(self, validator_components) -> None:
        """Test cross-layer validator initialization."""
        validator = validator_components["validator"]

        assert validator.protocol_mapper is not None
        assert validator.dynamic_monitor is not None

        # Verify SIL levels are properly initialized for all safety systems
        assert len(validator.current_sil_levels) == 5  # 5 safety systems in protocol mappings
        assert validator.current_sil_levels["Emergency Stop Command"] == "SIL 3"
        assert validator.current_sil_levels["Vehicle Position"] == "SIL 2"
        assert validator.current_sil_levels["Diagnostic Message 1"] == "SIL 2"
        assert validator.current_sil_levels["Electronic Engine Controller 1"] == "SIL 1"
        assert validator.current_sil_levels["Wheel-Based Vehicle Speed"] == "SIL 1"

        assert validator.emergency_escalation_active is False

        # Check that safety functions are registered
        heartbeat_status = validator.heartbeat_monitor.get_health_status()
        assert "cross_layer_validation" in heartbeat_status

    def test_emergency_stop_validation_success(self, validator_components) -> None:
        """Test successful validation of emergency stop message."""
        validator = validator_components["validator"]

        # Create valid emergency stop message from authorized controller
        emergency_message = can.Message(
            arbitration_id=0x18EF0000,  # Emergency stop from address 0x00 (authorized)
            data=b"\x01\x00\x00\x00\x00\x00\x00\x00",
            is_extended_id=True,
        )

        result = validator.validate_safety_critical_message(emergency_message)

        assert result.safety_critical is True
        assert result.criticality_level == SafetyCriticalityLevel.SAFETY_CRITICAL
        assert result.required_sil_level == "SIL 3"
        assert result.validation_passed is True  # Should pass with proper format

    def test_emergency_stop_validation_failure(self, validator_components) -> None:
        """Test failed validation of emergency stop message."""
        validator = validator_components["validator"]

        # Create invalid emergency stop message from unauthorized controller
        invalid_emergency = can.Message(
            arbitration_id=0x18EF0099,  # Emergency stop from unauthorized address 0x99
            data=b"\xFF",  # Invalid/insufficient data
            is_extended_id=True,
        )

        result = validator.validate_safety_critical_message(invalid_emergency)

        assert result.safety_critical is True
        assert result.criticality_level == SafetyCriticalityLevel.SAFETY_CRITICAL
        assert result.validation_passed is False
        assert len(result.validation_errors) > 0

    def test_vehicle_position_validation(self, validator_components) -> None:
        """Test validation of vehicle position message."""
        validator = validator_components["validator"]

        # Create vehicle position message
        position_message = can.Message(
            arbitration_id=0x18FEF300,  # Vehicle Position from address 0x00
            data=b"\x12\x34\x56\x78\x9A\xBC\xDE\xF0",  # Valid 8-byte GPS data
            is_extended_id=True,
        )

        result = validator.validate_safety_critical_message(position_message)

        assert result.safety_critical is True
        assert result.criticality_level == SafetyCriticalityLevel.HIGH_CRITICAL
        assert result.required_sil_level == "SIL 2"
        assert result.validation_passed is True

    def test_non_critical_message_handling(self, validator_components) -> None:
        """Test handling of non-critical messages."""
        validator = validator_components["validator"]

        # Create unknown/non-critical message
        unknown_message = can.Message(
            arbitration_id=0x18DEAD00,  # Unknown PGN
            data=b"\x01\x02\x03\x04",
            is_extended_id=True,
        )

        result = validator.validate_safety_critical_message(unknown_message)

        assert result.safety_critical is False
        assert result.criticality_level == SafetyCriticalityLevel.NON_CRITICAL
        assert result.validation_passed is True
        assert result.iso25119_compliant is True

    def test_sil_level_inadequacy_detection(self, validator_components) -> None:
        """Test detection of inadequate SIL levels."""
        validator = validator_components["validator"]

        # Set current SIL level lower than required
        validator.current_sil_levels["Vehicle Position"] = "SIL 1"  # Required is SIL 2

        position_message = can.Message(
            arbitration_id=0x18FEF300,
            data=b"\x12\x34\x56\x78\x9A\xBC\xDE\xF0",
            is_extended_id=True,
        )

        result = validator.validate_safety_critical_message(position_message)

        assert result.validation_passed is False
        assert any("inadequate" in error for error in result.validation_errors)
        assert "escalate_sil_level" in result.mandatory_actions

    def test_performance_monitoring_integration(self, validator_components) -> None:
        """Test integration with performance monitoring."""
        validator = validator_components["validator"]
        performance_monitor = validator_components["performance_monitor"]

        # Validate a message (which should record performance metrics)
        message = can.Message(
            arbitration_id=0x18F00400,  # Engine Controller
            data=b"\x01\x02\x03\x04\x05\x06\x07\x08",
            is_extended_id=True,
        )

        validator.validate_safety_critical_message(message)

        # Check that performance was recorded
        metrics = performance_monitor.get_performance_report()
        assert "cross_layer_validation" in metrics
        assert metrics["cross_layer_validation"].execution_count > 0

    def test_audit_logging_integration(self, validator_components) -> None:
        """Test integration with audit logging."""
        validator = validator_components["validator"]
        audit_logger = validator_components["audit_logger"]

        # Trigger a validation failure
        invalid_message = can.Message(
            arbitration_id=0x18EF0099,  # Invalid emergency stop
            data=b"\xFF",
            is_extended_id=True,
        )

        validator.validate_safety_critical_message(invalid_message)

        # Check that event was logged
        events = audit_logger.audit_events
        assert len(events) > 0

        safety_events = [e for e in events if e.event_type == "safety_validation"]
        assert len(safety_events) > 0

    def test_dynamic_conditions_effect_on_validation(self, validator_components) -> None:
        """Test effect of dynamic conditions on validation."""
        validator = validator_components["validator"]
        dynamic_monitor = validator_components["dynamic_monitor"]

        # Set adverse conditions
        adverse_conditions = DynamicSafetyConditions(
            weather_conditions="rain",
            visibility_meters=30.0,
            communication_quality="poor",
        )
        dynamic_monitor.update_field_conditions(adverse_conditions)

        # Validate message under adverse conditions
        message = can.Message(
            arbitration_id=0x18F00400,  # Engine Controller
            data=b"\x01\x02\x03\x04\x05\x06\x07\x08",
            is_extended_id=True,
        )

        result = validator.validate_safety_critical_message(message)

        # The validation should still work, but conditions affect dynamic SIL evaluation
        assert result is not None
        assert hasattr(result, "validation_passed")

    def test_safety_status_reporting(self, validator_components) -> None:
        """Test comprehensive safety status reporting."""
        validator = validator_components["validator"]

        # Add some test data
        validator.current_sil_levels["test_system"] = "SIL 2"

        status = validator.get_safety_status()

        required_keys = [
            "current_sil_levels",
            "emergency_escalation_active",
            "recent_violations",
            "heartbeat_status",
            "performance_compliant",
        ]

        for key in required_keys:
            assert key in status

        assert status["current_sil_levels"]["test_system"] == "SIL 2"
        assert isinstance(status["emergency_escalation_active"], bool)
        assert isinstance(status["recent_violations"], int)


class TestValidationRules:
    """Test specific validation rules for different message types."""

    @pytest.fixture
    def validator(self):
        """Create minimal validator for rule testing."""
        dynamic_monitor = DynamicSafetyMonitor()
        heartbeat_monitor = SafetyHeartbeatMonitor()
        performance_monitor = SafetyPerformanceMonitor()
        audit_logger = SafetyAuditLogger()

        return CrossLayerSafetyValidator(
            dynamic_monitor, heartbeat_monitor, performance_monitor, audit_logger
        )

    def test_dtc_format_validation(self, validator: CrossLayerSafetyValidator) -> None:
        """Test DTC message format validation."""
        # Valid DM1 message with sufficient length
        valid_dm1 = can.Message(
            arbitration_id=0x18FECA00,
            data=b"\x40\xFF\x12\x34\x56\x78\x01\x02",  # Valid DTC format
            is_extended_id=True,
        )

        result = validator.validate_safety_critical_message(valid_dm1)
        assert result.validation_passed is True

        # Invalid DM1 message with insufficient length
        invalid_dm1 = can.Message(
            arbitration_id=0x18FECA00,
            data=b"\x40",  # Too short
            is_extended_id=True,
        )

        result = validator.validate_safety_critical_message(invalid_dm1)
        assert result.validation_passed is False

    def test_gps_accuracy_validation(self, validator: CrossLayerSafetyValidator) -> None:
        """Test GPS accuracy validation."""
        # Valid GPS message with sufficient data length
        valid_gps = can.Message(
            arbitration_id=0x18FEF300,
            data=b"\x12\x34\x56\x78\x9A\xBC\xDE\xF0",  # 8 bytes - valid
            is_extended_id=True,
        )

        result = validator.validate_safety_critical_message(valid_gps)
        assert result.validation_passed is True

        # Invalid GPS message with insufficient data
        invalid_gps = can.Message(
            arbitration_id=0x18FEF300,
            data=b"\x12\x34\x56",  # Only 3 bytes - invalid
            is_extended_id=True,
        )

        result = validator.validate_safety_critical_message(invalid_gps)
        assert result.validation_passed is False

    def test_emergency_authority_validation(self, validator: CrossLayerSafetyValidator) -> None:
        """Test emergency command authority validation."""
        # Authorized emergency controller (address 0x00)
        authorized_emergency = can.Message(
            arbitration_id=0x18EF0000,  # From address 0x00
            data=b"\x01\x00\x00\x00\x00\x00\x00\x00",
            is_extended_id=True,
        )

        result = validator.validate_safety_critical_message(authorized_emergency)
        assert result.validation_passed is True

        # Unauthorized emergency controller (address 0x99)
        unauthorized_emergency = can.Message(
            arbitration_id=0x18EF0099,  # From address 0x99 (not authorized)
            data=b"\x01\x00\x00\x00\x00\x00\x00\x00",
            is_extended_id=True,
        )

        result = validator.validate_safety_critical_message(unauthorized_emergency)
        assert result.validation_passed is False


class TestIntegratedSafetyWorkflow:
    """Test integrated safety validation workflows."""

    @pytest.mark.asyncio
    async def test_complete_safety_validation_workflow(self) -> None:
        """Test complete safety validation workflow with all components."""
        # Initialize all safety components
        dynamic_monitor = DynamicSafetyMonitor()
        heartbeat_monitor = SafetyHeartbeatMonitor(timeout_ms=500)
        performance_monitor = SafetyPerformanceMonitor()
        audit_logger = SafetyAuditLogger()

        validator = CrossLayerSafetyValidator(
            dynamic_monitor, heartbeat_monitor, performance_monitor, audit_logger
        )

        # Step 1: Set challenging field conditions
        challenging_conditions = DynamicSafetyConditions(
            weather_conditions="fog",
            visibility_meters=25.0,
            bystander_proximity_meters=20.0,
            communication_quality="poor",
        )
        dynamic_monitor.update_field_conditions(challenging_conditions)

        # Step 2: Validate emergency stop message
        emergency_message = can.Message(
            arbitration_id=0x18EF0000,
            data=b"\x01\x00\x00\x00\x00\x00\x00\x00",
            is_extended_id=True,
        )

        emergency_result = validator.validate_safety_critical_message(emergency_message)

        # Step 3: Validate vehicle position message
        position_message = can.Message(
            arbitration_id=0x18FEF300,
            data=b"\x12\x34\x56\x78\x9A\xBC\xDE\xF0",
            is_extended_id=True,
        )

        position_result = validator.validate_safety_critical_message(position_message)

        # Step 4: Check system status and reports
        safety_status = validator.get_safety_status()
        compliance_report = audit_logger.generate_compliance_report()
        performance_report = performance_monitor.get_performance_report()

        # Verify results
        assert emergency_result.safety_critical is True
        assert position_result.safety_critical is True

        assert compliance_report["total_events"] >= 2
        assert "cross_layer_validation" in performance_report
        assert performance_report["cross_layer_validation"].execution_count >= 2

        assert "current_sil_levels" in safety_status
        assert "heartbeat_status" in safety_status

    def test_cascading_safety_escalation(self) -> None:
        """Test cascading safety escalation across multiple systems."""
        # Initialize components
        dynamic_monitor = DynamicSafetyMonitor()
        audit_logger = SafetyAuditLogger()
        heartbeat_monitor = SafetyHeartbeatMonitor()
        performance_monitor = SafetyPerformanceMonitor()

        validator = CrossLayerSafetyValidator(
            dynamic_monitor, heartbeat_monitor, performance_monitor, audit_logger
        )

        # Create critical conditions that should trigger escalation
        critical_conditions = DynamicSafetyConditions(
            weather_conditions="snow",
            visibility_meters=10.0,
            bystander_proximity_meters=5.0,
            communication_quality="failed",
            gps_accuracy_meters=20.0,
        )
        dynamic_monitor.update_field_conditions(critical_conditions)

        # Evaluate dynamic SIL under critical conditions
        sil_result = dynamic_monitor.evaluate_dynamic_sil(
            "emergency_stop", "autonomous_operation", ["bystander_safety"]
        )

        # Validate a safety-critical message that should fail under these conditions
        inadequate_emergency = can.Message(
            arbitration_id=0x18EF0099,  # Unauthorized source
            data=b"\xFF",  # Invalid data
            is_extended_id=True,
        )

        validation_result = validator.validate_safety_critical_message(inadequate_emergency)

        # Verify cascading effects
        assert sil_result.adjusted_sil in ["SIL 3", "SIL 4"]  # Should be escalated
        assert len(sil_result.mandatory_actions) > 0

        assert validation_result.validation_passed is False
        assert validation_result.criticality_level == SafetyCriticalityLevel.SAFETY_CRITICAL

        # Check audit trail captured all events
        events = audit_logger.audit_events
        assert len(events) >= 1

        # Verify emergency escalation is triggered
        safety_events = [e for e in events if "emergency" in e.event_type]
        critical_events = audit_logger.get_events_by_severity("critical")

        assert len(safety_events) > 0 or len(critical_events) > 0
