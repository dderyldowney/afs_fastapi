import can
import pytest

# PGN 65260 (0xFEEC) - Vehicle Identification
PGN_MESSAGE = can.Message(
    arbitration_id=0xFEEC | 0x18000000,  # Add priority and extended ID flag
    data=[0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08],
    is_extended_id=True,
)

# Acknowledgment for PGN 65260
ACK_MESSAGE = can.Message(
    arbitration_id=0x18EEFF00,  # Global Address, PGN of Acknowledgement
    data=[
        0x01,  # Positive Acknowledgment
        0x00,
        0x00,
        0x00,  # Reserved
        0xEC,
        0xFE,
        0x00,
        0x00,  # PGN of acknowledged message (LSB first)
    ],
    is_extended_id=True,
)


@pytest.mark.parametrize("interface, channel", [("virtual", "test"), ("socketcan", "vcan0")])
def test_pgn_transmission_and_acknowledgment(interface, channel):
    """
    Tests sending a PGN message and receiving an acknowledgment.
    This test is designed to be portable and can be run on different platforms.
    """
    try:
        with can.Bus(interface=interface, channel=channel, receive_own_messages=True) as bus:
            # In a real scenario, another node on the bus would send the ACK.
            # For this test, we will simulate this by having the bus receive the ACK message we created.
            if interface == "virtual":
                # The virtual interface needs to be fed the messages it will receive
                # In a real test, you would have another thread or process sending the ACK.
                # For this simple test, we will just send the ack from the same bus.
                pass

            bus.send(PGN_MESSAGE)
            if interface == "virtual":
                bus.send(ACK_MESSAGE)  # Simulate the other node sending the ACK
            received_message = bus.recv(timeout=1.0)  # This will receive the PGN message
            received_message = bus.recv(timeout=1.0)  # This will receive the ACK message

            assert received_message is not None, "Did not receive any message"
            assert received_message.arbitration_id == ACK_MESSAGE.arbitration_id
            assert received_message.data == ACK_MESSAGE.data

    except (can.CanInterfaceNotImplementedError, OSError):
        if interface == "socketcan":
            pytest.skip("socketcan interface not available on this system. Skipping test.")
        else:
            pytest.fail(
                f"CAN interface '{interface}' not implemented. Please check your python-can installation."
            )
    except Exception as e:
        pytest.fail(f"An unexpected error occurred: {e}")
