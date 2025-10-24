import logging

import can
from pybreaker import CircuitBreaker, CircuitBreakerError
from tenacity import retry, stop_after_attempt, wait_fixed


class CanBusManager:
    """
    Manages CAN bus communication for agricultural equipment.
    Supports various CAN interfaces and provides methods for sending and receiving messages.
    """

    def __init__(self, interface: str = "socketcan", channel: str = "can0", bitrate: int = 500000):
        """
        Initializes the CAN bus manager.

        Args:
            interface (str): The CAN interface to use (e.g., 'socketcan', 'pcan', 'kvaser').
            channel (str): The CAN channel to connect to (e.g., 'can0' for socketcan).
            bitrate (int): The bitrate of the CAN bus (e.g., 500000 for 500 kbit/s).
        """
        self.interface = interface
        self.channel = channel
        self.bitrate = bitrate
        self.bus: can.BusABC | None = None
        self.notifier: can.Notifier | None = None
        self.breaker = CircuitBreaker(fail_max=5, reset_timeout=60, exclude=[can.CanError])
        self.logger = logging.getLogger(__name__)

    def connect(self) -> None:
        """
        Connects to the CAN bus.
        """
        try:
            self.bus = can.interface.Bus(
                interface=self.interface, channel=self.channel, bitrate=self.bitrate
            )
            self.logger.info(
                f"Successfully connected to CAN bus: {self.interface} on {self.channel} at {self.bitrate} bps"
            )
            self.breaker.close()  # Close circuit on successful connection
        except Exception as e:
            self.logger.error(f"Failed to connect to CAN bus: {e}")
            self.bus = None
            self.breaker.open()  # Open circuit on connection failure

    def disconnect(self) -> None:
        """
        Disconnects from the CAN bus.
        """
        if self.notifier:
            self.notifier.stop()
            self.notifier = None
        if self.bus:
            self.bus.shutdown()
            self.bus = None
            self.logger.info("Disconnected from CAN bus.")
            self.breaker.open()  # Open circuit on disconnection

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def _send_message_with_retry(self, message: can.Message) -> bool:
        """
        Internal method to send a CAN message with retry logic.
        """
        if not self.bus:
            self.logger.warning("CAN bus not connected. Cannot send message.")
            raise can.CanError("CAN bus not connected")  # Raise exception for tenacity to catch
        try:
            self.bus.send(message)
            self.logger.debug(f"Message sent: {message}")
            return True
        except can.CanError as e:
            self.logger.warning(f"Failed to send CAN message: {e}. Retrying...")
            raise  # Re-raise for tenacity to catch

    def send_reliable_message(self, message: can.Message) -> bool:
        """
        Sends a CAN message reliably with retries and circuit breaker protection.
        """
        try:
            return self.breaker.call(self._send_message_with_retry, message)
        except CircuitBreakerError:
            self.logger.error(f"Circuit breaker is open. Cannot send message {message}.")
            return False
        except can.CanError:
            self.logger.error(f"Failed to send message {message} after multiple retries.")
            return False

    def add_listener(self, listener: can.Listener) -> None:
        """
        Adds a listener to receive CAN messages.

        Args:
            listener (can.Listener): The listener object to add.
        """
        if not self.bus:
            self.logger.warning("CAN bus not connected. Cannot add listener.")
            return
        if not self.notifier:
            self.notifier = can.Notifier(self.bus, [listener])
        else:
            self.notifier.add_listener(listener)

    def remove_listener(self, listener: can.Listener) -> None:
        """
        Removes a listener from receiving CAN messages.

        Args:
            listener (can.Listener): The listener object to remove.
        """
        if self.notifier:
            self.notifier.remove_listener(listener)
            if not self.notifier.listeners:
                self.notifier.stop()
                self.notifier = None
