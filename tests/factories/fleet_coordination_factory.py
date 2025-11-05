"""
Real fleet coordination factory for agricultural testing.

This module provides real FleetCoordinationEngine instances integrated with
actual CAN communication, replacing mocks with functional agricultural systems.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from afs_fastapi.core.can_manager import create_can_manager
from afs_fastapi.equipment.network.isobus import ISOBUSDevice
from afs_fastapi.services.fleet import FleetCoordinationEngine

logger = logging.getLogger(__name__)


class TestISOBUSDevice(ISOBUSDevice):
    """ISOBUS device implementation for testing with real CAN communication.

    Integrates with our cross-platform CAN manager to provide actual
    ISOBUS messaging capabilities for fleet coordination testing.
    """

    def __init__(self, tractor_id: str, can_manager: Any | None = None) -> None:
        """Initialize test ISOBUS device with CAN integration.

        Parameters
        ----------
        tractor_id : str
            Unique identifier for this tractor
        can_manager : Any, optional
            Pre-configured CAN manager. If None, creates a new one.
        """
        self.tractor_id = tractor_id

        # Use provided CAN manager or create a new one
        if can_manager:
            self.can_manager = can_manager
        else:
            self.can_manager = create_can_manager(auto_connect=True)

        # ISOBUS address for this device (based on tractor ID)
        self.isobus_address = hash(tractor_id) % 255 + 1  # 1-255

        # Message tracking for testing
        self._sent_messages: list[dict[str, Any]] = []
        self._received_messages: list[dict[str, Any]] = []
        self._message_callbacks: list[callable] = []

        # Device state
        self._is_started = False
        self._logger = logging.getLogger(f"{__name__}.{tractor_id}")

    async def start(self) -> None:
        """Start ISOBUS communication."""
        if not self._is_started:
            # Start CAN message receiving
            self.can_manager.add_message_handler(self._handle_can_message)
            self.can_manager.start_receiving()

            self._is_started = True
            self._logger.info(
                f"ISOBUS device {self.tractor_id} started (address: {self.isobus_address})"
            )

    async def stop(self) -> None:
        """Stop ISOBUS communication."""
        if self._is_started:
            self.can_manager.stop_receiving()
            self._is_started = False
            self._logger.info(f"ISOBUS device {self.tractor_id} stopped")

    async def send_message(self, message: dict[str, Any]) -> bool:
        """Send ISOBUS message via CAN.

        Parameters
        ----------
        message : dict[str, Any]
            ISOBUS message data

        Returns
        -------
        bool
            True if message sent successfully
        """
        try:
            # Convert ISOBUS message to J1939 format
            pgn = message.get("pgn", 0xEF00)  # Default to transport protocol
            priority = message.get("priority", 6)
            data = message.get("data", [])

            success = self.can_manager.send_j1939_message(
                pgn=pgn,
                source_address=self.isobus_address,
                destination_address=message.get("destination_address", 255),
                priority=priority,
                data=data,
            )

            if success:
                self._sent_messages.append(message)
                self._logger.debug(f"ISOBUS message sent: PGN={pgn:04X}")

            return success

        except Exception as e:
            self._logger.error(f"Failed to send ISOBUS message: {e}")
            return False

    async def broadcast_message(self, message: dict[str, Any]) -> bool:
        """Broadcast ISOBUS message to all fleet members.

        Parameters
        ----------
        message : dict[str, Any]
            ISOBUS message to broadcast

        Returns
        -------
        bool
            True if message broadcast successfully
        """
        message["destination_address"] = 255  # Global broadcast
        return await self.send_message(message)

    async def broadcast_priority_message(self, message: dict[str, Any]) -> bool:
        """Broadcast high-priority ISOBUS message.

        Parameters
        ----------
        message : dict[str, Any]
            High-priority ISOBUS message

        Returns
        -------
        bool
            True if message sent successfully
        """
        message["priority"] = 0  # Highest priority
        return await self.broadcast_message(message)

    async def send_message(self, message: Any) -> bool:
        """Send ISOBUS message (interface compatibility)."""
        if isinstance(message, dict):
            return await self.send_message(message)
        else:
            # Convert message object to dict format
            msg_dict = {
                "pgn": getattr(message, "pgn", 0xEF00),
                "data": getattr(message, "data", []),
                "priority": getattr(message, "priority", 6),
                "destination_address": getattr(message, "destination_address", 255),
            }
            return await self.send_message(msg_dict)

    def receive_message(self) -> dict[str, Any] | None:
        """Receive ISOBUS message (synchronous interface)."""
        if self._received_messages:
            return self._received_messages.pop(0)
        return None

    def get_device_name(self) -> str:
        """Get standardized device name."""
        return f"TRACTOR_{self.tractor_id}"

    def _handle_can_message(self, decoded_message: dict[str, Any]) -> None:
        """Handle received CAN message and convert to ISOBUS format.

        Parameters
        ----------
        decoded_message : dict[str, Any]
            Decoded CAN message from CAN manager
        """
        # Convert J1939 message to ISOBUS format
        isobus_message = {
            "pgn": decoded_message["pgn"],
            "source_address": decoded_message["source_address"],
            "destination_address": decoded_message["destination_address"],
            "priority": decoded_message["priority"],
            "data": decoded_message["data"],
            "timestamp": decoded_message["timestamp"],
        }

        self._received_messages.append(isobus_message)

        # Notify callbacks
        for callback in self._message_callbacks:
            try:
                callback(isobus_message)
            except Exception as e:
                self._logger.error(f"Message callback error: {e}")

    def add_message_callback(self, callback: callable) -> None:
        """Add callback for received messages."""
        self._message_callbacks.append(callback)

    def get_sent_messages(self) -> list[dict[str, Any]]:
        """Get list of sent messages for test verification."""
        return self._sent_messages.copy()

    def get_received_messages(self) -> list[dict[str, Any]]:
        """Get list of received messages for test verification."""
        return self._received_messages.copy()

    def clear_message_history(self) -> None:
        """Clear message history for clean test state."""
        self._sent_messages.clear()
        self._received_messages.clear()


def create_test_fleet_coordination_engine(
    tractor_id: str, can_manager: Any | None = None, auto_start: bool = False
) -> FleetCoordinationEngine:
    """Create a real FleetCoordinationEngine with actual CAN communication.

    Parameters
    ----------
    tractor_id : str
        Unique identifier for this tractor in the fleet
    can_manager : Any, optional
        Pre-configured CAN manager. If None, creates a new one.
    auto_start : bool, default False
        Whether to automatically start the engine

    Returns
    -------
    FleetCoordinationEngine
        Real fleet coordination engine with functional ISOBUS communication

    Examples
    --------
    >>> engine = create_test_fleet_coordination_engine("TRACTOR_001")
    >>> engine.tractor_id
    'TRACTOR_001'
    >>> isinstance(engine.isobus_interface, TestISOBUSDevice)
    True
    """
    # Create ISOBUS device with CAN integration
    isobus_device = TestISOBUSDevice(tractor_id, can_manager)

    # Create fleet coordination engine
    engine = FleetCoordinationEngine(tractor_id, isobus_device)

    if auto_start:
        # Note: In real tests, use await engine.start()
        asyncio.create_task(engine.start())

    return engine


def create_test_fleet(
    fleet_size: int = 3, base_tractor_id: str = "TRACTOR", shared_can_manager: bool = False
) -> list[FleetCoordinationEngine]:
    """Create a fleet of tractors for multi-tractor testing.

    Parameters
    ----------
    fleet_size : int, default 3
        Number of tractors to create
    base_tractor_id : str, default "TRACTOR"
        Base name for tractor IDs
    shared_can_manager : bool, default False
        Whether to use a shared CAN manager for all tractors

    Returns
    -------
    list[FleetCoordinationEngine]
        List of fleet coordination engines

    Examples
    --------
    >>> fleet = create_test_fleet(fleet_size=2)
    >>> len(fleet)
    2
    >>> fleet[0].tractor_id
    'TRACTOR_001'
    >>> fleet[1].tractor_id
    'TRACTOR_002'
    """
    fleet = []
    can_manager = None

    if shared_can_manager:
        can_manager = create_can_manager(auto_connect=True)

    for i in range(fleet_size):
        tractor_id = f"{base_tractor_id}_{i+1:03d}"

        if not shared_can_manager:
            can_manager = create_can_manager(auto_connect=True)

        engine = create_test_fleet_coordination_engine(
            tractor_id=tractor_id, can_manager=can_manager
        )
        fleet.append(engine)

    return fleet


async def start_fleet(fleet: list[FleetCoordinationEngine]) -> None:
    """Start all engines in a fleet.

    Parameters
    ----------
    fleet : list[FleetCoordinationEngine]
        List of fleet coordination engines to start
    """
    start_tasks = [engine.start() for engine in fleet]
    await asyncio.gather(*start_tasks)


async def stop_fleet(fleet: list[FleetCoordinationEngine]) -> None:
    """Stop all engines in a fleet.

    Parameters
    ----------
    fleet : list[FleetCoordinationEngine]
        List of fleet coordination engines to stop
    """
    stop_tasks = [engine.stop() for engine in fleet]
    await asyncio.gather(*stop_tasks)
