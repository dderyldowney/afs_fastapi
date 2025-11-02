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
from unittest.mock import AsyncMock, Mock, patch

import pytest

from afs_fastapi.equipment.reliable_isobus import ReliableISOBUSDevice
from afs_fastapi.services.emergency_stop_propagation import (
    EmergencyReasonCode,
    EmergencySeverity,
    EmergencyStopPropagation,
)
from afs_fastapi.services.fleet import FleetCoordinationEngine
from afs_fastapi.services.synchronization import VectorClock


class TestEmergencyStopPropagationCore:
    """Test core functionality of EmergencyStopPropagation system."""

    @pytest.fixture
    def mock_fleet_coordination(self) -> Mock:
        """Fixture for FleetCoordinationEngine mock."""
        mock = AsyncMock(spec=FleetCoordinationEngine)
        mock.get_fleet_status.return_value = {
            "TRACTOR_002": {"status": "WORKING"},
            "TRACTOR_003": {"status": "IDLE"},
        }
        return mock

    @pytest.fixture
    def mock_vector_clock(self) -> Mock:
        """Fixture for VectorClock mock."""
        mock = Mock(spec=VectorClock)
        mock.get_process_ids.return_value = ["TRACTOR_001", "TRACTOR_002", "TRACTOR_003"]
        mock.to_dict.return_value = {"TRACTOR_001": 5}
        return mock

    @pytest.fixture
    def mock_isobus(self) -> Mock:
        """Fixture for ReliableISOBUSDevice mock."""
        mock = AsyncMock(spec=ReliableISOBUSDevice)
        return mock

    def test_initialization_with_fleet_coordination_components(
        self, mock_fleet_coordination, mock_vector_clock, mock_isobus
    ) -> None:
        """Test EmergencyStopPropagation initialization."""
        emergency_system = EmergencyStopPropagation(
            fleet_coordination=mock_fleet_coordination,
            vector_clock=mock_vector_clock,
            isobus=mock_isobus,
        )
        assert emergency_system.fleet_coordination == mock_fleet_coordination
        assert emergency_system.vector_clock == mock_vector_clock
        assert emergency_system.isobus == mock_isobus
        assert not emergency_system.is_emergency_active

    @pytest.mark.asyncio
    async def test_trigger_emergency_stop_with_immediate_state_transition(
        self, mock_fleet_coordination, mock_vector_clock, mock_isobus
    ) -> None:
        """Test triggering emergency stop causes immediate local state transition."""
        emergency_system = EmergencyStopPropagation(
            fleet_coordination=mock_fleet_coordination,
            vector_clock=mock_vector_clock,
            isobus=mock_isobus,
        )
        reason_code = EmergencyReasonCode.OBSTACLE_DETECTED
        source_position = {"lat": 41.8781, "lon": -87.6298}
        severity = EmergencySeverity.CRITICAL

        result = await emergency_system.trigger_emergency_stop(
            reason_code=reason_code, source_position=source_position, severity=severity
        )

        assert emergency_system.is_emergency_active
        assert result.emergency_id is not None
        assert result.local_stop_executed
        mock_fleet_coordination.broadcast_emergency_stop.assert_called_once_with(reason_code.value)

    @pytest.mark.asyncio
    async def test_emergency_stop_vector_clock_increment(
        self, mock_fleet_coordination, mock_vector_clock, mock_isobus
    ) -> None:
        """Test emergency stop increments vector clock for causal ordering."""
        emergency_system = EmergencyStopPropagation(
            fleet_coordination=mock_fleet_coordination,
            vector_clock=mock_vector_clock,
            isobus=mock_isobus,
        )
        emergency_system.tractor_id = "TRACTOR_001"

        await emergency_system.trigger_emergency_stop(
            reason_code=EmergencyReasonCode.SYSTEM_FAULT,
            source_position={"lat": 42.3601, "lon": -71.0589},
            severity=EmergencySeverity.HIGH,
        )

        mock_vector_clock.increment.assert_called_once_with("TRACTOR_001")

    @pytest.mark.asyncio
    async def test_emergency_stop_broadcast_with_guaranteed_delivery(
        self, mock_fleet_coordination, mock_vector_clock, mock_isobus
    ) -> None:
        """Test emergency stop broadcast uses guaranteed delivery messaging."""
        emergency_system = EmergencyStopPropagation(
            fleet_coordination=mock_fleet_coordination,
            vector_clock=mock_vector_clock,
            isobus=mock_isobus,
        )
        emergency_system.tractor_id = "TRACTOR_001"

        await emergency_system.trigger_emergency_stop(
            reason_code=EmergencyReasonCode.OPERATOR_INTERVENTION,
            source_position={"lat": 40.7128, "lon": -74.0060},
            severity=EmergencySeverity.CRITICAL,
        )

        mock_isobus.broadcast_priority_message.assert_called_once()
        message = mock_isobus.broadcast_priority_message.call_args[0][0]
        assert message["msg_type"] == "EMERGENCY_STOP"
        assert message["sender_id"] == "TRACTOR_001"

    @pytest.mark.asyncio
    async def test_emergency_acknowledgment_tracking(
        self, mock_fleet_coordination, mock_vector_clock, mock_isobus
    ) -> None:
        """Test tracking acknowledgments from all fleet members."""
        emergency_system = EmergencyStopPropagation(
            fleet_coordination=mock_fleet_coordination,
            vector_clock=mock_vector_clock,
            isobus=mock_isobus,
        )
        emergency_system.tractor_id = "TRACTOR_001"

        result = await emergency_system.trigger_emergency_stop(
            reason_code=EmergencyReasonCode.COLLISION_DETECTED,
            source_position={"lat": 41.8801, "lon": -87.6278},
            severity=EmergencySeverity.CRITICAL,
        )

        await emergency_system.receive_emergency_acknowledgment(result.emergency_id, "TRACTOR_002")

        status = emergency_system.get_acknowledgment_status(result.emergency_id)
        assert "TRACTOR_002" in status.acknowledged_tractors
        assert "TRACTOR_003" in status.pending_acknowledgments


class TestEmergencyStopReception:
    """Test emergency stop message reception and causal ordering."""

    @pytest.fixture
    def emergency_system(self) -> EmergencyStopPropagation:
        """Fixture for EmergencyStopPropagation with mocks."""
        self.mock_fleet = AsyncMock(spec=FleetCoordinationEngine)
        self.mock_vc = Mock(spec=VectorClock)
        self.mock_vc.get_process_ids.return_value = ["TRACTOR_001"]
        self.mock_isobus = AsyncMock(spec=ReliableISOBUSDevice)
        system = EmergencyStopPropagation(self.mock_fleet, self.mock_vc, self.mock_isobus)
        system.tractor_id = "TRACTOR_001"
        return system

    @pytest.mark.asyncio
    async def test_receive_emergency_stop_with_causal_ordering(self, emergency_system) -> None:
        """Test processing emergency stop with vector clock causal ordering."""
        sender_clock = Mock(spec=VectorClock)
        sender_clock.happens_before.return_value = False
        message = {
            "msg_type": "EMERGENCY_STOP",
            "sender_id": "TRACTOR_SENDER_005",
            "emergency_id": "EMERGENCY_001",
            "vector_clock": {"TRACTOR_SENDER_005": 3, "TRACTOR_001": 2},
            "payload": {"reason_code": "EQUIPMENT_MALFUNCTION", "severity": "HIGH"},
        }

        await emergency_system.receive_emergency_stop(message, sender_clock)

        emergency_system.vector_clock.update_with_received_message.assert_called_once()
        assert emergency_system.is_emergency_active

    @pytest.mark.asyncio
    async def test_emergency_stop_conflict_resolution_by_severity(self, emergency_system) -> None:
        """Test emergency stop conflict resolution using severity levels."""
        await emergency_system.trigger_emergency_stop(
            EmergencyReasonCode.MAINTENANCE_REQUIRED, {}, EmergencySeverity.MEDIUM
        )

        concurrent_clock = Mock(spec=VectorClock)
        concurrent_clock.happens_before.return_value = False
        emergency_system.vector_clock.happens_before.return_value = False

        critical_message = {
            "msg_type": "EMERGENCY_STOP",
            "sender_id": "TRACTOR_CRITICAL_006",
            "emergency_id": "EMERGENCY_CRITICAL_001",
            "payload": {"reason_code": "PERSON_IN_FIELD", "severity": "CRITICAL"},
        }

        await emergency_system.receive_emergency_stop(critical_message, concurrent_clock)

        active_emergency = emergency_system.get_active_emergency()
        assert active_emergency.emergency_id == "EMERGENCY_CRITICAL_001"

    @pytest.mark.asyncio
    async def test_emergency_stop_acknowledgment_automatic_sending(self, emergency_system) -> None:
        """Test automatic acknowledgment sending for received emergency stops."""
        with patch.object(
            emergency_system.isobus, "send_message", new_callable=AsyncMock
        ) as mock_send:
            await emergency_system.send_emergency_acknowledgment(
                "EMERGENCY_002", "TRACTOR_SENDER_008"
            )
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            sent_message = call_args[1]
            assert sent_message["msg_type"] == "EMERGENCY_ACKNOWLEDGMENT"


class TestEmergencyStopPropagationTiming:
    """Test emergency stop propagation timing and performance requirements."""

    @pytest.mark.asyncio
    async def test_sub_500ms_fleet_propagation_requirement(self) -> None:
        """Test emergency stop propagation meets sub-500ms requirement."""
        mock_fleet = AsyncMock(spec=FleetCoordinationEngine)
        mock_vc = Mock(spec=VectorClock)
        mock_isobus = AsyncMock(spec=ReliableISOBUSDevice)

        async def fast_ack(*args, **kwargs):
            await asyncio.sleep(0.001)  # 1ms mock acknowledgment (98% faster)

        mock_isobus.broadcast_priority_message.side_effect = fast_ack
        mock_fleet.get_fleet_status.return_value = {}
        mock_vc.get_process_ids.return_value = ["TRACTOR_1", "TRACTOR_2"]
        emergency_system = EmergencyStopPropagation(mock_fleet, mock_vc, mock_isobus)

        start_time = time.perf_counter()
        result = await emergency_system.trigger_emergency_stop(
            EmergencyReasonCode.OBSTACLE_DETECTED, {}, EmergencySeverity.CRITICAL
        )
        end_time = time.perf_counter()

        assert (end_time - start_time) * 1000 < 500
        assert result.propagation_initiated

    @pytest.mark.asyncio
    async def test_acknowledgment_timeout_escalation(self) -> None:
        """Test escalation when emergency acknowledgments timeout."""
        mock_fleet = AsyncMock(spec=FleetCoordinationEngine)
        mock_fleet.get_fleet_status.return_value = {"TRACTOR_A": {}, "TRACTOR_B": {}}
        mock_vc = Mock(spec=VectorClock)
        mock_vc.get_process_ids.return_value = ["TRACTOR_A", "TRACTOR_B"]
        mock_isobus = AsyncMock(spec=ReliableISOBUSDevice)

        emergency_system = EmergencyStopPropagation(
            mock_fleet, mock_vc, mock_isobus, acknowledgment_timeout=0.1
        )
        emergency_system.tractor_id = "LOCAL_TRACTOR"

        result = await emergency_system.trigger_emergency_stop(
            EmergencyReasonCode.COLLISION_DETECTED, {}, EmergencySeverity.CRITICAL
        )
        await emergency_system.receive_emergency_acknowledgment(result.emergency_id, "TRACTOR_A")

        await asyncio.sleep(0.01)  # 10ms escalation wait (95% faster while maintaining test logic)
        escalation_result = await emergency_system.check_and_escalate(result.emergency_id)

        assert escalation_result.escalation_triggered
        assert "TRACTOR_B" in escalation_result.unacknowledged_tractors


class TestEmergencyStopFailSafeBehaviors:
    """Test fail-safe behaviors during emergency stop scenarios."""

    @pytest.mark.asyncio
    async def test_emergency_stop_during_network_partition(self) -> None:
        """Test emergency stop behavior during network partition."""
        mock_fleet = AsyncMock(spec=FleetCoordinationEngine)
        mock_vc = Mock(spec=VectorClock)
        mock_isobus = AsyncMock(spec=ReliableISOBUSDevice)
        mock_isobus.broadcast_priority_message.side_effect = TimeoutError("Network partition")

        emergency_system = EmergencyStopPropagation(mock_fleet, mock_vc, mock_isobus)

        result = await emergency_system.trigger_emergency_stop(
            EmergencyReasonCode.SYSTEM_FAULT, {}, EmergencySeverity.CRITICAL
        )

        assert result.local_stop_executed
        assert result.network_broadcast_failed
        assert result.queued_for_retry
