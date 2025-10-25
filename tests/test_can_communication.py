from unittest.mock import patch

import can

from afs_fastapi.equipment.can_bus import CANBus


def test_can_bus_initialization_and_shutdown() -> None:
    """
    Test that the CANBus class initializes and shuts down correctly.
    """
    with patch("can.Bus") as mock_bus:
        # Create an instance of the CANBus
        can_bus = CANBus(interface="mock", channel="vcan0")

        # Assert that the can.Bus was called with the correct parameters
        mock_bus.assert_called_once_with(interface="mock", channel="vcan0")

        # Call the shutdown method
        can_bus.shutdown()

        # Assert that the shutdown method was called on the bus instance
        mock_bus.return_value.shutdown.assert_called_once()


def test_can_bus_send_message() -> None:
    """
    Test that the CANBus class can send a message.
    """
    with patch("can.Bus") as mock_bus:
        # Create an instance of the CANBus
        can_bus = CANBus(interface="mock", channel="vcan0")

        # Create a mock message
        message = can.Message(arbitration_id=0x123, data=[0x11, 0x22, 0x33])

        # Send the message
        can_bus.send_message(message)

        # Assert that the send method was called on the bus instance with the correct message
        mock_bus.return_value.send.assert_called_once_with(message)


def test_can_bus_receive_message() -> None:
    """
    Test that the CANBus class can receive a message.
    """
    with patch("can.Bus") as mock_bus:
        # Create an instance of the CANBus
        can_bus = CANBus(interface="mock", channel="vcan0")

        # Create a mock message to be returned by the recv method
        mock_message = can.Message(arbitration_id=0x123, data=[0x11, 0x22, 0x33])
        mock_bus.return_value.recv.return_value = mock_message

        # Receive the message
        received_message = can_bus.receive_message()

        # Assert that the recv method was called on the bus instance
        mock_bus.return_value.recv.assert_called_once_with(timeout=1.0)

        # Assert that the received message is the same as the mock message
        assert received_message == mock_message


def test_send_pgn_and_receive_ack() -> None:
    """
    Test sending a PGN/SPN message and receiving an acknowledgment.
    """
    with patch("can.Bus") as mock_bus:
        # Create an instance of the CANBus
        can_bus = CANBus(interface="mock", channel="vcan0")

        # PGN 65260 (0xFEEC) - Vehicle Identification
        pgn_message: can.Message = can.Message(
            arbitration_id=0xFEEC,
            data=[0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08],
            is_extended_id=True,
        )

        # Mock acknowledgment message
        ack_message: can.Message = can.Message(
            arbitration_id=0x18EEFF00,
            data=[0x01, 0x00, 0x00, 0x00, 0xFE, 0xEC, 0x00, 0x00],
            is_extended_id=True,
        )

        # Set the mock bus to return the ack message after the pgn message is sent
        mock_bus.return_value.recv.return_value = ack_message

        # Send the PGN message
        can_bus.send_message(pgn_message)

        # Receive the acknowledgment
        received_message = can_bus.receive_message()

        # Assert that the send method was called with the PGN message
        mock_bus.return_value.send.assert_called_once_with(pgn_message)

        # Assert that the recv method was called
        mock_bus.return_value.recv.assert_called_once_with(timeout=1.0)

        # Assert that the received message is the acknowledgment message
        assert received_message == ack_message
