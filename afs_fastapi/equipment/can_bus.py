import can


class CANBus:
    def __init__(self, interface: str, channel: str):
        try:
            self.bus = can.Bus(interface=interface, channel=channel)
        except can.CanError as e:
            raise can.CanInterfaceNotImplementedError(f"Failed to initialize CAN bus: {e}") from e

    def send_message(self, message: can.Message):
        try:
            self.bus.send(message)
        except can.CanError as e:
            print(f"Failed to send message: {e}")

    def receive_message(self, timeout: float = 1.0) -> can.Message | None:
        try:
            return self.bus.recv(timeout=timeout)
        except can.CanError as e:
            print(f"Failed to receive message: {e}")
            return None

    def shutdown(self):
        self.bus.shutdown()
