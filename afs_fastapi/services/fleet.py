"""FleetCoordinationEngine - Agricultural Multi-Tractor Orchestration System.

This module implements the FleetCoordinationEngine, which orchestrates
multi-tractor fleet coordination using CRDT-based field allocation
and vector clock synchronization for autonomous agricultural operations.

The engine provides the central coordination layer for:
- Multi-tractor task orchestration and field section allocation
- Emergency stop protocols for safety-critical situations
- Fleet-wide state synchronization using vector clocks
- ISOBUS-compatible message routing for agricultural equipment

Agricultural Context
--------------------
The FleetCoordinationEngine enables coordinated autonomous agricultural
operations across multiple tractors working the same field. It ensures:
- No conflicts between tractors working adjacent field sections
- Emergency coordination for safety-critical situations
- Efficient work distribution across the fleet
- Compliance with ISO 11783 agricultural communication standards

Implementation follows TDD GREEN phase - minimal implementation
to satisfy test requirements with agricultural domain focus.
"""

from __future__ import annotations

import asyncio
import copy
import logging
from collections.abc import Callable
from enum import Enum
from typing import Any

from afs_fastapi.equipment.reliable_isobus import ReliableISOBUSDevice
from afs_fastapi.services.field_allocation import FieldAllocationCRDT
from afs_fastapi.services.synchronization import VectorClock

logger = logging.getLogger(__name__)


class TractorState(Enum):
    """Tractor state machine states for fleet coordination."""

    DISCONNECTED = "DISCONNECTED"
    IDLE = "IDLE"
    SYNCHRONIZING = "SYNCHRONIZING"
    WORKING = "WORKING"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class FleetCoordinationEngine:
    """Orchestrates fleet coordination using distributed agricultural protocols.

    The FleetCoordinationEngine manages multi-tractor coordination through
    a combination of CRDT-based field allocation, vector clock synchronization,
    and ISOBUS message routing. Implements the fleet coordination protocol
    specified in FLEET_COORDINATION_PROTOCOL.md.

    Agricultural Context
    --------------------
    This engine serves as the central coordination point for autonomous
    agricultural equipment operating in the same field. It ensures:
    - Conflict-free section allocation across multiple tractors
    - Emergency coordination for safety-critical situations
    - Consistent fleet state through distributed synchronization
    - Compliance with agricultural communication standards

    Attributes
    ----------
    tractor_id : str
        Unique identifier for this tractor in the fleet
    isobus_interface : ReliableISOBUSDevice
        ISOBUS communication interface for fleet messaging
    """

    def __init__(self, tractor_id: str, isobus_interface: ReliableISOBUSDevice) -> None:
        """Initialize FleetCoordinationEngine for agricultural operations.

        Parameters
        ----------
        tractor_id : str
            Unique identifier for this tractor (e.g., "TRACTOR_FIELD_001")
        isobus_interface : ReliableISOBUSDevice
            Reliable ISOBUS interface for fleet communication

        Agricultural Context
        --------------------
        Each tractor in the fleet must have a unique identifier and
        reliable communication interface to participate in coordinated
        field operations. The engine initializes in DISCONNECTED state
        until explicitly joined to the fleet network.
        """
        self.tractor_id = tractor_id
        self.isobus_interface = isobus_interface

        # Initialize state machine
        self._current_state = TractorState.DISCONNECTED

        # Initialize field allocation CRDT with this tractor
        self._field_allocation = FieldAllocationCRDT(
            field_id="current_field", tractor_ids=[tractor_id]
        )

        # Initialize vector clock for causal ordering
        self._vector_clock = VectorClock([tractor_id])

        # Fleet status tracking
        self._fleet_status: dict[str, dict[str, Any]] = {}

        # Current operational data
        self._current_position = {"lat": 0.0, "lon": 0.0}
        self._current_speed = 0.0
        self._health_metric = 1.0

        # Event callbacks
        self._state_change_callbacks: list[Callable[[str], None]] = []
        self._emergency_callbacks: list[Callable[[dict[str, Any]], None]] = []

        # Background tasks
        self._background_tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """Start the engine and join the fleet network.

        Initializes ISOBUS interface, transitions to IDLE state, and begins
        fleet coordination activities including heartbeat broadcasting.

        Agricultural Context
        --------------------
        When a tractor starts field operations, it joins the fleet
        coordination network to enable collaborative agricultural work.
        """
        # Start ISOBUS interface
        await self.isobus_interface.start()

        # Transition to IDLE state
        self._transition_state(TractorState.IDLE)

        # Start background coordination tasks
        self._start_background_tasks()

    async def stop(self) -> None:
        """Stop the engine and gracefully leave the fleet.

        Shuts down ISOBUS interface, cancels background tasks, and
        transitions to DISCONNECTED state.

        Agricultural Context
        --------------------
        When tractor operations are complete or maintenance is required,
        graceful departure from fleet ensures proper handoff of any
        claimed field sections.
        """
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()

        # Stop ISOBUS interface
        await self.isobus_interface.stop()

        # Transition to DISCONNECTED state
        self._transition_state(TractorState.DISCONNECTED)

    async def claim_section(self, section_id: str) -> bool:
        """Attempt to claim a field section for work assignment.

        Broadcasts TASK_CLAIM message and updates local CRDT state.

        Parameters
        ----------
        section_id : str
            Field section identifier to claim (e.g., "FIELD_A_SECTION_12")

        Returns
        -------
        bool
            True if claim is successful locally

        Agricultural Context
        --------------------
        When a tractor identifies a field section requiring work
        (cultivation, planting, harvesting), it claims that section
        to prevent conflicts with other tractors.
        """
        # Increment vector clock for local section claim event
        if self.tractor_id in self._vector_clock.get_process_ids():
            self._vector_clock.increment(self.tractor_id)

        # Update local CRDT
        self._field_allocation.claim(section_id, self.tractor_id)

        # Broadcast claim message to fleet
        claim_message = {
            "msg_type": "TASK_CLAIM",
            "sender_id": self.tractor_id,
            "vector_clock": self._vector_clock.to_dict(),
            "payload": {"section_id": section_id, "action": "claim"},
        }
        await self.isobus_interface.broadcast_message(claim_message)

        # Transition to WORKING state if claim is successful
        if self._field_allocation.owner_of(section_id) == self.tractor_id:
            self._transition_state(TractorState.WORKING)
            return True

        return False

    async def release_section(self, section_id: str) -> None:
        """Release a completed field section.

        Broadcasts TASK_CLAIM message with 'release' action and updates
        local CRDT state.

        Parameters
        ----------
        section_id : str
            Field section identifier to release

        Agricultural Context
        --------------------
        After completing agricultural operations on a field section,
        the tractor releases that section to make it available for
        subsequent operations by other tractors.
        """
        # Increment vector clock for local section release event
        if self.tractor_id in self._vector_clock.get_process_ids():
            self._vector_clock.increment(self.tractor_id)

        # Update local CRDT
        self._field_allocation.release(section_id, self.tractor_id)

        # Broadcast release message to fleet
        release_message = {
            "msg_type": "TASK_CLAIM",
            "sender_id": self.tractor_id,
            "vector_clock": self._vector_clock.to_dict(),
            "payload": {"section_id": section_id, "action": "release"},
        }
        await self.isobus_interface.broadcast_message(release_message)

        # Transition back to IDLE state
        self._transition_state(TractorState.IDLE)

    async def broadcast_emergency_stop(self, reason_code: str) -> None:
        """Broadcast fleet-wide emergency stop command.

        Sends highest priority emergency message and transitions to
        EMERGENCY_STOP state immediately.

        Parameters
        ----------
        reason_code : str
            Emergency reason code (e.g., "OBSTACLE_DETECTED", "SYSTEM_FAULT")

        Agricultural Context
        --------------------
        When safety hazards are detected, immediate fleet-wide emergency
        stop prevents accidents and equipment damage. Uses guaranteed
        delivery for safety-critical messaging.
        """
        # Transition to emergency state immediately
        self._transition_state(TractorState.EMERGENCY_STOP)

        # Broadcast emergency message with highest priority
        emergency_message = {
            "msg_type": "EMERGENCY_STOP",
            "sender_id": self.tractor_id,
            "vector_clock": self._vector_clock.to_dict(),
            "payload": {
                "reason_code": reason_code,
                "source_position": copy.deepcopy(self._current_position),
            },
        }
        await self.isobus_interface.broadcast_priority_message(emergency_message)

    def get_current_state(self) -> str:
        """Get current tractor state from state machine.

        Returns
        -------
        str
            Current state ("DISCONNECTED", "IDLE", "WORKING", etc.)
        """
        return self._current_state.value

    def get_field_allocation_state(self) -> FieldAllocationCRDT:
        """Get current merged view of field allocation CRDT.

        Returns
        -------
        FieldAllocationCRDT
            Current field allocation state with all known section assignments

        Agricultural Context
        --------------------
        Provides current view of which field sections are allocated
        to which tractors across the fleet. Essential for coordination
        and conflict prevention.
        """
        return self._field_allocation

    def get_fleet_status(self) -> dict[str, dict[str, Any]]:
        """Get last known status of all tractors in fleet.

        Returns
        -------
        dict
            Fleet status mapping tractor IDs to status information

        Agricultural Context
        --------------------
        Provides fleet management view of all tractor positions,
        operational status, and health metrics for coordination
        and monitoring purposes.
        """
        return copy.deepcopy(self._fleet_status)

    def merge_field_allocation_state(self, other_crdt: FieldAllocationCRDT) -> None:
        """Merge another CRDT replica into local state.

        Parameters
        ----------
        other_crdt : FieldAllocationCRDT
            Another field allocation CRDT replica to merge

        Agricultural Context
        --------------------
        When tractors synchronize after network partitions or
        when joining ongoing operations, CRDT merge ensures
        consistent field allocation state across the fleet.
        """
        self._field_allocation.merge(other_crdt)

    def on_emergency(self, callback: Callable[[dict[str, Any]], Any]) -> None:
        """Register callback for emergency stop events.

        Parameters
        ----------
        callback : callable
            Function to call when emergency stop is received
        """
        self._emergency_callbacks.append(callback)

    def on_state_change(self, callback: Callable[[str], None]) -> None:
        """Register callback for state machine transitions.

        Parameters
        ----------
        callback : callable
            Function to call when state changes
        """
        self._state_change_callbacks.append(callback)

    async def _handle_received_message(self, message: dict[str, Any]) -> None:
        """Handle received fleet coordination messages.

        Parameters
        ----------
        message : dict
            Received message from another tractor

        Agricultural Context
        --------------------
        Processes incoming fleet coordination messages including
        heartbeats, task claims, emergency stops, and state synchronization.
        """
        msg_type = message.get("msg_type")

        if msg_type == "EMERGENCY_STOP":
            # Handle emergency stop - highest priority
            self._transition_state(TractorState.EMERGENCY_STOP)
            for callback in self._emergency_callbacks:
                try:
                    # Handle both sync and async callbacks
                    result = callback(message["payload"])
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Error in emergency callback: {e}")

        elif msg_type == "STATE_SYNC_RESPONSE":
            # Handle state synchronization response
            crdt_data = message["payload"]["crdt_payload"]
            other_crdt = FieldAllocationCRDT.deserialize(crdt_data)
            self.merge_field_allocation_state(other_crdt)

        elif msg_type == "HEARTBEAT":
            # Update fleet status
            sender_id = message["sender_id"]
            self._fleet_status[sender_id] = message["payload"]

    async def _request_state_sync(self) -> None:
        """Request state synchronization from fleet.

        Broadcasts STATE_SYNC_REQUEST to obtain current field allocation
        state from other tractors in the fleet.
        """
        sync_request = {
            "msg_type": "STATE_SYNC_REQUEST",
            "sender_id": self.tractor_id,
            "vector_clock": self._vector_clock.to_dict(),
            "payload": {},
        }
        await self.isobus_interface.broadcast_message(sync_request)

    async def _broadcast_heartbeat(self) -> None:
        """Broadcast heartbeat message with current status.

        Agricultural Context
        --------------------
        Regular heartbeats maintain fleet awareness and enable
        coordinated decision-making across autonomous tractors.
        """
        heartbeat_message = {
            "msg_type": "HEARTBEAT",
            "sender_id": self.tractor_id,
            "vector_clock": self._vector_clock.to_dict(),
            "payload": {
                "status": self._current_state.value,
                "position": copy.deepcopy(self._current_position),
                "speed": self._current_speed,
                "health_metric": self._health_metric,
            },
        }
        await self.isobus_interface.broadcast_message(heartbeat_message)

    def _transition_state(self, new_state: TractorState) -> None:
        """Transition to new state and notify callbacks.

        Parameters
        ----------
        new_state : TractorState
            New state to transition to
        """
        old_state = self._current_state
        self._current_state = new_state

        # Notify state change callbacks
        for callback in self._state_change_callbacks:
            callback(new_state.value)

        logger.info(
            f"Tractor {self.tractor_id} state transition: {old_state.value} -> {new_state.value}"
        )

    def _start_background_tasks(self) -> None:
        """Start background coordination tasks.

        Starts periodic heartbeat broadcasting and message handling
        for ongoing fleet coordination.
        """
        # Note: In real implementation, would start actual background tasks
        # For GREEN phase, minimal implementation focused on test satisfaction
        pass
