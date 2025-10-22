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
    """Mock implementation of CanHal for testing purposes."""

    def __init__(self) -> None:
        self._bus: can.BusABC | None = None

    def connect(self, channel: str, interface: str) -> None:
        if interface != "mock":
            raise ValueError("MockCanHal only supports 'mock' interface.")
        self._bus = can.interface.Bus(channel=channel, interface=interface)

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
