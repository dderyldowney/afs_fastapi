"""
Comprehensive Test Suite for Dynamic Safety Monitoring Features

Tests the enhanced safety framework including dynamic monitoring, heartbeat,
cross-layer validation, and diagnostic integration for agricultural equipment.

Implementation follows Test-First Development (TDD) RED phase.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock

import can
import pytest

from afs_fastapi.safety.cross_layer_validation import (
    CrossLayerSafetyValidator,
    DTCSafetyAnalyzer,
    SafetyCriticalityLevel,
)
from afs_fastapi.safety.iso25119 import (
    DynamicSafetyConditions,
    DynamicSafetyMonitor,
    SafetyAuditLogger,
    SafetyHeartbeatMonitor,
    SafetyPerformanceMonitor,
)


class TestDynamicSafetyMonitor:
    """Test dynamic safety monitoring system."""

    @pytest.fixture
    def dynamic_monitor(self) -> DynamicSafetyMonitor:
        """Create dynamic safety monitor."""
        return DynamicSafetyMonitor()

    def test_monitor_initialization(self, dynamic_monitor: DynamicSafetyMonitor) -> None:
        """Test dynamic safety monitor initialization."""
        assert dynamic_monitor.safety_classifier is not None
        assert dynamic_monitor.current_conditions.weather_conditions == "clear"
        assert dynamic_monitor.current_conditions.visibility_meters == 100.0
        assert len(dynamic_monitor.risk_escalation_rules) > 0

    def test_clear_conditions_no_escalation(self, dynamic_monitor: DynamicSafetyMonitor) -> None:
        """Test SIL evaluation under clear conditions requires no escalation."""
        # Test baseline conditions
        result = dynamic_monitor.evaluate_dynamic_sil(
            system_type="autonomous_navigation",
            operation_mode="field_operations",
            base_risk_factors=["collision_risk"],
        )

        assert result.original_sil == "SIL 2"
        assert result.adjusted_sil == "SIL 2"
        assert result.risk_escalation_applied is False
        assert result.adjustment_reason == "No risk escalation required - baseline SIL maintained"

    def test_adverse_weather_escalation(self, dynamic_monitor: DynamicSafetyMonitor) -> None:
        """Test SIL escalation under adverse weather conditions."""
        # Update conditions to include rain
        adverse_conditions = DynamicSafetyConditions(
            weather_conditions="rain",
            visibility_meters=30.0,  # Poor visibility
            bystander_proximity_meters=15.0,  # Close bystanders
        )
        dynamic_monitor.update_field_conditions(adverse_conditions)

        result = dynamic_monitor.evaluate_dynamic_sil(
            system_type="autonomous_navigation",
            operation_mode="field_operations",
            base_risk_factors=["collision_risk"],
        )

        assert result.original_sil == "SIL 2"
        assert result.adjusted_sil == "SIL 3"  # Escalated due to multiple risk factors
        assert result.risk_escalation_applied is True
        assert "elevated weather risk" in result.adjustment_reason
        assert "elevated visibility risk" in result.adjustment_reason

    def test_critical_conditions_maximum_escalation(
        self, dynamic_monitor: DynamicSafetyMonitor
    ) -> None:
        """Test maximum SIL escalation under critical conditions."""
        # Create critical conditions
        critical_conditions = DynamicSafetyConditions(
            weather_conditions="snow",
            visibility_meters=10.0,  # Very poor visibility
            bystander_proximity_meters=5.0,  # Very close bystanders
            communication_quality="failed",
            gps_accuracy_meters=15.0,  # Poor GPS
            time_of_day="night",
        )
        dynamic_monitor.update_field_conditions(critical_conditions)

        result = dynamic_monitor.evaluate_dynamic_sil(
            system_type="emergency_stop",  # Already SIL 3
            operation_mode="field_operations",
            base_risk_factors=["collision_risk", "bystander_safety"],
        )

        assert result.adjusted_sil == "SIL 4"  # Maximum escalation
        assert result.risk_escalation_applied is True
        assert len(result.mandatory_actions) > 0
        assert "activate_backup_communication" in result.mandatory_actions

    def test_mandatory_actions_generation(self, dynamic_monitor: DynamicSafetyMonitor) -> None:
        """Test generation of mandatory actions based on risk escalation."""
        conditions = DynamicSafetyConditions(
            communication_quality="failed",
            visibility_meters=15.0,
            bystander_proximity_meters=20.0,
        )
        dynamic_monitor.update_field_conditions(conditions)

        result = dynamic_monitor.evaluate_dynamic_sil(
            system_type="autonomous_navigation",
            operation_mode="field_operations",
            base_risk_factors=[],
        )

        expected_actions = [
            "activate_backup_communication",
            "reduce_operation_speed_50_percent",
            "activate_enhanced_sensor_fusion",
            "reduce_operation_speed_25_percent",
            "activate_proximity_alerts",
            "implement_expanded_safety_zones",
        ]

        for action in expected_actions:
            assert action in result.mandatory_actions

    def test_condition_update_callbacks(self, dynamic_monitor: DynamicSafetyMonitor) -> None:
        """Test condition update callbacks."""
        callback_calls = []

        def test_callback(conditions: DynamicSafetyConditions) -> None:
            callback_calls.append(conditions)

        dynamic_monitor.add_condition_callback(test_callback)

        new_conditions = DynamicSafetyConditions(weather_conditions="fog")
        dynamic_monitor.update_field_conditions(new_conditions)

        assert len(callback_calls) == 1
        assert callback_calls[0].weather_conditions == "fog"


class TestSafetyHeartbeatMonitor:
    """Test safety heartbeat monitoring system."""

    @pytest.fixture
    def heartbeat_monitor(self) -> SafetyHeartbeatMonitor:
        """Create safety heartbeat monitor."""
        return SafetyHeartbeatMonitor(timeout_ms=500)

    def test_monitor_initialization(self, heartbeat_monitor: SafetyHeartbeatMonitor) -> None:
        """Test heartbeat monitor initialization."""
        assert heartbeat_monitor.timeout_ms == 500
        assert len(heartbeat_monitor.heartbeat_status) == 0
        assert heartbeat_monitor.monitoring_active is False

    def test_function_registration(self, heartbeat_monitor: SafetyHeartbeatMonitor) -> None:
        """Test safety function registration."""
        heartbeat_monitor.register_safety_function("emergency_stop")

        assert "emergency_stop" in heartbeat_monitor.heartbeat_status
        status = heartbeat_monitor.heartbeat_status["emergency_stop"]
        assert status.heartbeat_active is True
        assert status.missed_heartbeats == 0

    def test_normal_heartbeat_timing(self, heartbeat_monitor: SafetyHeartbeatMonitor) -> None:
        """Test normal heartbeat timing within limits."""
        heartbeat_monitor.register_safety_function("collision_detection")

        # First heartbeat
        response_time1 = heartbeat_monitor.heartbeat("collision_detection")
        assert response_time1 <= 10.0  # First heartbeat should be very small (< 10ms)

        # Second heartbeat after short delay - optimized for test performance
        time.sleep(0.01)  # 10ms delay (90% faster while maintaining timing validation)
        response_time2 = heartbeat_monitor.heartbeat("collision_detection")

        assert 5 <= response_time2 <= 25  # Should be around 10ms ± tolerance (optimized timing)
        status = heartbeat_monitor.heartbeat_status["collision_detection"]
        assert status.missed_heartbeats == 0
        assert status.emergency_escalation_triggered is False

    def test_heartbeat_timeout_detection(self, heartbeat_monitor: SafetyHeartbeatMonitor) -> None:
        """Test detection of heartbeat timeouts."""
        heartbeat_monitor.register_safety_function("path_validation")

        # Simulate timeout by manually setting last heartbeat time
        status = heartbeat_monitor.heartbeat_status["path_validation"]
        status.last_heartbeat_time = datetime.now() - timedelta(seconds=1)  # 1 second ago

        response_time = heartbeat_monitor.heartbeat("path_validation")

        assert response_time > 500  # Should exceed timeout
        assert status.missed_heartbeats == 1

    def test_emergency_escalation_trigger(self, heartbeat_monitor: SafetyHeartbeatMonitor) -> None:
        """Test emergency escalation after multiple missed heartbeats."""
        emergency_calls = []

        def emergency_callback(function_name: str, status) -> None:
            emergency_calls.append((function_name, status.missed_heartbeats))

        heartbeat_monitor.add_emergency_callback(emergency_callback)
        heartbeat_monitor.register_safety_function("emergency_response")

        # Simulate 3 consecutive timeout heartbeats
        status = heartbeat_monitor.heartbeat_status["emergency_response"]
        for _ in range(3):
            status.last_heartbeat_time = datetime.now() - timedelta(seconds=1)
            heartbeat_monitor.heartbeat("emergency_response")

        assert len(emergency_calls) == 1
        assert emergency_calls[0][0] == "emergency_response"
        assert emergency_calls[0][1] == 3
        assert status.emergency_escalation_triggered is True

    @pytest.mark.asyncio
    async def test_background_monitoring(self, heartbeat_monitor: SafetyHeartbeatMonitor) -> None:
        """Test background heartbeat monitoring."""
        heartbeat_monitor.register_safety_function("background_test")

        # Start monitoring in background
        monitoring_task = asyncio.create_task(heartbeat_monitor.start_monitoring())

        # Wait a short time for monitoring to start - optimized for test performance
        await asyncio.sleep(0.01)  # 10ms (95% faster while maintaining async task startup)

        # Stop monitoring
        heartbeat_monitor.stop_monitoring()
        await asyncio.sleep(0.005)  # Allow task to complete - optimized (95% faster)

        # Clean up
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            pass

        assert heartbeat_monitor.monitoring_active is False


class TestSafetyPerformanceMonitor:
    """Test safety performance monitoring system."""

    @pytest.fixture
    def performance_monitor(self) -> SafetyPerformanceMonitor:
        """Create safety performance monitor."""
        return SafetyPerformanceMonitor()

    def test_monitor_initialization(self, performance_monitor: SafetyPerformanceMonitor) -> None:
        """Test performance monitor initialization."""
        assert len(performance_monitor.function_metrics) == 0
        assert "emergency_stop" in performance_monitor.performance_thresholds
        assert performance_monitor.performance_thresholds["emergency_stop"] == 1000.0

    def test_function_timing_within_limits(
        self, performance_monitor: SafetyPerformanceMonitor
    ) -> None:
        """Test function timing within ISO 25119 limits."""
        start_time = performance_monitor.start_function_timing("collision_detection")
        time.sleep(0.005)  # 5ms execution (90% faster while maintaining timing validation)
        metrics = performance_monitor.end_function_timing("collision_detection", start_time)

        assert metrics.function_name == "collision_detection"
        assert metrics.execution_count == 1
        assert (
            2 <= metrics.average_execution_time_ms <= 15
        )  # Around 5ms ± tolerance (optimized timing)
        assert metrics.iso25119_compliant is True  # Within 100ms limit
        assert metrics.failures == 0

    def test_function_timing_exceeds_limits(
        self, performance_monitor: SafetyPerformanceMonitor
    ) -> None:
        """Test function timing that exceeds ISO 25119 limits."""
        # Temporarily lower threshold for faster test execution
        original_threshold = performance_monitor.performance_thresholds["emergency_stop"]
        performance_monitor.performance_thresholds["emergency_stop"] = 50.0  # 50ms threshold

        start_time = performance_monitor.start_function_timing("emergency_stop")
        time.sleep(0.06)  # 60ms execution - exceeds 50ms test limit (40% faster)
        metrics = performance_monitor.end_function_timing("emergency_stop", start_time)

        assert metrics.iso25119_compliant is False
        assert metrics.average_execution_time_ms > 50.0

        # Restore original threshold
        performance_monitor.performance_thresholds["emergency_stop"] = original_threshold

    def test_failure_tracking(self, performance_monitor: SafetyPerformanceMonitor) -> None:
        """Test tracking of function failures."""
        start_time = performance_monitor.start_function_timing("path_validation")
        time.sleep(0.01)
        metrics = performance_monitor.end_function_timing(
            "path_validation", start_time, success=False
        )

        assert metrics.failures == 1
        assert metrics.execution_count == 1

    def test_system_compliance_check(self, performance_monitor: SafetyPerformanceMonitor) -> None:
        """Test system-wide compliance checking."""
        # Add compliant function
        start_time1 = performance_monitor.start_function_timing("safe_function")
        time.sleep(0.01)
        performance_monitor.end_function_timing("safe_function", start_time1)

        assert performance_monitor.is_system_compliant() is True

        # Add non-compliant function with lowered threshold for fast testing
        original_threshold = performance_monitor.performance_thresholds["emergency_stop"]
        performance_monitor.performance_thresholds["emergency_stop"] = 50.0  # 50ms threshold

        start_time2 = performance_monitor.start_function_timing("emergency_stop")
        time.sleep(0.06)  # 60ms - exceeds 50ms test limit (40% faster)
        performance_monitor.end_function_timing("emergency_stop", start_time2)

        assert performance_monitor.is_system_compliant() is False

        # Restore original threshold
        performance_monitor.performance_thresholds["emergency_stop"] = original_threshold


class TestSafetyAuditLogger:
    """Test safety audit logging system."""

    @pytest.fixture
    def audit_logger(self) -> SafetyAuditLogger:
        """Create safety audit logger."""
        return SafetyAuditLogger(max_events=100)

    def test_logger_initialization(self, audit_logger: SafetyAuditLogger) -> None:
        """Test audit logger initialization."""
        assert len(audit_logger.audit_events) == 0
        assert audit_logger.max_events == 100

    def test_safety_event_logging(self, audit_logger: SafetyAuditLogger) -> None:
        """Test logging of safety events."""
        audit_logger.log_safety_event(
            event_type="sil_adjustment",
            severity="medium",
            description="SIL escalated due to weather conditions",
            safety_function="dynamic_monitoring",
            equipment_id="tractor_001",
            response_actions=["reduce_speed", "activate_sensors"],
            iso25119_context={"original_sil": "SIL 1", "new_sil": "SIL 2"},
        )

        assert len(audit_logger.audit_events) == 1
        event = audit_logger.audit_events[0]
        assert event.event_type == "sil_adjustment"
        assert event.severity == "medium"
        assert event.equipment_id == "tractor_001"
        assert len(event.response_actions) == 2

    def test_event_filtering_by_severity(self, audit_logger: SafetyAuditLogger) -> None:
        """Test filtering events by severity level."""
        # Add events with different severities
        audit_logger.log_safety_event("test1", "low", "Low severity event", "test_function")
        audit_logger.log_safety_event("test2", "critical", "Critical event", "test_function")
        audit_logger.log_safety_event("test3", "medium", "Medium event", "test_function")
        audit_logger.log_safety_event("test4", "critical", "Another critical", "test_function")

        critical_events = audit_logger.get_events_by_severity("critical")
        assert len(critical_events) == 2

        low_events = audit_logger.get_events_by_severity("low")
        assert len(low_events) == 1

    def test_event_filtering_by_function(self, audit_logger: SafetyAuditLogger) -> None:
        """Test filtering events by safety function."""
        audit_logger.log_safety_event("test1", "medium", "Event 1", "emergency_stop")
        audit_logger.log_safety_event("test2", "high", "Event 2", "collision_detection")
        audit_logger.log_safety_event("test3", "low", "Event 3", "emergency_stop")

        emergency_events = audit_logger.get_events_by_function("emergency_stop")
        assert len(emergency_events) == 2

        collision_events = audit_logger.get_events_by_function("collision_detection")
        assert len(collision_events) == 1

    def test_compliance_report_generation(self, audit_logger: SafetyAuditLogger) -> None:
        """Test generation of ISO 25119 compliance reports."""
        # Add test events
        audit_logger.log_safety_event("normal_op", "low", "Normal operation", "monitoring")
        audit_logger.log_safety_event("warning", "medium", "Warning event", "validation")
        audit_logger.log_safety_event("critical", "critical", "Critical failure", "emergency")

        report = audit_logger.generate_compliance_report()

        assert report["total_events"] == 3
        assert report["critical_events"] == 1
        assert report["critical_event_ratio"] == 1 / 3
        assert report["compliance_status"] == "needs_attention"  # >1% critical events

    def test_event_callbacks(self, audit_logger: SafetyAuditLogger) -> None:
        """Test event callbacks for real-time monitoring."""
        callback_events = []

        def test_callback(event) -> None:
            callback_events.append(event)

        audit_logger.add_event_callback(test_callback)

        audit_logger.log_safety_event("callback_test", "high", "Test event", "test_function")

        assert len(callback_events) == 1
        assert callback_events[0].event_type == "callback_test"


class TestCrossLayerSafetyValidator:
    """Test cross-layer safety validation system."""

    @pytest.fixture
    def safety_components(self):
        """Create integrated safety components."""
        dynamic_monitor = DynamicSafetyMonitor()
        heartbeat_monitor = SafetyHeartbeatMonitor()
        performance_monitor = SafetyPerformanceMonitor()
        audit_logger = SafetyAuditLogger()

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

    def test_validator_initialization(self, safety_components) -> None:
        """Test cross-layer validator initialization."""
        validator = safety_components["validator"]

        assert validator.protocol_mapper is not None

        # Verify SIL levels are properly initialized for all safety systems
        assert len(validator.current_sil_levels) == 5  # 5 safety systems in protocol mappings
        assert validator.current_sil_levels["Emergency Stop Command"] == "SIL 3"
        assert validator.current_sil_levels["Vehicle Position"] == "SIL 2"
        assert validator.current_sil_levels["Diagnostic Message 1"] == "SIL 2"
        assert validator.current_sil_levels["Electronic Engine Controller 1"] == "SIL 1"
        assert validator.current_sil_levels["Wheel-Based Vehicle Speed"] == "SIL 1"

        assert validator.emergency_escalation_active is False

    def test_safety_critical_message_validation(self, safety_components) -> None:
        """Test validation of safety-critical J1939 messages."""
        validator = safety_components["validator"]

        # Create emergency stop message (PGN 0xEF00)
        emergency_message = can.Message(
            arbitration_id=0x18EF0000,  # Emergency stop from address 0x00
            data=b"\x01\x00\x00\x00\x00\x00\x00\x00",
            is_extended_id=True,
        )

        result = validator.validate_safety_critical_message(emergency_message)

        assert result.safety_critical is True
        assert result.criticality_level == SafetyCriticalityLevel.SAFETY_CRITICAL
        assert result.required_sil_level == "SIL 3"

    def test_non_critical_message_handling(self, safety_components) -> None:
        """Test handling of non-critical messages."""
        validator = safety_components["validator"]

        # Create non-mapped message
        normal_message = can.Message(
            arbitration_id=0x18DEAD00,  # Unknown PGN
            data=b"\x01\x02\x03\x04",
            is_extended_id=True,
        )

        result = validator.validate_safety_critical_message(normal_message)

        assert result.safety_critical is False
        assert result.criticality_level == SafetyCriticalityLevel.NON_CRITICAL
        assert result.validation_passed is True

    def test_sil_compliance_validation(self, safety_components) -> None:
        """Test SIL compliance validation."""
        validator = safety_components["validator"]

        # Set current SIL level lower than required
        validator.current_sil_levels["Vehicle Position"] = "SIL 1"

        # Create GPS position message (requires SIL 2)
        gps_message = can.Message(
            arbitration_id=0x18FEF300,  # Vehicle Position from address 0x00
            data=b"\x12\x34\x56\x78\x9A\xBC\xDE\xF0",
            is_extended_id=True,
        )

        result = validator.validate_safety_critical_message(gps_message)

        assert result.validation_passed is False
        assert "inadequate" in result.validation_errors[0]
        assert "escalate_sil_level" in result.mandatory_actions

    def test_emergency_response_trigger(self, safety_components) -> None:
        """Test emergency response triggering."""
        validator = safety_components["validator"]
        audit_logger = safety_components["audit_logger"]

        # Create malformed emergency stop message
        malformed_emergency = can.Message(
            arbitration_id=0x18EF0099,  # Emergency stop from unauthorized address
            data=b"\xFF",  # Invalid data
            is_extended_id=True,
        )

        result = validator.validate_safety_critical_message(malformed_emergency)

        # Should trigger emergency response due to validation failure
        assert result.criticality_level == SafetyCriticalityLevel.SAFETY_CRITICAL
        assert result.validation_passed is False

        # Check that emergency event was logged
        critical_events = audit_logger.get_events_by_severity("critical")
        assert len(critical_events) > 0

    def test_safety_status_reporting(self, safety_components) -> None:
        """Test comprehensive safety status reporting."""
        validator = safety_components["validator"]

        status = validator.get_safety_status()

        assert "current_sil_levels" in status
        assert "emergency_escalation_active" in status
        assert "recent_violations" in status
        assert "heartbeat_status" in status
        assert "performance_compliant" in status


class TestDTCSafetyAnalyzer:
    """Test DTC safety analysis system."""

    @pytest.fixture
    def dtc_analyzer(self):
        """Create DTC safety analyzer."""
        dynamic_monitor = DynamicSafetyMonitor()
        audit_logger = SafetyAuditLogger()
        return DTCSafetyAnalyzer(dynamic_monitor, audit_logger)

    def test_analyzer_initialization(self, dtc_analyzer: DTCSafetyAnalyzer) -> None:
        """Test DTC analyzer initialization."""
        assert len(dtc_analyzer.safety_critical_spns) > 0
        assert 110 in dtc_analyzer.safety_critical_spns  # Engine coolant temperature
        assert 9999 in dtc_analyzer.safety_critical_spns  # Emergency stop system

    def test_critical_dtc_analysis(self, dtc_analyzer: DTCSafetyAnalyzer) -> None:
        """Test analysis of critical DTCs."""
        # Create mock emergency stop system DTC
        emergency_dtc = Mock()
        emergency_dtc.spn = 9999
        emergency_dtc.fmi = 15
        emergency_dtc.occurrence_count = 1
        emergency_dtc.timestamp = datetime.now()

        analysis = dtc_analyzer.analyze_dtc_safety_impact(emergency_dtc)

        assert analysis.safety_impact == "critical"
        assert analysis.required_response == "emergency_stop"
        assert analysis.sil_escalation_required is True
        assert analysis.new_sil_level == "SIL 3"
        assert "immediate_stop" in analysis.mandatory_actions

    def test_engine_dtc_analysis(self, dtc_analyzer: DTCSafetyAnalyzer) -> None:
        """Test analysis of engine-related DTCs."""
        # Create mock engine coolant temperature DTC
        coolant_dtc = Mock()
        coolant_dtc.spn = 110
        coolant_dtc.fmi = 16
        coolant_dtc.occurrence_count = 3
        coolant_dtc.timestamp = datetime.now()

        analysis = dtc_analyzer.analyze_dtc_safety_impact(coolant_dtc)

        assert analysis.safety_impact == "high"
        assert analysis.required_response == "alert"
        assert analysis.sil_escalation_required is True
        assert analysis.new_sil_level == "SIL 2"
        assert "reduce_engine_load" in analysis.mandatory_actions

    def test_low_priority_dtc_analysis(self, dtc_analyzer: DTCSafetyAnalyzer) -> None:
        """Test analysis of low-priority DTCs."""
        # Create mock non-critical DTC
        non_critical_dtc = Mock()
        non_critical_dtc.spn = 1234
        non_critical_dtc.fmi = 2
        non_critical_dtc.occurrence_count = 1
        non_critical_dtc.timestamp = datetime.now()

        analysis = dtc_analyzer.analyze_dtc_safety_impact(non_critical_dtc)

        assert analysis.safety_impact == "low"
        assert analysis.required_response == "log"
        assert analysis.sil_escalation_required is False
        assert analysis.new_sil_level is None


class TestIntegratedSafetySystem:
    """Test integrated safety system functionality."""

    @pytest.mark.asyncio
    async def test_complete_safety_monitoring_workflow(self) -> None:
        """Test complete safety monitoring workflow."""
        # Initialize all components
        dynamic_monitor = DynamicSafetyMonitor()
        heartbeat_monitor = SafetyHeartbeatMonitor()
        performance_monitor = SafetyPerformanceMonitor()
        audit_logger = SafetyAuditLogger()

        validator = CrossLayerSafetyValidator(
            dynamic_monitor, heartbeat_monitor, performance_monitor, audit_logger
        )

        dtc_analyzer = DTCSafetyAnalyzer(dynamic_monitor, audit_logger)

        # 1. Update field conditions to adverse
        adverse_conditions = DynamicSafetyConditions(
            weather_conditions="rain",
            visibility_meters=40.0,
            communication_quality="poor",
        )
        dynamic_monitor.update_field_conditions(adverse_conditions)

        # 2. Validate safety-critical message
        emergency_message = can.Message(
            arbitration_id=0x18EF0000,
            data=b"\x01\x00\x00\x00\x00\x00\x00\x00",
            is_extended_id=True,
        )

        validation_result = validator.validate_safety_critical_message(emergency_message)

        # 3. Analyze critical DTC
        critical_dtc = Mock()
        critical_dtc.spn = 9999
        critical_dtc.fmi = 15
        critical_dtc.occurrence_count = 1
        critical_dtc.timestamp = datetime.now()

        dtc_analysis = dtc_analyzer.analyze_dtc_safety_impact(critical_dtc)

        # 4. Check overall system status
        safety_status = validator.get_safety_status()
        compliance_report = audit_logger.generate_compliance_report()

        # Verify integrated functionality
        assert validation_result.safety_critical is True
        assert dtc_analysis.safety_impact == "critical"
        assert compliance_report["total_events"] > 0
        assert "heartbeat_status" in safety_status

    def test_safety_escalation_cascade(self) -> None:
        """Test cascading safety escalation across systems."""
        # Initialize components
        dynamic_monitor = DynamicSafetyMonitor()
        audit_logger = SafetyAuditLogger()
        dtc_analyzer = DTCSafetyAnalyzer(dynamic_monitor, audit_logger)

        # Create critical conditions
        critical_conditions = DynamicSafetyConditions(
            weather_conditions="snow",
            visibility_meters=10.0,
            bystander_proximity_meters=5.0,
            communication_quality="failed",
        )
        dynamic_monitor.update_field_conditions(critical_conditions)

        # Trigger SIL escalation through dynamic conditions
        sil_result = dynamic_monitor.evaluate_dynamic_sil(
            "emergency_stop", "autonomous_operation", ["bystander_safety"]
        )

        # Trigger additional escalation through DTC
        emergency_dtc = Mock()
        emergency_dtc.spn = 9999
        emergency_dtc.fmi = 15
        emergency_dtc.occurrence_count = 1
        emergency_dtc.timestamp = datetime.now()

        dtc_analysis = dtc_analyzer.analyze_dtc_safety_impact(emergency_dtc)

        # Verify cascading effects
        assert sil_result.adjusted_sil == "SIL 4"  # Maximum escalation
        assert dtc_analysis.required_response == "emergency_stop"
        assert len(audit_logger.audit_events) >= 2  # Both events logged

        # Check for critical events in audit trail
        critical_events = audit_logger.get_events_by_severity("critical")
        assert len(critical_events) >= 1
