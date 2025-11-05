"""
Cross-platform CAN manager for agricultural robotics.

This module provides a unified CAN interface that automatically selects the appropriate
communication method based on platform availability, replacing traditional mocking
with intelligent virtual CAN fallback for non-Linux systems.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from afs_fastapi.core.can_frame_codec import CANFrameCodec
from afs_fastapi.core.can_hal import SmartCanHal
from afs_fastapi.core.platform_detection import get_can_capabilities

# Configure logging for CAN manager
logger = logging.getLogger(__name__)


class CANManager:
    """Cross-platform CAN manager with automatic interface selection.

    This manager provides real CAN communication on Linux (SocketCAN) and
    virtual CAN communication on macOS/Windows, ensuring consistent behavior
    across all platforms for agricultural ISOBUS/J1939 communication.
    """

    def __init__(
        self,
        preferred_interface: str | None = None,
        channel: str | None = None,
        auto_connect: bool = True,
    ) -> None:
        """Initialize CAN manager.

        Parameters
        ----------
        preferred_interface : str, optional
            Preferred CAN interface. If None, auto-selects based on platform.
        channel : str, optional
            CAN channel identifier. If None, uses platform-appropriate default.
        auto_connect : bool, default True
            Whether to automatically connect on initialization.
        """
        self.preferred_interface = preferred_interface
        self.channel = channel
        self.auto_connect = auto_connect

        # Initialize components
        self._hal = SmartCanHal(preferred_interface=preferred_interface)
        self._codec = CANFrameCodec()
        self._message_handlers: list[Callable] = []
        self._receive_task: asyncio.Task | None = None
        self._is_running = False

        # Platform and connection info
        self._platform_info = get_can_capabilities()
        self._connection_info: dict[str, Any] = {}

        logger.info(f"CAN Manager initialized for platform: {self._platform_info['platform']}")

        if auto_connect:
            self.connect()

    def connect(self, channel: str | None = None, interface: str | None = None) -> None:
        """Connect to CAN bus using optimal interface.

        Parameters
        ----------
        channel : str, optional
            CAN channel identifier. If None, uses instance default or platform default.
        interface : str, optional
            Interface type. If None, uses instance default or auto-selects.

        Raises
        ------
        RuntimeError: If connection fails
        """
        try:
            # Use provided parameters or fall back to instance defaults
            actual_channel = channel or self.channel
            actual_interface = interface or self.preferred_interface

            # Connect using Smart HAL
            self._hal.connect(channel=actual_channel, interface=actual_interface)

            # Store connection information
            self._connection_info = self._hal.get_connection_info()

            logger.info(f"CAN Manager connected: {self._connection_info}")

        except Exception as e:
            logger.error(f"CAN Manager connection failed: {e}")
            raise

    def disconnect(self) -> None:
        """Disconnect from CAN bus."""
        try:
            if self._is_running:
                self.stop_receiving()

            self._hal.disconnect()
            self._connection_info = {}
            logger.info("CAN Manager disconnected")

        except Exception as e:
            logger.warning(f"Error during CAN disconnect: {e}")

    def is_connected(self) -> bool:
        """Check if connected to CAN bus.

        Returns
        -------
        bool
            True if connected, False otherwise
        """
        return self._hal.is_connected()

    def send_j1939_message(
        self,
        pgn: int,
        source_address: int,
        destination_address: int = 255,
        priority: int = 6,
        data: list[int] | None = None,
        **spn_values: Any,
    ) -> bool:
        """Send a J1939/ISOBUS message.

        Parameters
        ----------
        pgn : int
            Parameter Group Number
        source_address : int
            Source address (0-255)
        destination_address : int, default 255
            Destination address (0-255, 255 = global)
        priority : int, default 6
            Message priority (0-7, 0 = highest)
        data : list[int], optional
            Raw data bytes (overrides spn_values)
        **spn_values : Any
            SPN (Suspect Parameter Number) values for automatic encoding

        Returns
        -------
        bool
            True if message sent successfully, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot send message: not connected to CAN bus")
            return False

        try:
            # Encode message using codec
            if data:
                # Use provided raw data
                message = self._codec.encode_message(
                    pgn=pgn,
                    source_address=source_address,
                    spn_values={},  # No SPN values when using raw data
                    priority=priority,
                    destination_address=destination_address,
                )
                if message:
                    message.data = data
            else:
                # Use SPN values for automatic encoding
                message = self._codec.encode_message(
                    pgn=pgn,
                    source_address=source_address,
                    spn_values=spn_values,
                    priority=priority,
                    destination_address=destination_address,
                )

            if message:
                self._hal.send(message)
                logger.debug(
                    f"J1939 message sent: PGN={pgn:05X}, SA={source_address:02X}, DA={destination_address:02X}"
                )
                return True
            else:
                logger.error(f"Failed to encode J1939 message: PGN={pgn:05X}")
                return False

        except Exception as e:
            logger.error(f"Failed to send J1939 message: {e}")
            return False

    def decode_message(self, message) -> dict[str, Any] | None:
        """Decode a CAN message using J1939/ISOBUS protocol.

        Parameters
        ----------
        message : can.Message
            CAN message to decode

        Returns
        -------
        dict[str, Any] | None
            Decoded message data or None if decoding failed
        """
        try:
            decoded = self._codec.decode_message(message)
            if decoded:
                return {
                    "pgn": decoded.pgn,
                    "priority": decoded.priority,
                    "source_address": decoded.source_address,
                    "destination_address": decoded.destination_address,
                    "data": decoded.data,
                    "timestamp": decoded.timestamp,
                    "spn_data": decoded.spn_data,
                }
            else:
                return None

        except Exception as e:
            logger.error(f"Failed to decode CAN message: {e}")
            return None

    def start_receiving(
        self, message_callback: Callable[[dict[str, Any]], None] | None = None
    ) -> None:
        """Start receiving CAN messages asynchronously.

        Parameters
        ----------
        message_callback : Callable, optional
            Callback function for received messages. If None, uses registered handlers.
        """
        if not self.is_connected():
            raise RuntimeError("Cannot start receiving: not connected to CAN bus")

        if self._is_running:
            logger.warning("CAN receiving already started")
            return

        self._is_running = True
        self._receive_task = asyncio.create_task(self._receive_loop(message_callback))
        logger.info("CAN message receiving started")

    async def _receive_loop(
        self, message_callback: Callable[[dict[str, Any]], None] | None = None
    ) -> None:
        """Async receive loop for CAN messages."""
        logger.info("CAN receive loop started")

        while self._is_running:
            try:
                # Receive message with timeout
                message = self._hal.receive(timeout=0.1)
                if message:
                    # Decode message
                    decoded = self.decode_message(message)
                    if decoded:
                        # Call custom callback or registered handlers
                        if message_callback:
                            message_callback(decoded)
                        else:
                            for handler in self._message_handlers:
                                try:
                                    handler(decoded)
                                except Exception as e:
                                    logger.error(f"Message handler error: {e}")

                # Small delay to prevent busy waiting
                await asyncio.sleep(0.001)

            except Exception as e:
                logger.error(f"Error in CAN receive loop: {e}")
                await asyncio.sleep(0.1)

        logger.info("CAN receive loop stopped")

    def stop_receiving(self) -> None:
        """Stop receiving CAN messages."""
        if not self._is_running:
            return

        self._is_running = False
        if self._receive_task:
            self._receive_task.cancel()
            try:
                asyncio.get_event_loop().run_until_complete(self._receive_task)
            except (asyncio.CancelledError, RuntimeError):
                pass
            self._receive_task = None

        logger.info("CAN message receiving stopped")

    def add_message_handler(self, handler: Callable[[dict[str, Any]], None]) -> None:
        """Add a message handler callback.

        Parameters
        ----------
        handler : Callable
            Function to call when a message is received
        """
        self._message_handlers.append(handler)
        logger.debug(f"Added message handler: {handler.__name__}")

    def remove_message_handler(self, handler: Callable[[dict[str, Any]], None]) -> None:
        """Remove a message handler callback.

        Parameters
        ----------
        handler : Callable
            Function to remove from handlers
        """
        if handler in self._message_handlers:
            self._message_handlers.remove(handler)
            logger.debug(f"Removed message handler: {handler.__name__}")

    def get_connection_info(self) -> dict[str, Any]:
        """Get connection and platform information.

        Returns
        -------
        dict[str, Any]
            Comprehensive connection and platform information
        """
        info = self._connection_info.copy()
        info.update(
            {
                "platform_capabilities": self._platform_info,
                "is_receiving": self._is_running,
                "message_handlers_count": len(self._message_handlers),
            }
        )
        return info

    def send_tractor_telemetry(
        self,
        tractor_id: int,
        speed: float,
        rpm: int,
        engine_temperature: float,
        fuel_rate: float | None = None,
    ) -> bool:
        """Send tractor telemetry data via J1939.

        Parameters
        ----------
        tractor_id : int
            Tractor identifier (used as source address)
        speed : float
            Vehicle speed in km/h
        rpm : int
            Engine RPM
        engine_temperature : float
            Engine temperature in Celsius
        fuel_rate : float, optional
            Fuel consumption rate in L/h

        Returns
        -------
        bool
            True if message sent successfully
        """
        return self.send_j1939_message(
            pgn=61444,  # Electronic Engine Controller 1 - EEC1
            source_address=tractor_id,
            engine_speed=rpm,
            vehicle_speed=speed,
            engine_coolant_temperature=engine_temperature,
            fuel_rate=fuel_rate,
        )

    def send_emergency_stop(self, tractor_id: int, reason_code: int = 1, urgency: int = 7) -> bool:
        """Send emergency stop message via J1939.

        Parameters
        ----------
        tractor_id : int
            Tractor identifier sending the emergency stop
        reason_code : int, default 1
            Emergency reason code
        urgency : int, default 7
            Urgency level (0-7, 7 = highest)

        Returns
        -------
        bool
            True if message sent successfully
        """
        # Use high priority engine controller message for emergency stop indication
        # Set engine speed to 0 and high priority to indicate emergency condition
        return self.send_j1939_message(
            pgn=61444,  # Electronic Engine Controller 1
            source_address=tractor_id,
            engine_speed=0,  # Engine stopped
            priority=urgency,  # High priority for emergency
            emergency_stop=True,
        )

    def __enter__(self):
        """Context manager entry."""
        if not self.is_connected() and self.auto_connect:
            self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


# Convenience function for creating CAN managers
def create_can_manager(
    interface: str | None = None, channel: str | None = None, auto_connect: bool = True
) -> CANManager:
    """Create a CAN manager with optimal settings for the current platform.

    Parameters
    ----------
    interface : str, optional
        Preferred interface. If None, auto-selects.
    channel : str, optional
        Channel identifier. If None, uses platform default.
    auto_connect : bool, default True
        Whether to connect immediately.

    Returns
    -------
    CANManager
        Configured CAN manager instance
    """
    return CANManager(preferred_interface=interface, channel=channel, auto_connect=auto_connect)
