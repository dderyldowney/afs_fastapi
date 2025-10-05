"""Tests for EmergencyStopPropagation - TDD RED Phase Implementation.

This module implements comprehensive unit tests for the EmergencyStopPropagation
system, which coordinates fleet-wide emergency stops using vector clock causal
ordering and guaranteed message delivery for agricultural robotics safety.

Agricultural Context
--------------------
Emergency stop propagation is the most critical safety component for autonomous
agricultural fleet operations. It must ensure that when any tractor detects a
safety hazard (obstacle, equipment failure, operator intervention), all tractors
in the fleet immediately stop operations within 500ms to prevent accidents.

The system implements ISO 18497 safety requirements:
- Performance Level D (PLd) for autonomous agricultural equipment
- Sub-500ms emergency stop propagation fleet-wide
- Guaranteed message delivery with acknowledgment tracking
- Causal ordering prevents conflicting emergency responses
- Fail-safe escalation for unacknowledged emergencies

Test Strategy
-------------
Tests follow TDD methodology with agricultural domain scenarios:
1. RED Phase: Failing tests defining expected emergency coordination behavior
2. GREEN Phase: Minimal implementation meeting safety requirements
3. REFACTOR Phase: Enhanced implementation with enterprise reliability

These tests ensure safety-critical agricultural operations meet ISO 18497
compliance and distributed systems reliability for commercial deployment.
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, Mock

import pytest

from afs_fastapi.equipment.reliable_isobus import ReliableISOBUSDevice
from afs_fastapi.services.emergency_stop_propagation import (
    EmergencyReasonCode,
    EmergencySeverity,
    EmergencyStopPropagation,
    PropagationStatus,
)
from afs_fastapi.services.fleet import FleetCoordinationEngine
from afs_fastapi.services.synchronization import VectorClock


class TestEmergencyStopPropagationCore:
    """Test core functionality of EmergencyStopPropagation system.

    Tests the fundamental emergency stop triggering, propagation, and
    acknowledgment tracking required for fleet-wide safety coordination.
    """

    def test_initialization_with_fleet_coordination_components(self) -> None:
        """Test EmergencyStopPropagation initialization with required components.

        Agricultural Context:
        Each tractor must have emergency stop coordination integrated with
        its fleet coordination engine, vector clock for causal ordering,
        and reliable ISOBUS interface for guaranteed message delivery.
        """
        # Arrange
        mock_fleet_coordination = Mock()
        mock_fleet_coordination.get_fleet_status.return_value = {}
        mock_vector_clock = Mock()
        mock_isobus = Mock()
        mock_isobus.broadcast_priority_message = AsyncMock()
        mock_isobus.send_message = Mock()

        # Act
        emergency_system = EmergencyStopPropagation(
            fleet_coordination=mock_fleet_coordination,
            vector_clock=mock_vector_clock,
            isobus=mock_isobus,
        )

        # Assert
        assert emergency_system.fleet_coordination == mock_fleet_coordination
        assert emergency_system.vector_clock == mock_vector_clock
        assert emergency_system.isobus == mock_isobus
        assert emergency_system.is_emergency_active is False

    @pytest.mark.asyncio
    async def test_trigger_emergency_stop_with_immediate_state_transition(self) -> None:
        """Test triggering emergency stop causes immediate local state transition.

        Agricultural Context:
        When a tractor detects a safety hazard (obstacle detected by LiDAR,
        equipment malfunction, operator emergency button), it must immediately
        transition to emergency stop state before attempting fleet coordination.
        This ensures local safety even if communication fails.
        """
        # Arrange
        mock_fleet_coordination = AsyncMock(spec=FleetCoordinationEngine)
        mock_vector_clock = Mock(spec=VectorClock)
        mock_isobus = AsyncMock(spec=ReliableISOBUSDevice)

        emergency_system = EmergencyStopPropagation(
            fleet_coordination=mock_fleet_coordination,
            vector_clock=mock_vector_clock,
            isobus=mock_isobus,
        )

        reason_code = EmergencyReasonCode.OBSTACLE_DETECTED
        source_position = {"lat": 41.8781, "lon": -87.6298}
        severity = EmergencySeverity.CRITICAL

        # Act
        result = await emergency_system.trigger_emergency_stop(
            reason_code=reason_code, source_position=source_position, severity=severity
        )

        # Assert
        # Verify immediate local emergency state activation
        assert emergency_system.is_emergency_active is True
        assert result.emergency_id is not None
        assert result.local_stop_executed is True

        # Verify fleet coordination engine state transition
        mock_fleet_coordination.broadcast_emergency_stop.assert_called_once()
        call_args = mock_fleet_coordination.broadcast_emergency_stop.call_args
        assert call_args[0][0] == reason_code.value

    @pytest.mark.asyncio
    async def test_emergency_stop_vector_clock_increment(self) -> None:
        """Test emergency stop increments vector clock for causal ordering.

        Agricultural Context:
        Vector clocks ensure proper causal ordering of emergency events
        across the fleet. When a tractor triggers an emergency stop,
        it must increment its logical clock to establish happens-before
        relationships with subsequent fleet coordination events.
        """
        # Arrange
        mock_fleet_coordination = AsyncMock(spec=FleetCoordinationEngine)
        mock_vector_clock = Mock(spec=VectorClock)
        mock_vector_clock.get_process_ids.return_value = ["TRACTOR_001"]
        mock_isobus = AsyncMock(spec=ReliableISOBUSDevice)

        emergency_system = EmergencyStopPropagation(
            fleet_coordination=mock_fleet_coordination,
            vector_clock=mock_vector_clock,
            isobus=mock_isobus,
        )
        emergency_system.tractor_id = "TRACTOR_001"

        # Act
        await emergency_system.trigger_emergency_stop(
            reason_code=EmergencyReasonCode.SYSTEM_FAULT,
            source_position={"lat": 42.3601, "lon": -71.0589},
            severity=EmergencySeverity.HIGH,
        )

        # Assert
        # Vector clock must be incremented for local emergency event
        mock_vector_clock.increment.assert_called_once_with("TRACTOR_001")

    @pytest.mark.asyncio
    async def test_emergency_stop_broadcast_with_guaranteed_delivery(self) -> None:
        """Test emergency stop broadcast uses guaranteed delivery messaging.

        Agricultural Context:
        Emergency stops are safety-critical and must reach all tractors
        in the fleet. The system uses ReliableISOBUSDevice with highest
        priority (ISOBUSPriority.EMERGENCY_STOP = 0) and acknowledgment
        tracking to ensure delivery despite network issues.
        """
        # Arrange
        mock_fleet_coordination = AsyncMock(spec=FleetCoordinationEngine)
        mock_vector_clock = Mock(spec=VectorClock)
        mock_vector_clock.to_dict.return_value = {"TRACTOR_001": 5}
        mock_isobus = AsyncMock(spec=ReliableISOBUSDevice)

        emergency_system = EmergencyStopPropagation(
            fleet_coordination=mock_fleet_coordination,
            vector_clock=mock_vector_clock,
            isobus=mock_isobus,
        )
        emergency_system.tractor_id = "TRACTOR_001"

        # Act
        await emergency_system.trigger_emergency_stop(
            reason_code=EmergencyReasonCode.OPERATOR_INTERVENTION,
            source_position={"lat": 40.7128, "lon": -74.0060},
            severity=EmergencySeverity.CRITICAL,
        )

        # Assert
        # Verify guaranteed delivery emergency message broadcast
        mock_isobus.broadcast_priority_message.assert_called_once()
        broadcast_args = mock_isobus.broadcast_priority_message.call_args
        message = broadcast_args[0][0]

        assert message["msg_type"] == "EMERGENCY_STOP"
        assert message["sender_id"] == "TRACTOR_001"
        assert message["vector_clock"] == {"TRACTOR_001": 5}
        assert message["payload"]["reason_code"] == "OPERATOR_INTERVENTION"
        assert message["payload"]["severity"] == "CRITICAL"
        assert message["payload"]["source_position"] == {"lat": 40.7128, "lon": -74.0060}

    @pytest.mark.asyncio
    async def test_emergency_acknowledgment_tracking(self) -> None:
        """Test tracking acknowledgments from all fleet members.

        Agricultural Context:
        For safety compliance, the system must track which tractors
        have acknowledged the emergency stop. This ensures all equipment
        received the safety-critical message and enables escalation
        procedures if any tractors fail to respond within timeout.
        """
        # Arrange
        mock_fleet_coordination = AsyncMock(spec=FleetCoordinationEngine)
        mock_fleet_coordination.get_fleet_status.return_value = {
            "TRACTOR_002": {"status": "WORKING"},
            "TRACTOR_003": {"status": "IDLE"},
            "TRACTOR_004": {"status": "WORKING"},
        }

        mock_vector_clock = Mock(spec=VectorClock)
        mock_isobus = AsyncMock(spec=ReliableISOBUSDevice)

        emergency_system = EmergencyStopPropagation(
            fleet_coordination=mock_fleet_coordination,
            vector_clock=mock_vector_clock,
            isobus=mock_isobus,
        )

        # Trigger emergency stop
        result = await emergency_system.trigger_emergency_stop(
            reason_code=EmergencyReasonCode.COLLISION_DETECTED,
            source_position={"lat": 41.8801, "lon": -87.6278},
            severity=EmergencySeverity.CRITICAL,
        )

        # Act - Simulate acknowledgments from fleet members
        await emergency_system.receive_emergency_acknowledgment(
            emergency_id=result.emergency_id, acknowledging_tractor="TRACTOR_002"
        )
        await emergency_system.receive_emergency_acknowledgment(
            emergency_id=result.emergency_id, acknowledging_tractor="TRACTOR_003"
        )

        # Assert
        tracking_status = emergency_system.get_acknowledgment_status(result.emergency_id)
        assert "TRACTOR_002" in tracking_status.acknowledged_tractors
        assert "TRACTOR_003" in tracking_status.acknowledged_tractors
        assert "TRACTOR_004" in tracking_status.pending_acknowledgments
        assert tracking_status.all_acknowledged is False


class TestEmergencyStopReception:
    """Test emergency stop message reception and causal ordering.

    Tests how tractors process received emergency stop messages,
    including vector clock causal ordering and conflict resolution.
    """

    @pytest.mark.asyncio
    async def test_receive_emergency_stop_with_causal_ordering(self) -> None:
        """Test processing emergency stop with vector clock causal ordering.

        Agricultural Context:
        When a tractor receives an emergency stop message from another
        tractor, it must use vector clock comparison to determine the
        causal relationship and ensure proper emergency response ordering.
        This prevents conflicting emergency responses in distributed systems.
        """
        # Arrange
        mock_fleet_coordination = AsyncMock(spec=FleetCoordinationEngine)
        mock_vector_clock = Mock(spec=VectorClock)
        mock_isobus = AsyncMock(spec=ReliableISOBUSDevice)

        emergency_system = EmergencyStopPropagation(
            fleet_coordination=mock_fleet_coordination,
            vector_clock=mock_vector_clock,
            isobus=mock_isobus,
        )

        # Simulate received emergency stop message
        sender_clock = Mock(spec=VectorClock)
        sender_clock.happens_before.return_value = False  # Sender clock is concurrent/after

        emergency_message = {
            "msg_type": "EMERGENCY_STOP",
            "sender_id": "TRACTOR_SENDER_005",
            "emergency_id": "EMERGENCY_001",
            "vector_clock": {"TRACTOR_SENDER_005": 3, "TRACTOR_001": 2},
            "payload": {
                "reason_code": "EQUIPMENT_MALFUNCTION",
                "severity": "HIGH",
                "source_position": {"lat": 39.7391, "lon": -104.9847},
            },
        }

        # Act
        await emergency_system.receive_emergency_stop(
            message=emergency_message, sender_clock=sender_clock
        )

        # Assert
        # Vector clock should be updated with received message
        mock_vector_clock.update_with_received_message.assert_called_once()

        # Fleet coordination should transition to emergency stop
        mock_fleet_coordination.broadcast_emergency_stop.assert_called_once()
        assert emergency_system.is_emergency_active is True

    @pytest.mark.asyncio
    async def test_emergency_stop_conflict_resolution_by_severity(self) -> None:
        """Test emergency stop conflict resolution using severity levels.

        Agricultural Context:
        When multiple emergency stops occur simultaneously (concurrent
        vector clock events), the system must resolve conflicts using
        emergency severity as tiebreaker. CRITICAL severity takes
        precedence over HIGH, which takes precedence over MEDIUM.
        """
        # Arrange
        mock_fleet_coordination = AsyncMock(spec=FleetCoordinationEngine)
        mock_vector_clock = Mock(spec=VectorClock)
        mock_isobus = AsyncMock(spec=ReliableISOBUSDevice)

        emergency_system = EmergencyStopPropagation(
            fleet_coordination=mock_fleet_coordination,
            vector_clock=mock_vector_clock,
            isobus=mock_isobus,
        )

        # Simulate local emergency (MEDIUM severity)
        await emergency_system.trigger_emergency_stop(
            reason_code=EmergencyReasonCode.MAINTENANCE_REQUIRED,
            source_position={"lat": 45.5152, "lon": -122.6784},
            severity=EmergencySeverity.MEDIUM,
        )

        # Simulate concurrent emergency from another tractor (CRITICAL severity)
        concurrent_clock = Mock(spec=VectorClock)
        concurrent_clock.happens_before.return_value = False
        mock_vector_clock.happens_before.return_value = False  # Events are concurrent

        critical_message = {
            "msg_type": "EMERGENCY_STOP",
            "sender_id": "TRACTOR_CRITICAL_006",
            "emergency_id": "EMERGENCY_CRITICAL_001",
            "vector_clock": {"TRACTOR_CRITICAL_006": 2, "TRACTOR_001": 1},
            "payload": {
                "reason_code": "PERSON_IN_FIELD",
                "severity": "CRITICAL",
                "source_position": {"lat": 45.5162, "lon": -122.6794},
            },
        }

        # Act
        await emergency_system.receive_emergency_stop(
            message=critical_message, sender_clock=concurrent_clock
        )

        # Assert
        # Critical severity should override local medium severity
        active_emergency = emergency_system.get_active_emergency()
        assert active_emergency is not None
        assert active_emergency.emergency_id == "EMERGENCY_CRITICAL_001"
        assert active_emergency.severity == EmergencySeverity.CRITICAL
        assert active_emergency.reason_code == EmergencyReasonCode.PERSON_IN_FIELD

    @pytest.mark.asyncio
    async def test_emergency_stop_acknowledgment_automatic_sending(self) -> None:
        """Test automatic acknowledgment sending for received emergency stops.

        Agricultural Context:
        When a tractor receives and processes an emergency stop message,
        it must automatically send an acknowledgment back to the sender
        to confirm receipt. This enables the sender to track fleet-wide
        acknowledgment status for safety compliance verification.
        """
        # Arrange
        mock_fleet_coordination = Mock()
        mock_fleet_coordination.get_fleet_status.return_value = {}
        mock_vector_clock = Mock()
        mock_isobus = Mock()
        mock_isobus.broadcast_priority_message = AsyncMock()
        mock_isobus.send_message = Mock()

        emergency_system = EmergencyStopPropagation(
            fleet_coordination=mock_fleet_coordination,
            vector_clock=mock_vector_clock,
            isobus=mock_isobus,
        )
        emergency_system.tractor_id = "TRACTOR_RECEIVER_007"

        # Act
        await emergency_system.send_emergency_acknowledgment(
            emergency_id="EMERGENCY_002", sender_tractor_id="TRACTOR_SENDER_008"
        )

        # Assert
        # Acknowledgment message should be sent via ISOBUS
        mock_isobus.send_message.assert_called_once()
        ack_message = mock_isobus.send_message.call_args[0][0]

        assert ack_message["msg_type"] == "EMERGENCY_ACKNOWLEDGMENT"
        assert ack_message["sender_id"] == "TRACTOR_RECEIVER_007"
        assert ack_message["payload"]["emergency_id"] == "EMERGENCY_002"
        assert ack_message["payload"]["acknowledging_tractor"] == "TRACTOR_RECEIVER_007"


class TestEmergencyStopPropagationTiming:
    """Test emergency stop propagation timing and performance requirements.

    Tests critical timing requirements for agricultural safety including
    sub-500ms fleet-wide propagation and timeout-based escalation.
    """

    @pytest.mark.asyncio
    async def test_sub_500ms_fleet_propagation_requirement(self) -> None:
        """Test emergency stop propagation meets sub-500ms requirement.

        Agricultural Context:
        ISO 18497 requires emergency stop propagation to reach all fleet
        members within 500ms to prevent agricultural accidents. This test
        validates timing performance under ideal network conditions.
        """
        # Arrange
        mock_fleet_coordination = AsyncMock(spec=FleetCoordinationEngine)
        mock_vector_clock = Mock(spec=VectorClock)
        mock_isobus = AsyncMock(spec=ReliableISOBUSDevice)

        # Simulate fast acknowledgment responses
        async def fast_acknowledgment(*args, **kwargs):
            await asyncio.sleep(0.05)  # 50ms response time

        mock_isobus.broadcast_priority_message.side_effect = fast_acknowledgment

        emergency_system = EmergencyStopPropagation(
            fleet_coordination=mock_fleet_coordination,
            vector_clock=mock_vector_clock,
            isobus=mock_isobus,
        )

        # Act
        start_time = time.perf_counter()

        result = await emergency_system.trigger_emergency_stop(
            reason_code=EmergencyReasonCode.OBSTACLE_DETECTED,
            source_position={"lat": 37.7749, "lon": -122.4194},
            severity=EmergencySeverity.CRITICAL,
        )

        # Simulate rapid acknowledgments from 3 fleet members
        for i in range(3):
            await emergency_system.receive_emergency_acknowledgment(
                emergency_id=result.emergency_id, acknowledging_tractor=f"TRACTOR_{i+10:03d}"
            )

        end_time = time.perf_counter()
        propagation_time = (end_time - start_time) * 1000  # Convert to milliseconds

        # Assert
        assert propagation_time < 500.0  # Must be under 500ms
        assert result.propagation_initiated is True

    @pytest.mark.asyncio
    async def test_acknowledgment_timeout_escalation(self) -> None:
        """Test escalation when emergency acknowledgments timeout.

        Agricultural Context:
        If tractors fail to acknowledge emergency stops within timeout
        (indicating potential communication failure or equipment problems),
        the system must escalate with redundant emergency broadcasts
        and operator notification for manual intervention.
        """
        # Arrange
        mock_fleet_coordination = AsyncMock(spec=FleetCoordinationEngine)
        mock_vector_coordination = Mock(spec=VectorClock)
        mock_isobus = AsyncMock(spec=ReliableISOBUSDevice)

        emergency_system = EmergencyStopPropagation(
            fleet_coordination=mock_fleet_coordination,
            vector_clock=mock_vector_coordination,
            isobus=mock_isobus,
            acknowledgment_timeout=1.0,  # 1 second timeout for testing
        )

        # Configure mock fleet with 4 tractors
        mock_fleet_coordination.get_fleet_status.return_value = {
            "TRACTOR_A": {"status": "WORKING"},
            "TRACTOR_B": {"status": "WORKING"},
            "TRACTOR_C": {"status": "IDLE"},
            "TRACTOR_D": {"status": "WORKING"},
        }

        # Trigger emergency stop
        result = await emergency_system.trigger_emergency_stop(
            reason_code=EmergencyReasonCode.COLLISION_DETECTED,
            source_position={"lat": 34.0522, "lon": -118.2437},
            severity=EmergencySeverity.CRITICAL,
        )

        # Simulate partial acknowledgments (only 2 out of 4 tractors respond)
        await emergency_system.receive_emergency_acknowledgment(
            emergency_id=result.emergency_id, acknowledging_tractor="TRACTOR_A"
        )
        await emergency_system.receive_emergency_acknowledgment(
            emergency_id=result.emergency_id, acknowledging_tractor="TRACTOR_B"
        )

        # Act - Wait for timeout and check escalation
        await asyncio.sleep(1.2)  # Wait beyond timeout
        escalation_result = await emergency_system.check_and_escalate(result.emergency_id)

        # Assert
        assert escalation_result.escalation_triggered is True
        assert escalation_result.unacknowledged_tractors == ["TRACTOR_C", "TRACTOR_D"]

        # Should trigger redundant emergency broadcast
        assert mock_isobus.broadcast_priority_message.call_count >= 2

    def test_emergency_propagation_validation(self) -> None:
        """Test validation of emergency propagation completeness.

        Agricultural Context:
        For safety compliance documentation, the system must validate
        that emergency stops successfully propagated to all fleet members
        with proper vector clock ordering and acknowledgment confirmation.
        """
        # Arrange
        mock_fleet_coordination = Mock()
        mock_fleet_coordination.get_fleet_status.return_value = {}
        mock_vector_clock = Mock()
        mock_isobus = Mock()
        mock_isobus.broadcast_priority_message = AsyncMock()
        mock_isobus.send_message = Mock()

        emergency_system = EmergencyStopPropagation(
            fleet_coordination=mock_fleet_coordination,
            vector_clock=mock_vector_clock,
            isobus=mock_isobus,
        )

        emergency_id = "EMERGENCY_VALIDATION_001"
        fleet_size = 5
        timeout_seconds = 2.0

        # Simulate complete propagation (all tractors acknowledged)
        for i in range(fleet_size):
            emergency_system._acknowledged_tractors[emergency_id] = (
                emergency_system._acknowledged_tractors.get(emergency_id, set())
            )
            emergency_system._acknowledged_tractors[emergency_id].add(f"TRACTOR_{i+1:03d}")

        # Act
        validation_result = emergency_system.validate_emergency_propagation(
            emergency_id=emergency_id, fleet_size=fleet_size, timeout_seconds=timeout_seconds
        )

        # Assert
        assert validation_result == PropagationStatus.COMPLETE
        assert len(emergency_system._acknowledged_tractors[emergency_id]) == fleet_size


class TestEmergencyStopFailSafeBehaviors:
    """Test fail-safe behaviors during emergency stop scenarios.

    Tests system behavior when emergency stops encounter failures,
    network issues, or other safety-critical error conditions.
    """

    @pytest.mark.asyncio
    async def test_emergency_stop_during_network_partition(self) -> None:
        """Test emergency stop behavior during network partition.

        Agricultural Context:
        Network partitions can isolate tractors during field operations.
        If an emergency occurs on one side of the partition, the system
        must ensure safe behavior for isolated tractors and proper
        synchronization when connectivity is restored.
        """
        # Arrange
        mock_fleet_coordination = AsyncMock(spec=FleetCoordinationEngine)
        mock_vector_clock = Mock(spec=VectorClock)
        mock_isobus = AsyncMock(spec=ReliableISOBUSDevice)

        # Simulate network partition by making broadcasts fail
        mock_isobus.broadcast_priority_message.side_effect = TimeoutError("Network partition")

        emergency_system = EmergencyStopPropagation(
            fleet_coordination=mock_fleet_coordination,
            vector_clock=mock_vector_clock,
            isobus=mock_isobus,
        )

        # Act
        result = await emergency_system.trigger_emergency_stop(
            reason_code=EmergencyReasonCode.SYSTEM_FAULT,
            source_position={"lat": 29.7604, "lon": -95.3698},
            severity=EmergencySeverity.CRITICAL,
        )

        # Assert
        # Local emergency stop should still execute despite network failure
        assert result.local_stop_executed is True
        assert emergency_system.is_emergency_active is True

        # Should attempt to queue message for later transmission
        assert result.network_broadcast_failed is True
        assert result.queued_for_retry is True

    @pytest.mark.asyncio
    async def test_multiple_concurrent_emergency_stops(self) -> None:
        """Test handling of multiple simultaneous emergency stops.

        Agricultural Context:
        Multiple tractors may detect different safety hazards simultaneously
        (e.g., person in field, obstacle detected, equipment malfunction).
        The system must handle concurrent emergency stops with proper
        priority resolution and unified fleet emergency response.
        """
        # Arrange
        mock_fleet_coordination = AsyncMock(spec=FleetCoordinationEngine)
        mock_vector_clock = Mock(spec=VectorClock)
        mock_isobus = AsyncMock(spec=ReliableISOBUSDevice)

        emergency_system = EmergencyStopPropagation(
            fleet_coordination=mock_fleet_coordination,
            vector_clock=mock_vector_clock,
            isobus=mock_isobus,
        )

        # Act - Simulate multiple concurrent emergencies
        emergency_tasks = [
            emergency_system.trigger_emergency_stop(
                reason_code=EmergencyReasonCode.PERSON_IN_FIELD,
                source_position={"lat": 41.8781, "lon": -87.6298},
                severity=EmergencySeverity.CRITICAL,
            ),
            emergency_system.trigger_emergency_stop(
                reason_code=EmergencyReasonCode.OBSTACLE_DETECTED,
                source_position={"lat": 41.8791, "lon": -87.6308},
                severity=EmergencySeverity.HIGH,
            ),
            emergency_system.trigger_emergency_stop(
                reason_code=EmergencyReasonCode.EQUIPMENT_MALFUNCTION,
                source_position={"lat": 41.8801, "lon": -87.6318},
                severity=EmergencySeverity.MEDIUM,
            ),
        ]

        results = await asyncio.gather(*emergency_tasks)

        # Assert
        # System should handle all emergencies but prioritize by severity
        assert all(result.local_stop_executed for result in results)

        # Highest severity (CRITICAL) should be the active emergency
        active_emergency = emergency_system.get_active_emergency()
        assert active_emergency is not None
        assert active_emergency.reason_code == EmergencyReasonCode.PERSON_IN_FIELD
        assert active_emergency.severity == EmergencySeverity.CRITICAL

    def test_emergency_stop_audit_trail(self) -> None:
        """Test comprehensive audit trail for emergency stop events.

        Agricultural Context:
        Safety compliance requires detailed audit trails of all emergency
        events including timestamps, reason codes, fleet response times,
        and acknowledgment tracking. This data is essential for incident
        analysis and regulatory compliance documentation.
        """
        # Arrange
        mock_fleet_coordination = Mock()
        mock_fleet_coordination.get_fleet_status.return_value = {}
        mock_vector_clock = Mock()
        mock_isobus = Mock()
        mock_isobus.broadcast_priority_message = AsyncMock()
        mock_isobus.send_message = Mock()

        emergency_system = EmergencyStopPropagation(
            fleet_coordination=mock_fleet_coordination,
            vector_clock=mock_vector_clock,
            isobus=mock_isobus,
        )

        emergency_id = "EMERGENCY_AUDIT_001"

        # Simulate emergency events for audit trail
        emergency_system._log_emergency_event(
            emergency_id=emergency_id,
            event_type="EMERGENCY_TRIGGERED",
            tractor_id="TRACTOR_001",
            reason_code=EmergencyReasonCode.COLLISION_DETECTED,
            severity=EmergencySeverity.CRITICAL,
            additional_data={"detection_sensor": "LiDAR_FRONT", "distance": 2.5},
        )

        emergency_system._log_emergency_event(
            emergency_id=emergency_id,
            event_type="ACKNOWLEDGMENT_RECEIVED",
            tractor_id="TRACTOR_002",
            response_time_ms=125.5,
        )

        # Act
        audit_trail = emergency_system.get_emergency_audit_trail(emergency_id)

        # Assert
        assert len(audit_trail.events) == 2

        trigger_event = audit_trail.events[0]
        assert trigger_event.event_type == "EMERGENCY_TRIGGERED"
        assert trigger_event.reason_code == EmergencyReasonCode.COLLISION_DETECTED
        assert trigger_event.severity == EmergencySeverity.CRITICAL
        assert trigger_event.additional_data["detection_sensor"] == "LiDAR_FRONT"

        ack_event = audit_trail.events[1]
        assert ack_event.event_type == "ACKNOWLEDGMENT_RECEIVED"
        assert ack_event.tractor_id == "TRACTOR_002"
        assert ack_event.response_time_ms == 125.5
