"""
Real CAN integration factory for agricultural testing.

This module provides real CAN communication components for integration testing,
replacing mocks with actual cross-platform CAN implementations.
"""

from __future__ import annotations

from typing import Any

from afs_fastapi.core.can_manager import create_can_manager


class CANBusConnectionManager:
    """CAN bus connection manager using cross-platform CAN system.

    Provides CAN communication with the same interface for test compatibility.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize CAN bus manager.

        Parameters
        ----------
        config : dict[str, Any], optional
            Connection configuration. If None, uses defaults.
        """
        self.config = config or {}
        self._can_manager = None
        self._is_initialized = False
        self._status = "DISCONNECTED"
        self._statistics = {"messages_sent": 0, "messages_received": 0, "errors": 0, "uptime": 0.0}

    async def initialize(self) -> bool:
        """Initialize the CAN connection manager.

        Returns
        -------
        bool
            True if initialization successful
        """
        try:
            # Create real CAN manager with cross-platform support
            self._can_manager = create_can_manager(
                interface=self.config.get("interface"),
                channel=self.config.get("channel"),
                auto_connect=True,
            )

            self._is_initialized = True
            self._status = "CONNECTED"
            return True

        except Exception:
            self._status = "ERROR"
            self._statistics["errors"] += 1
            return False

    async def shutdown(self) -> None:
        """Shutdown the CAN connection manager."""
        if self._can_manager:
            self._can_manager.disconnect()
            self._can_manager = None

        self._is_initialized = False
        self._status = "DISCONNECTED"

    async def connect_interface(self, interface_name: str, config: dict[str, Any]) -> bool:
        """Connect to a specific CAN interface.

        Parameters
        ----------
        interface_name : str
            Name of the interface to connect
        config : dict[str, Any]
            Interface configuration

        Returns
        -------
        bool
            True if connection successful
        """
        if not self._can_manager:
            await self.initialize()

        return self._can_manager.is_connected()

    async def disconnect_all(self) -> dict[str, bool]:
        """Disconnect all interfaces.

        Returns
        -------
        dict[str, bool]
            Status of each disconnection
        """
        if self._can_manager:
            self._can_manager.disconnect()
            return {"default": True}
        return {"default": False}

    async def get_interface_status(self, interface_name: str) -> dict[str, Any] | None:
        """Get status of a specific interface.

        Parameters
        ----------
        interface_name : str
            Name of the interface

        Returns
        -------
        dict[str, Any] | None
            Interface status or None if not found
        """
        if self._can_manager:
            return self._can_manager.get_connection_info()
        return None

    def add_global_callback(self, callback: callable) -> None:
        """Add global message callback.

        Parameters
        ----------
        callback : callable
            Callback function for received messages
        """
        if self._can_manager:
            self._can_manager.add_message_handler(callback)

    def get_manager_status(self) -> dict[str, Any]:
        """Get comprehensive manager status.

        Returns
        -------
        dict[str, Any]
            Manager status information
        """
        if self._can_manager:
            conn_info = self._can_manager.get_connection_info()
            return {
                "state": self._status,
                "statistics": self._statistics,
                "connection_pool": conn_info,
                "platform": conn_info.get("platform", "unknown"),
                "interface": conn_info.get("interface", "unknown"),
                "connected": conn_info.get("fallback_used", False),
            }
        else:
            return {
                "state": self._status,
                "statistics": self._statistics,
                "connection_pool": {},
                "platform": "unknown",
                "interface": "none",
                "connected": False,
            }


def create_real_can_manager(config: dict[str, Any] | None = None) -> CANBusConnectionManager:
    """Create a real CAN manager for integration testing.

    Parameters
    ----------
    config : dict[str, Any], optional
        CAN configuration

    Returns
    -------
    CANBusConnectionManager
        Real CAN manager instance
    """
    return CANBusConnectionManager(config)


# Compatibility with existing test code
def MockPhysicalManager(config: dict[str, Any] | None = None) -> CANBusConnectionManager:
    """Mock function that returns real implementation for backward compatibility."""
    return create_real_can_manager(config)


class ISOBUSManager:
    """ISOBUS manager using CAN communication.

    Provides ISOBUS communication implementation.
    """

    def __init__(self, can_manager: CANBusConnectionManager | None = None) -> None:
        """Initialize ISOBUS manager.

        Parameters
        ----------
        can_manager : CANBusConnectionManager, optional
            CAN manager to use. If None, creates a new one.
        """
        self._can_manager = can_manager or create_real_can_manager()
        self._is_initialized = False
        self._devices: dict[str, Any] = {}
        self._message_handlers: list[callable] = []

    async def initialize(self) -> bool:
        """Initialize the ISOBUS manager.

        Returns
        -------
        bool
            True if initialization successful
        """
        try:
            success = await self._can_manager.initialize()
            if success:
                self._can_manager.add_global_callback(self._handle_message)
                self._is_initialized = True
            return success
        except Exception:
            return False

    async def shutdown(self) -> None:
        """Shutdown the ISOBUS manager."""
        await self._can_manager.shutdown()
        self._is_initialized = False

    def add_device(self, device_id: str, device_config: dict[str, Any]) -> bool:
        """Add an ISOBUS device.

        Parameters
        ----------
        device_id : str
            Device identifier
        device_config : dict[str, Any]
            Device configuration

        Returns
        -------
        bool
            True if device added successfully
        """
        self._devices[device_id] = device_config
        return True

    def remove_device(self, device_id: str) -> bool:
        """Remove an ISOBUS device.

        Parameters
        ----------
        device_id : str
            Device identifier

        Returns
        -------
        bool
            True if device removed successfully
        """
        return self._devices.pop(device_id, None) is not None

    def add_message_handler(self, handler: callable) -> None:
        """Add message handler.

        Parameters
        ----------
        handler : callable
            Message handler function
        """
        self._message_handlers.append(handler)

    def _handle_message(self, message: dict[str, Any]) -> None:
        """Handle received CAN messages.

        Parameters
        ----------
        message : dict[str, Any]
            Decoded CAN message
        """
        for handler in self._message_handlers:
            try:
                handler(message)
            except Exception:
                pass  # Ignore handler errors in tests


def create_isobus_manager(can_manager: CANBusConnectionManager | None = None) -> ISOBUSManager:
    """Create an ISOBUS manager for testing.

    Parameters
    ----------
    can_manager : CANBusConnectionManager, optional
        CAN manager to use

    Returns
    -------
    ISOBUSManager
        ISOBUS manager instance
    """
    return ISOBUSManager(can_manager)
