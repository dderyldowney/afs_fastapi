import can

from afs_fastapi.core.can_hal import MockCanHal

# Define the PGNs and SPNs for the test
COMMAND_PGN = 0x1234
ACK_PGN = 0x5678

# The SPN that contains the command
COMMAND_SPN = 1

# The value of the command SPN
COMMAND_VALUE = 1  # 1 = start engine

# The SPN that contains the acknowledgment
ACK_SPN = 1

# The expected value of the acknowledgment SPN
EXPECTED_ACK = 1

HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 65433  # The port used by the server


def platform_test():
    """Represents the platform and runs the test."""
    can_hal = MockCanHal()
    can_hal.connect(channel="test", interface="virtual")

    print("Received start test message, sending command to CAN bus")
    msg = can.Message(
        arbitration_id=COMMAND_PGN,
        data=[COMMAND_VALUE],
        is_extended_id=True,
    )
    can_hal.send(msg)
    print("Command sent")

    # Wait for the acknowledgment
    while True:
        ack_msg = can_hal.receive(timeout=1)
        if ack_msg:
            if ack_msg.arbitration_id == ACK_PGN:
                print(f"Received acknowledgment PGN: {ack_msg.arbitration_id}")
                if ack_msg.data[0] == EXPECTED_ACK:
                    print("Test passed!")
                    break
                else:
                    print("Test failed: incorrect acknowledgment value")
                    break
    can_hal.disconnect()
