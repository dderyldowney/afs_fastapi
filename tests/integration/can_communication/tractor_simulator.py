import can

from afs_fastapi.core.can_hal import MockCanHal

# Define the PGNs and SPNs for the test
COMMAND_PGN = 0x1234
ACK_PGN = 0x5678

# The SPN that contains the command
COMMAND_SPN = 1

# The expected value of the command SPN
EXPECTED_COMMAND = 1  # 1 = start engine

# The SPN that contains the acknowledgment
ACK_SPN = 1

# The value of the acknowledgment SPN
ACK_VALUE = 1  # 1 = command acknowledged


def tractor_simulator():
    """Simulates a tractor on the CAN bus."""
    can_hal = MockCanHal()
    can_hal.connect(channel="test", interface="mock")

    print("Tractor simulator started")
    while True:
        msg = can_hal.receive(timeout=1)
        if msg:
            if msg.arbitration_id == COMMAND_PGN:
                print(f"Received command PGN: {msg.arbitration_id}")
                # For simplicity, we assume the command is in the first byte
                if msg.data[0] == EXPECTED_COMMAND:
                    print("Received correct command, sending acknowledgment")
                    ack_msg = can.Message(
                        arbitration_id=ACK_PGN,
                        data=[ACK_VALUE],
                        is_extended_id=True,
                    )
                    can_hal.send(ack_msg)
                    print("Acknowledgment sent")
                    break
    can_hal.disconnect()


if __name__ == "__main__":
    tractor_simulator()
