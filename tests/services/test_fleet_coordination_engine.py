"""Tests for FleetCoordinationEngine - TDD RED Phase Implementation.

This module implements comprehensive unit tests for the FleetCoordinationEngine,
which orchestrates multi-tractor fleet coordination using CRDT-based field
allocation and vector clock synchronization.

Agricultural Context
--------------------
The FleetCoordinationEngine is the central orchestration component for
autonomous agricultural fleet operations. It manages:
- Multi-tractor task coordination and field section allocation
- Emergency stop protocols for safety-critical situations
- Fleet-wide state synchronization using vector clocks
- ISOBUS-compatible message routing for agricultural equipment

Test Strategy
-------------
Tests follow TDD methodology with agricultural domain scenarios:
1. RED Phase: Failing tests defining expected fleet coordination behavior
2. GREEN Phase: Minimal implementation to satisfy agricultural requirements
3. REFACTOR Phase: Enhanced implementation with enterprise-grade reliability

These tests ensure safety-critical agricultural operations meet ISO 11783
compliance and distributed systems reliability standards.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from afs_fastapi.services.fleet import FleetCoordinationEngine


class TestFleetCoordinationEngineCore:
    """Test core functionality of FleetCoordinationEngine.

    Tests the fundamental lifecycle, state management, and orchestration
    capabilities required for multi-tractor field coordination.
    """

    def test_initialization_with_tractor_id_and_isobus_interface(self) -> None:
        """Test FleetCoordinationEngine initialization with required parameters.

        Agricultural Context:
        Each tractor in the fleet must be uniquely identifiable and have
        a reliable ISOBUS interface for communication with other equipment.
        The engine must initialize with proper default state.
        """
        # Arrange
        tractor_id = "TRACTOR_FIELD_001"
        mock_isobus = Mock()

        # Act
        engine = FleetCoordinationEngine(tractor_id, mock_isobus)

        # Assert
        assert engine.tractor_id == tractor_id
        assert engine.isobus_interface == mock_isobus
        assert engine.get_current_state() == "DISCONNECTED"

    @pytest.mark.asyncio
    async def test_fleet_joining_lifecycle(self) -> None:
        """Test complete fleet joining lifecycle from DISCONNECTED to IDLE.

        Agricultural Context:
        When a tractor starts field operations, it must join the fleet
        coordination network, transition to IDLE state, and begin
        broadcasting heartbeat messages for fleet awareness.
        """
        # Arrange
        tractor_id = "TRACTOR_HARVEST_002"
        mock_isobus = AsyncMock()
        engine = FleetCoordinationEngine(tractor_id, mock_isobus)

        # Act
        await engine.start()

        # Assert
        assert engine.get_current_state() == "IDLE"
        # Verify ISOBUS interface was properly configured for fleet communication
        mock_isobus.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_graceful_fleet_departure(self) -> None:
        """Test graceful departure from fleet coordination network.

        Agricultural Context:
        When a tractor completes field operations or requires maintenance,
        it must gracefully leave the fleet network, releasing any claimed
        field sections and notifying other tractors of its departure.
        """
        # Arrange
        tractor_id = "TRACTOR_CULTIVATION_003"
        mock_isobus = AsyncMock()
        engine = FleetCoordinationEngine(tractor_id, mock_isobus)

        await engine.start()  # Join fleet first

        # Act
        await engine.stop()

        # Assert
        assert engine.get_current_state() == "DISCONNECTED"
        mock_isobus.stop.assert_called_once()


class TestFleetTaskOrchestration:
    """Test multi-tractor task orchestration and field section management.

    Tests the critical field allocation functionality that prevents conflicts
    between tractors working in the same field area.
    """

    @pytest.mark.asyncio
    async def test_successful_field_section_claim(self) -> None:
        """Test successful claiming of field section for work assignment.

        Agricultural Context:
        When a tractor identifies a field section that needs cultivation,
        planting, or harvesting, it must claim that section to prevent
        conflicts with other tractors. The claim must be broadcast to
        the fleet via ISOBUS messaging.
        """
        # Arrange
        tractor_id = "TRACTOR_PLANTING_004"
        section_id = "FIELD_A_SECTION_12"
        mock_isobus = AsyncMock()
        engine = FleetCoordinationEngine(tractor_id, mock_isobus)

        await engine.start()

        # Act
        claim_successful = await engine.claim_section(section_id)

        # Assert
        assert claim_successful is True

        # Verify CRDT state was updated
        field_allocation = engine.get_field_allocation_state()
        assert field_allocation.owner_of(section_id) == tractor_id

        # Verify TASK_CLAIM message was broadcast
        mock_isobus.broadcast_message.assert_called_once()
        broadcast_args = mock_isobus.broadcast_message.call_args
        message = broadcast_args[0][0]
        assert message["msg_type"] == "TASK_CLAIM"
        assert message["payload"]["section_id"] == section_id
        assert message["payload"]["action"] == "claim"

    @pytest.mark.asyncio
    async def test_field_section_release_after_completion(self) -> None:
        """Test releasing field section after agricultural task completion.

        Agricultural Context:
        After completing planting, cultivation, or harvesting operations
        on a field section, the tractor must release that section to
        make it available for subsequent operations by other tractors.
        """
        # Arrange
        tractor_id = "TRACTOR_HARVESTING_005"
        section_id = "FIELD_B_SECTION_08"
        mock_isobus = AsyncMock()
        engine = FleetCoordinationEngine(tractor_id, mock_isobus)

        await engine.start()
        await engine.claim_section(section_id)  # Claim first
        mock_isobus.reset_mock()  # Reset to check release message

        # Act
        await engine.release_section(section_id)

        # Assert
        field_allocation = engine.get_field_allocation_state()
        assert field_allocation.owner_of(section_id) is None

        # Verify TASK_CLAIM release message was broadcast
        mock_isobus.broadcast_message.assert_called_once()
        broadcast_args = mock_isobus.broadcast_message.call_args
        message = broadcast_args[0][0]
        assert message["msg_type"] == "TASK_CLAIM"
        assert message["payload"]["section_id"] == section_id
        assert message["payload"]["action"] == "release"

    @pytest.mark.asyncio
    async def test_conflict_resolution_for_simultaneous_claims(self) -> None:
        """Test CRDT conflict resolution for simultaneous section claims.

        Agricultural Context:
        When multiple tractors attempt to claim the same field section
        simultaneously (due to network partitions or timing), the CRDT
        conflict resolution must deterministically assign the section
        to ensure consistent fleet-wide state.
        """
        # Arrange
        tractor_a_id = "TRACTOR_ALPHA_001"
        tractor_b_id = "TRACTOR_BETA_002"
        section_id = "CONTESTED_SECTION_15"

        mock_isobus_a = AsyncMock()
        mock_isobus_b = AsyncMock()

        engine_a = FleetCoordinationEngine(tractor_a_id, mock_isobus_a)
        engine_b = FleetCoordinationEngine(tractor_b_id, mock_isobus_b)

        await engine_a.start()
        await engine_b.start()

        # Act - Simulate simultaneous claims
        await engine_a.claim_section(section_id)
        await engine_b.claim_section(section_id)

        # Simulate CRDT merge to resolve conflict
        engine_a.merge_field_allocation_state(engine_b.get_field_allocation_state())
        engine_b.merge_field_allocation_state(engine_a.get_field_allocation_state())

        # Assert - Both engines should converge to same state
        final_owner_a = engine_a.get_field_allocation_state().owner_of(section_id)
        final_owner_b = engine_b.get_field_allocation_state().owner_of(section_id)

        assert final_owner_a == final_owner_b
        assert final_owner_a in [tractor_a_id, tractor_b_id]


class TestFleetEmergencyCoordination:
    """Test emergency coordination and safety protocols.

    Tests critical safety functionality for emergency stops and
    collision avoidance in multi-tractor operations.
    """

    @pytest.mark.asyncio
    async def test_emergency_stop_broadcast(self) -> None:
        """Test broadcasting emergency stop to entire fleet.

        Agricultural Context:
        When a tractor detects a safety hazard (obstacle, equipment failure,
        operator intervention), it must immediately broadcast an emergency
        stop command to all tractors in the fleet using highest priority
        guaranteed delivery messaging.
        """
        # Arrange
        tractor_id = "TRACTOR_SAFETY_006"
        reason_code = "OBSTACLE_DETECTED"
        mock_isobus = AsyncMock()
        engine = FleetCoordinationEngine(tractor_id, mock_isobus)

        await engine.start()

        # Act
        await engine.broadcast_emergency_stop(reason_code)

        # Assert
        assert engine.get_current_state() == "EMERGENCY_STOP"

        # Verify guaranteed delivery emergency message was sent
        mock_isobus.broadcast_priority_message.assert_called_once()
        broadcast_args = mock_isobus.broadcast_priority_message.call_args
        message = broadcast_args[0][0]
        assert message["msg_type"] == "EMERGENCY_STOP"
        assert message["payload"]["reason_code"] == reason_code

    @pytest.mark.asyncio
    async def test_emergency_stop_reception_and_state_transition(self) -> None:
        """Test proper handling of received emergency stop messages.

        Agricultural Context:
        When a tractor receives an emergency stop message from another
        tractor, it must immediately halt all operations, transition to
        EMERGENCY_STOP state, and execute safety protocols to prevent
        accidents or equipment damage.
        """
        # Arrange
        tractor_id = "TRACTOR_RECEIVING_007"
        mock_isobus = AsyncMock()
        engine = FleetCoordinationEngine(tractor_id, mock_isobus)

        await engine.start()

        # Simulate tractor working in field
        await engine.claim_section("ACTIVE_SECTION_20")
        assert engine.get_current_state() == "WORKING"

        # Arrange emergency callback
        emergency_callback = AsyncMock()
        engine.on_emergency(emergency_callback)

        # Act - Simulate receiving emergency stop message
        emergency_message = {
            "msg_type": "EMERGENCY_STOP",
            "sender_id": "TRACTOR_SENDER_008",
            "payload": {
                "reason_code": "SYSTEM_FAULT",
                "source_position": {"lat": 42.3601, "lon": -71.0589},
            },
        }
        await engine._handle_received_message(emergency_message)

        # Assert
        assert engine.get_current_state() == "EMERGENCY_STOP"
        emergency_callback.assert_called_once_with(emergency_message["payload"])


class TestFleetStatusSynchronization:
    """Test fleet-wide status synchronization and state management.

    Tests the distributed coordination mechanisms that ensure all
    tractors maintain consistent views of fleet status and field allocation.
    """

    @pytest.mark.asyncio
    async def test_heartbeat_broadcasting(self) -> None:
        """Test periodic heartbeat broadcasting for fleet awareness.

        Agricultural Context:
        Tractors must periodically broadcast heartbeat messages containing
        their status, position, speed, and health metrics to maintain
        fleet awareness and enable coordinated operations.
        """
        # Arrange
        tractor_id = "TRACTOR_HEARTBEAT_009"
        mock_isobus = AsyncMock()
        engine = FleetCoordinationEngine(tractor_id, mock_isobus)

        # Mock position and health data
        engine._current_position = {"lat": 40.7128, "lon": -74.0060}
        engine._current_speed = 5.2
        engine._health_metric = 0.95

        await engine.start()

        # Act - Trigger heartbeat broadcast
        await engine._broadcast_heartbeat()

        # Assert
        mock_isobus.broadcast_message.assert_called()
        broadcast_args = mock_isobus.broadcast_message.call_args
        message = broadcast_args[0][0]

        assert message["msg_type"] == "HEARTBEAT"
        assert message["payload"]["status"] == "IDLE"
        assert message["payload"]["position"] == {"lat": 40.7128, "lon": -74.0060}
        assert message["payload"]["speed"] == 5.2
        assert message["payload"]["health_metric"] == 0.95

    def test_fleet_status_query(self) -> None:
        """Test querying current status of all tractors in fleet.

        Agricultural Context:
        Fleet management systems need to query the current status of
        all tractors to make coordination decisions, monitor progress,
        and identify potential issues requiring intervention.
        """
        # Arrange
        tractor_id = "TRACTOR_COORDINATOR_010"
        mock_isobus = Mock()
        engine = FleetCoordinationEngine(tractor_id, mock_isobus)

        # Simulate received fleet status data
        engine._fleet_status = {
            "TRACTOR_ALPHA_001": {
                "status": "WORKING",
                "position": {"lat": 41.8781, "lon": -87.6298},
                "health_metric": 0.92,
            },
            "TRACTOR_BETA_002": {
                "status": "IDLE",
                "position": {"lat": 41.8801, "lon": -87.6278},
                "health_metric": 0.88,
            },
        }

        # Act
        fleet_status = engine.get_fleet_status()

        # Assert
        assert len(fleet_status) == 2
        assert "TRACTOR_ALPHA_001" in fleet_status
        assert fleet_status["TRACTOR_ALPHA_001"]["status"] == "WORKING"
        assert "TRACTOR_BETA_002" in fleet_status
        assert fleet_status["TRACTOR_BETA_002"]["status"] == "IDLE"

    @pytest.mark.asyncio
    async def test_state_synchronization_request_response(self) -> None:
        """Test state synchronization request/response cycle.

        Agricultural Context:
        When a tractor joins the fleet or recovers from network partition,
        it must request current field allocation state from other tractors
        to synchronize its local CRDT and maintain consistent coordination.
        """
        # Arrange
        joining_tractor_id = "TRACTOR_JOINING_011"
        responding_tractor_id = "TRACTOR_ESTABLISHED_012"

        mock_isobus_joining = AsyncMock()
        mock_isobus_responding = AsyncMock()

        joining_engine = FleetCoordinationEngine(joining_tractor_id, mock_isobus_joining)
        responding_engine = FleetCoordinationEngine(responding_tractor_id, mock_isobus_responding)

        await responding_engine.start()
        await responding_engine.claim_section("ESTABLISHED_SECTION_25")

        # Act - Joining tractor requests state sync
        await joining_engine.start()
        await joining_engine._request_state_sync()

        # Simulate state sync response from established tractor
        sync_message = {
            "msg_type": "STATE_SYNC_RESPONSE",
            "sender_id": responding_tractor_id,
            "payload": {"crdt_payload": responding_engine.get_field_allocation_state().serialize()},
        }
        await joining_engine._handle_received_message(sync_message)

        # Assert - Joining tractor should have synchronized state
        joining_field_allocation = joining_engine.get_field_allocation_state()
        assert joining_field_allocation.owner_of("ESTABLISHED_SECTION_25") == responding_tractor_id
