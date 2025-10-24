"""
Physical CAN interface integration layer for real-world tractor connectivity.

This module provides a production-grade abstraction layer for multiple CAN
interfaces, supporting ISOBUS J1939 protocol compliance and robust connection
management for agricultural equipment operations.

Implementation follows Test-First Development (TDD) GREEN phase.
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Protocol

import can

from afs_fastapi.equipment.can_error_handling import (
    CANErrorHandler,
    CANErrorType,
    CANFrameValidator,
    ISOBUSErrorLogger,
)

# Configure logging for physical CAN interface
logger = logging.getLogger(__name__)


class CANInterfaceType(Enum):
    """Supported physical CAN interface types."""

    SOCKETCAN = "socketcan"  # Linux SocketCAN
    PCAN = "pcan"  # PEAK-System PCAN
    KVASER = "kvaser"  # Kvaser interfaces
    IXXAT = "ixxat"  # IXXAT interfaces
    VIRTUAL = "virtual"  # Virtual CAN for testing
    USB2CAN = "usb2can"  # USB to CAN adapters


class InterfaceState(Enum):
    """Physical interface connection states."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECOVERING = "recovering"
    MAINTENANCE = "maintenance"


class BusSpeed(Enum):
    """Standard CAN bus speeds for agricultural equipment."""

    SPEED_125K = 125000  # 125 kbit/s
    SPEED_250K = 250000  # 250 kbit/s - ISOBUS standard
    SPEED_500K = 500000  # 500 kbit/s
    SPEED_1M = 1000000  # 1 Mbit/s


@dataclass
class InterfaceConfiguration:
    """Configuration for physical CAN interface."""

    interface_type: CANInterfaceType
    channel: str
    bitrate: BusSpeed
    fd_enabled: bool = False  # CAN FD support
    data_bitrate: int = 2000000  # CAN FD data phase bitrate
    auto_reset: bool = True
    listen_only: bool = False
    extended_frames: bool = True  # Support 29-bit identifiers
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class InterfaceStatus:
    """Status information for physical CAN interface."""

    interface_id: str
    state: InterfaceState
    last_heartbeat: datetime
    messages_sent: int = 0
    messages_received: int = 0
    errors_total: int = 0
    connection_uptime: timedelta = field(default_factory=lambda: timedelta())
    bus_load_percentage: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class J1939Address:
    """J1939/ISOBUS address structure."""

    source_address: int  # 0-255
    parameter_group_number: int  # PGN
    destination_address: int = 0xFF  # Broadcast by default
    priority: int = 6  # Default priority
    data_page: bool = False
    pdu_format: int = 0
    pdu_specific: int = 0


class CANMessageCallback(Protocol):
    """Protocol for CAN message callback functions."""

    def __call__(self, message: can.Message, interface_id: str) -> None:
        """Handle received CAN message."""
        ...


class PhysicalCANInterface(ABC):
    """Abstract base class for physical CAN interfaces."""

    def __init__(
        self,
        interface_id: str,
        config: InterfaceConfiguration,
        error_handler: CANErrorHandler,
    ) -> None:
        """Initialize physical CAN interface.

        Parameters
        ----------
        interface_id : str
            Unique identifier for this interface instance
        config : InterfaceConfiguration
            Interface configuration parameters
        error_handler : CANErrorHandler
            Error handling system
        """
        self.interface_id = interface_id
        self.config = config
        self.error_handler = error_handler
        self.validator = CANFrameValidator()

        self._state = InterfaceState.DISCONNECTED
        self._bus: can.BusABC | None = None
        self._notifier: can.Notifier | None = None
        self._listeners: list[can.Listener] = []
        self._message_callbacks: list[CANMessageCallback] = []

        # Statistics tracking
        self._status = InterfaceStatus(
            interface_id=interface_id,
            state=InterfaceState.DISCONNECTED,
            last_heartbeat=datetime.now(),
        )

        # Connection management
        self._connection_lock = asyncio.Lock()
        self._heartbeat_task: asyncio.Task | None = None
        self._message_reception_task: asyncio.Task | None = None  # Task for message reception loop
        self._auto_recovery_enabled = True

    @property
    def state(self) -> InterfaceState:
        """Get current interface state."""
        return self._state

    @property
    def status(self) -> InterfaceStatus:
        """Get current interface status."""
        return self._status

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to physical CAN interface.

        Returns
        -------
        bool
            True if connection successful
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from physical CAN interface.

        Returns
        -------
        bool
            True if disconnection successful
        """
        pass

    @abstractmethod
    async def send_message(self, message: can.Message) -> bool:
        """Send CAN message through physical interface.

        Parameters
        ----------
        message : can.Message
            CAN message to send

        Returns
        -------
        bool
            True if message sent successfully
        """
        pass

    @abstractmethod
    def get_hardware_info(self) -> dict[str, Any]:
        """Get hardware-specific information.

        Returns
        -------
        Dict[str, Any]
            Hardware information dictionary
        """
        pass

    def add_message_callback(self, callback: CANMessageCallback) -> None:
        """Add callback for received messages.

        Parameters
        ----------
        callback : CANMessageCallback
            Callback function for message handling
        """
        self._message_callbacks.append(callback)

    def remove_message_callback(self, callback: CANMessageCallback) -> None:
        """Remove message callback.

        Parameters
        ----------
        callback : CANMessageCallback
            Callback function to remove
        """
        if callback in self._message_callbacks:
            self._message_callbacks.remove(callback)

    async def _update_status(self) -> None:
        """Update interface status information."""
        self._status.last_heartbeat = datetime.now()
        self._status.state = self._state

        if self._bus and hasattr(self._bus, "get_stats"):
            try:
                stats: dict[str, Any] = self._bus.get_stats()
                self._status.bus_load_percentage = stats.get("bus_load", 0.0)
            except Exception as e:
                logger.debug(f"Could not get bus statistics: {e}")

    async def _heartbeat_loop(self) -> None:
        """Heartbeat loop for connection monitoring."""
        while self._state in [InterfaceState.CONNECTED, InterfaceState.RECOVERING]:
            try:
                await self._update_status()
                await asyncio.sleep(1.0)  # 1 second heartbeat
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Heartbeat error for {self.interface_id}: {e}")
                await asyncio.sleep(5.0)

    def _handle_received_message(self, message: can.Message) -> None:
        """Handle received CAN message.

        Parameters
        ----------
        message : can.Message
            Received CAN message
        """
        self._status.messages_received += 1

        # Call registered callbacks
        for callback in self._message_callbacks:
            try:
                callback(message, self.interface_id)
            except Exception as e:
                logger.error(f"Message callback error: {e}")
                self.error_handler.handle_error(
                    CANErrorType.DATA_CORRUPTION,
                    f"Message callback failed: {e}",
                    message.arbitration_id & 0xFF,
                )


class SocketCANInterface(PhysicalCANInterface):
    """Linux SocketCAN interface implementation."""

    async def connect(self) -> bool:
        """Connect to SocketCAN interface."""
        async with self._connection_lock:
            if self._state == InterfaceState.CONNECTED:
                return True

            try:
                self._state = InterfaceState.CONNECTING

                # Create SocketCAN bus
                self._bus = can.interface.Bus(
                    interface=self.config.interface_type.value,
                    channel=self.config.channel,
                    bitrate=self.config.bitrate.value,
                    fd=self.config.fd_enabled,
                    data_bitrate=self.config.data_bitrate,
                    can_filters=None,  # Accept all messages initially
                )

                # Set up message listener
                listener: can.BufferedReader = can.BufferedReader()
                self._listeners.append(listener)
                self._notifier = can.Notifier(self._bus, [listener])

                # Start heartbeat monitoring
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

                self._state = InterfaceState.CONNECTED
                logger.info(
                    f"SocketCAN connected: {self.config.channel} at {self.config.bitrate.value} bps"
                )

                # Start message reception task
                self._message_reception_task = asyncio.create_task(
                    self._message_reception_loop(listener)
                )

                return True

            except Exception as e:
                self._state = InterfaceState.ERROR
                self.error_handler.handle_error(
                    CANErrorType.TIMEOUT,
                    f"SocketCAN connection failed: {e}",
                    metadata={"channel": self.config.channel},
                )
                logger.error(f"SocketCAN connection failed: {e}")
                return False

    async def disconnect(self) -> bool:
        """Disconnect from SocketCAN interface."""
        async with self._connection_lock:
            try:
                self._state = InterfaceState.DISCONNECTED

                # Stop heartbeat
                if self._heartbeat_task:
                    self._heartbeat_task.cancel()
                    self._heartbeat_task = None

                # Stop message reception task
                if self._message_reception_task:
                    self._message_reception_task.cancel()
                    self._message_reception_task = None

                # Stop notifier
                if self._notifier:
                    self._notifier.stop()
                    self._notifier = None

                # Shutdown bus
                if self._bus:
                    self._bus.shutdown()
                    self._bus = None

                self._listeners.clear()
                logger.info(f"SocketCAN disconnected: {self.config.channel}")
                return True

            except Exception as e:
                logger.error(f"SocketCAN disconnect error: {e}")
                return False

    async def send_message(self, message: can.Message) -> bool:
        """Send message via SocketCAN."""
        if self._state != InterfaceState.CONNECTED or not self._bus:
            return False

        try:
            await asyncio.to_thread(self._bus.send, message)
            self._status.messages_sent += 1
            logger.debug(f"SocketCAN message sent: ID={message.arbitration_id:08X}")
            return True

        except Exception as e:
            self._status.errors_total += 1
            self.error_handler.handle_error(
                CANErrorType.DATA_CORRUPTION,
                f"SocketCAN send failed: {e}",
                message.arbitration_id & 0xFF,
            )
            return False

    def get_hardware_info(self) -> dict[str, Any]:
        """Get SocketCAN hardware information."""
        return {
            "interface_type": "SocketCAN",
            "channel": self.config.channel,
            "bitrate": self.config.bitrate.value,
            "fd_enabled": self.config.fd_enabled,
            "kernel_version": "Linux",  # Could be detected dynamically
            "driver": "socketcan",
        }

    async def _message_reception_loop(self, listener: can.BufferedReader) -> None:
        """Background task for receiving messages."""
        while self._state == InterfaceState.CONNECTED:
            try:
                message: can.Message | None = listener.get_message(timeout=1.0)
                if message:
                    self._handle_received_message(message)
            except can.CanError as e:
                self.error_handler.handle_error(
                    CANErrorType.DATA_CORRUPTION,
                    f"Message reception error: {e}",
                )
            except Exception:
                # Timeout or other non-critical error
                continue


class VirtualCANInterface(PhysicalCANInterface):
    """Virtual CAN interface implementation for testing and simulation."""

    async def connect(self) -> bool:
        """Connect to virtual CAN interface."""
        async with self._connection_lock:
            if self._state == InterfaceState.CONNECTED:
                return True

            try:
                self._state = InterfaceState.CONNECTING

                # Create virtual CAN bus
                self._bus = can.interface.Bus(
                    interface="virtual",
                    channel=self.config.channel,
                    bitrate=self.config.bitrate.value,
                    fd=self.config.fd_enabled,
                    data_bitrate=self.config.data_bitrate,
                    can_filters=None,  # Accept all messages initially
                )

                # Set up message listener
                listener: can.BufferedReader = can.BufferedReader()
                self._listeners.append(listener)
                self._notifier = can.Notifier(self._bus, [listener])

                # Start heartbeat monitoring
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

                self._state = InterfaceState.CONNECTED
                logger.info(
                    f"Virtual CAN connected: {self.config.channel} at {self.config.bitrate.value} bps"
                )

                # Start message reception task
                self._message_reception_task = asyncio.create_task(
                    self._message_reception_loop(listener)
                )

                return True

            except Exception as e:
                self._state = InterfaceState.ERROR
                self.error_handler.handle_error(
                    CANErrorType.TIMEOUT,
                    f"Virtual CAN connection failed: {e}",
                    metadata={"channel": self.config.channel},
                )
                logger.error(f"Virtual CAN connection failed: {e}")
                return False

    async def disconnect(self) -> bool:
        """Disconnect from virtual CAN interface."""
        async with self._connection_lock:
            try:
                self._state = InterfaceState.DISCONNECTED

                # Stop heartbeat
                if self._heartbeat_task:
                    self._heartbeat_task.cancel()
                    self._heartbeat_task = None

                # Stop message reception task
                if self._message_reception_task:
                    self._message_reception_task.cancel()
                    self._message_reception_task = None

                # Stop notifier
                if self._notifier:
                    self._notifier.stop()
                    self._notifier = None

                # Shutdown bus
                if self._bus:
                    self._bus.shutdown()
                    self._bus = None

                self._listeners.clear()
                logger.info(f"Virtual CAN disconnected: {self.config.channel}")
                return True

            except Exception as e:
                logger.error(f"Virtual CAN disconnect error: {e}")
                return False

    async def send_message(self, message: can.Message) -> bool:
        """Send message via virtual CAN."""
        if self._state != InterfaceState.CONNECTED or not self._bus:
            return False

        try:
            await asyncio.to_thread(self._bus.send, message)
            self._status.messages_sent += 1
            logger.debug(f"Virtual CAN message sent: ID={message.arbitration_id:08X}")
            return True

        except Exception as e:
            self._status.errors_total += 1
            self.error_handler.handle_error(
                CANErrorType.DATA_CORRUPTION,
                f"Virtual CAN send failed: {e}",
                message.arbitration_id & 0xFF,
            )
            return False

    def get_hardware_info(self) -> dict[str, Any]:
        """Get virtual CAN hardware information."""
        return {
            "interface_type": "VirtualCAN",
            "channel": self.config.channel,
            "bitrate": self.config.bitrate.value,
            "fd_enabled": self.config.fd_enabled,
            "driver": "python-can-virtual",
        }

    async def _message_reception_loop(self, listener: can.BufferedReader) -> None:
        """Background task for receiving messages."""
        while self._state == InterfaceState.CONNECTED:
            try:
                message: can.Message | None = listener.get_message(timeout=1.0)
                if message:
                    self._handle_received_message(message)
            except can.CanError as e:
                self.error_handler.handle_error(
                    CANErrorType.DATA_CORRUPTION,
                    f"Message reception error: {e}",
                )
            except Exception:
                # Timeout or other non-critical error
                continue


class PhysicalCANManager:
    """Manages multiple physical CAN interfaces for tractor connectivity."""

    def __init__(
        self,
        error_handler: CANErrorHandler | None = None,
        error_logger: ISOBUSErrorLogger | None = None,
    ) -> None:
        """Initialize physical CAN manager.

        Parameters
        ----------
        error_handler : CANErrorHandler, optional
            Error handling system
        error_logger : ISOBUSErrorLogger, optional
            Error logging system
        """
        self.error_handler = error_handler or CANErrorHandler()
        self.error_logger = error_logger or ISOBUSErrorLogger()

        self._interfaces: dict[str, PhysicalCANInterface] = {}
        self._active_interfaces: set[str] = set()
        self._manager_lock = asyncio.Lock()

        # Global message callbacks
        self._global_callbacks: list[CANMessageCallback] = []

    async def create_interface(
        self,
        interface_id: str,
        config: InterfaceConfiguration,
    ) -> PhysicalCANInterface:
        """Create new physical CAN interface.

        Parameters
        ----------
        interface_id : str
            Unique identifier for interface
        config : InterfaceConfiguration
            Interface configuration

        Returns
        -------
        PhysicalCANInterface
            Created interface instance
        """
        async with self._manager_lock:
            if interface_id in self._interfaces:
                raise ValueError(f"Interface {interface_id} already exists")

            # Create appropriate interface type
            if config.interface_type == CANInterfaceType.SOCKETCAN:
                interface = SocketCANInterface(interface_id, config, self.error_handler)
            elif config.interface_type == CANInterfaceType.VIRTUAL:
                interface = VirtualCANInterface(interface_id, config, self.error_handler)
            else:
                raise NotImplementedError(
                    f"Interface type {config.interface_type} not implemented yet"
                )

            # Add global message callbacks
            for callback in self._global_callbacks:
                interface.add_message_callback(callback)

            self._interfaces[interface_id] = interface
            logger.info(f"Created CAN interface: {interface_id} ({config.interface_type.value})")

            return interface

    async def connect_interface(self, interface_id: str) -> bool:
        """Connect specific interface.

        Parameters
        ----------
        interface_id : str
            Interface to connect

        Returns
        -------
        bool
            True if connection successful
        """
        if interface_id not in self._interfaces:
            logger.error(f"Interface {interface_id} not found")
            return False

        interface = self._interfaces[interface_id]
        success = await interface.connect()

        if success:
            self._active_interfaces.add(interface_id)

        return success

    async def disconnect_interface(self, interface_id: str) -> bool:
        """Disconnect specific interface.

        Parameters
        ----------
        interface_id : str
            Interface to disconnect

        Returns
        -------
        bool
            True if disconnection successful
        """
        if interface_id not in self._interfaces:
            return False

        interface = self._interfaces[interface_id]
        success = await interface.disconnect()

        if success:
            self._active_interfaces.discard(interface_id)

        return success

    async def connect_all(self) -> dict[str, bool]:
        """Connect all configured interfaces.

        Returns
        -------
        Dict[str, bool]
            Connection results by interface ID
        """
        results = {}
        for interface_id in self._interfaces:
            results[interface_id] = await self.connect_interface(interface_id)
        return results

    async def disconnect_all(self) -> dict[str, bool]:
        """Disconnect all interfaces.

        Returns
        -------
        Dict[str, bool]
            Disconnection results by interface ID
        """
        results = {}
        for interface_id in list(self._active_interfaces):
            results[interface_id] = await self.disconnect_interface(interface_id)
        return results

    async def broadcast_message(self, message: can.Message) -> dict[str, bool]:
        """Broadcast message to all active interfaces.

        Parameters
        ----------
        message : can.Message
            Message to broadcast

        Returns
        -------
        Dict[str, bool]
            Send results by interface ID
        """
        results = {}
        for interface_id in self._active_interfaces:
            interface = self._interfaces[interface_id]
            results[interface_id] = await interface.send_message(message)
        return results

    def add_global_callback(self, callback: CANMessageCallback) -> None:
        """Add callback to all interfaces.

        Parameters
        ----------
        callback : CANMessageCallback
            Callback function
        """
        self._global_callbacks.append(callback)

        # Add to existing interfaces
        for interface in self._interfaces.values():
            interface.add_message_callback(callback)

    def get_interface_status(self, interface_id: str) -> InterfaceStatus | None:
        """Get status of specific interface.

        Parameters
        ----------
        interface_id : str
            Interface to query

        Returns
        -------
        Optional[InterfaceStatus]
            Interface status or None if not found
        """
        if interface_id in self._interfaces:
            return self._interfaces[interface_id].status
        return None

    def get_all_interface_status(self) -> dict[str, InterfaceStatus]:
        """Get status of all interfaces.

        Returns
        -------
        Dict[str, InterfaceStatus]
            Status by interface ID
        """
        return {
            interface_id: interface.status for interface_id, interface in self._interfaces.items()
        }

    def create_j1939_message(
        self,
        address: J1939Address,
        data: bytes,
        timestamp: float | None = None,
    ) -> can.Message:
        """Create J1939/ISOBUS CAN message.

        Parameters
        ----------
        address : J1939Address
            J1939 address structure
        data : bytes
            Message data payload
        timestamp : float, optional
            Message timestamp

        Returns
        -------
        can.Message
            Formatted CAN message
        """
        # Construct 29-bit CAN ID for J1939
        can_id: int = (
            (address.priority << 26)
            | (int(address.data_page) << 25)
            | (address.pdu_format << 16)
            | (address.pdu_specific << 8)
            | address.source_address
        )

        return can.Message(
            arbitration_id=can_id,
            data=data,
            is_extended_id=True,  # J1939 uses 29-bit IDs
            timestamp=timestamp or time.time(),
        )
