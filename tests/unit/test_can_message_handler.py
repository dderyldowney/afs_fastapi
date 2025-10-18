from unittest.mock import MagicMock

import pytest

from afs_fastapi.equipment.can_message_handler import CANMessageHandler


class TestCANMessageHandler:
    def test_create_can_message_handler(self):
        """
        Tests that a CANMessageHandler object can be created.
        """
        handler = CANMessageHandler()
        assert isinstance(handler, CANMessageHandler)

    def test_encode_position_data_runs(self):
        """
        Tests that the encode_position_data method runs without error.
        """
        handler = CANMessageHandler()
        handler.encode_position_data(40.7128, -74.0060)

    def test_transmit_message_runs(self):
        """
        Tests that the transmit_message method runs without error.
        """
        handler = CANMessageHandler()
        handler.transmit_message(None)

    def test_encode_position_data(self):
        """
        Tests that the encode_position_data method correctly encodes the position data.
        """
        handler = CANMessageHandler()
        # Example coordinates for New York City
        latitude = 40.7128
        longitude = -74.0060
        encoded_message = handler.encode_position_data(latitude, longitude)
        # PGN 65280 is 0xFE00. The data is 8 bytes, with latitude and longitude
        # as 4-byte floats.
        # We will need to unpack the data to verify it.
        import struct

        assert encoded_message.arbitration_id == 0xFE00
        lat, lon = struct.unpack("<dd", encoded_message.data)
        assert pytest.approx(lat, 0.0001) == latitude
        assert pytest.approx(lon, 0.0001) == longitude

    def test_transmit_message(self):
        """
        Tests that the transmit_message method sends the message to the CAN bus.
        """
        handler = CANMessageHandler()
        mock_bus = MagicMock()
        handler.bus = mock_bus
        message = handler.encode_position_data(40.7128, -74.0060)
        handler.transmit_message(message)
        mock_bus.send.assert_called_once_with(message)
