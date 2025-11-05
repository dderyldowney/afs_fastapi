"""
Smart CAN Hardware Abstraction Layer with automatic platform detection.

This module provides cross-platform CAN communication with automatic interface
selection based on the underlying operating system and hardware availability.
"""

from __future__ import annotations

import logging
from typing import Protocol

import can

from afs_fastapi.core.platform_detection import select_optimal_can_interface

# Configure logging for CAN HAL
logger = logging.getLogger(__name__)


class CanHal(Protocol):
    """Hardware Abstraction Layer for CAN communication."""

    def connect(self, channel: str, interface: str) -> None:
        """Connects to the CAN bus."""
        ...

    def disconnect(self) -> None:
        """Disconnects from the CAN bus."""
        ...

    def send(self, msg: can.Message) -> None:
        """Sends a CAN message."""
        ...

    def receive(self, timeout: float | None = None) -> can.Message | None:
        """Receives a CAN message."""
        ...


class SmartCanHal:
    """Smart CAN HAL with automatic platform detection and interface selection.

    This implementation replaces traditional mocking with intelligent CAN interface
    selection that works across all platforms (Linux, macOS, Windows) while
    maintaining full agricultural ISOBUS/J1939 compatibility.
    """

    def __init__(self, preferred_interface: str | None = None) -> None:
        """Initialize smart CAN HAL.

        Parameters
        ----------
        preferred_interface : str, optional
            Preferred CAN interface. If None, auto-selects based on platform.
        """
        self._bus: can.BusABC | None = None
        self._interface_config: dict[str, any] | None = None
        self._preferred_interface = preferred_interface
        self._connection_info: dict[str, any] = {}

    def connect(self, channel: str | None = None, interface: str | None = None) -> None:
        """Connect to CAN bus using optimal interface for current platform.

        Parameters
        ----------
        channel : str, optional
            CAN channel identifier. If None, uses platform-appropriate default.
        interface : str, optional
            Interface type. If None, auto-selects based on platform and availability.

        Raises
        -------
            RuntimeError: If connection fails
            ValueError: If interface is not supported on current platform
        """
        try:
            # Select optimal interface configuration
            self._interface_config = select_optimal_can_interface(
                preferred_interface=interface or self._preferred_interface, allow_fallback=True
            )

            # Determine channel and interface from configuration
            actual_channel = channel or self._interface_config["configuration"]["channel"]
            actual_interface = self._interface_config["configuration"]["interface"]

            logger.info(
                f"Connecting to CAN bus: channel={actual_channel}, interface={actual_interface}"
            )

            # Create CAN bus connection
            self._bus = can.interface.Bus(
                channel=actual_channel,
                interface=actual_interface,
                bitrate=self._interface_config["configuration"]["bitrate"],
            )

            # Store connection information
            self._connection_info = {
                "channel": actual_channel,
                "interface": actual_interface,
                "bitrate": self._interface_config["configuration"]["bitrate"],
                "platform": self._interface_config["platform"],
                "fallback_used": self._interface_config["fallback_used"],
                "notes": self._interface_config["notes"],
            }

            logger.info(f"Successfully connected to CAN bus: {self._connection_info}")

        except Exception as e:
            logger.error(f"Failed to connect to CAN bus: {e}")
            raise RuntimeError(f"CAN connection failed: {e}") from e

    def disconnect(self) -> None:
        """Disconnect from CAN bus."""
        if self._bus:
            try:
                self._bus.shutdown()
                logger.info("Disconnected from CAN bus")
            except Exception as e:
                logger.warning(f"Error during CAN disconnect: {e}")
            finally:
                self._bus = None
                self._connection_info = {}

    def send(self, msg: can.Message) -> None:
        """Send a CAN message.

        Parameters
        ----------
        msg : can.Message
            CAN message to send

        Raises
        ------
        RuntimeError: If not connected to CAN bus
        """
        if not self._bus:
            raise RuntimeError("Not connected to CAN bus. Call connect() first.")

        try:
            self._bus.send(msg)
            logger.debug(f"CAN message sent: ID={msg.arbitration_id:08X}, DLC={msg.dlc}")
        except Exception as e:
            logger.error(f"Failed to send CAN message: {e}")
            raise

    def receive(self, timeout: float | None = None) -> can.Message | None:
        """Receive a CAN message.

        Parameters
        ----------
        timeout : float, optional
            Receive timeout in seconds. If None, blocks indefinitely.

        Returns
        -------
        can.Message | None
            Received CAN message or None if timeout reached

        Raises
        ------
        RuntimeError: If not connected to CAN bus
        """
        if not self._bus:
            raise RuntimeError("Not connected to CAN bus. Call connect() first.")

        try:
            msg = self._bus.recv(timeout)
            if msg:
                logger.debug(f"CAN message received: ID={msg.arbitration_id:08X}, DLC={msg.dlc}")
            return msg
        except Exception as e:
            logger.debug(f"CAN receive timeout or error: {e}")
            return None

    def get_connection_info(self) -> dict[str, any]:
        """Get information about the current CAN connection.

        Returns
        -------
        dict[str, any]
            Connection information including platform, interface, and configuration
        """
        return self._connection_info.copy()

    def is_connected(self) -> bool:
        """Check if connected to CAN bus.

        Returns
        -------
        bool
            True if connected, False otherwise
        """
        return self._bus is not None

    def get_platform_capabilities(self) -> dict[str, any]:
        """Get platform CAN capabilities.

        Returns
        -------
        dict[str, any]
            Platform-specific CAN capabilities and available interfaces
        """
        if self._interface_config:
            return {
                "platform": self._interface_config["platform"],
                "capabilities": self._interface_config.get("capabilities", []),
                "available_interfaces": self._interface_config.get("available_interfaces", []),
                "recommended_interface": self._interface_config.get("recommended_interface"),
                "notes": self._interface_config.get("notes", []),
            }
        else:
            # Return capabilities without connecting
            from afs_fastapi.core.platform_detection import get_can_capabilities

            return get_can_capabilities()


# Maintain backward compatibility
MockCanHal = SmartCanHal
