from __future__ import annotations

from typing import Protocol

import can


class CanHal(Protocol):
    """Hardware Abstraction Layer for CAN communication."""

    def connect(self, channel: str, interface: str) -> None:
        """Connects to the CAN bus."""
        ...

    def disconnect(self) -> None:
        """Disconnects from the CAN bus."""
        ...

    def receive(self, timeout: float | None = None) -> can.Message | None: ...


class MockCanHal:
    """Mock implementation of CanHal for testing purposes.

    Supports 'virtual' interface for testing CAN communication without hardware.
    The 'virtual' interface creates an in-memory CAN bus for testing.
    """

    def __init__(self) -> None:
        self._bus: can.BusABC | None = None

    def connect(self, channel: str, interface: str) -> None:
        """Connect to CAN bus using specified interface.

        Args:
            channel: CAN channel identifier
            interface: Interface type ('virtual' for testing, 'mock' deprecated)

        Raises:
            ValueError: If interface is not supported for testing
        """
        if interface not in ("mock", "virtual"):
            raise ValueError(
                f"MockCanHal only supports 'mock' or 'virtual' interface, got '{interface}'"
            )
        # Use 'virtual' interface for actual testing (python-can built-in)
        actual_interface = "virtual" if interface in ("mock", "virtual") else interface
        self._bus = can.interface.Bus(channel=channel, interface=actual_interface)

    def disconnect(self) -> None:
        if self._bus:
            self._bus.shutdown()
            self._bus = None

    def send(self, msg: can.Message) -> None:
        if not self._bus:
            raise RuntimeError("Not connected to CAN bus.")
        self._bus.send(msg)

    def receive(self, timeout: float | None = None) -> can.Message | None:
        if not self._bus:
            raise RuntimeError("Not connected to CAN bus.")
        return self._bus.recv(timeout)
