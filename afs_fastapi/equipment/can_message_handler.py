import struct

import can


class CANMessageHandler:
    def __init__(self, channel="vcan0", bustype="virtual"):
        """
        Initializes the CANMessageHandler.

        Args:
            channel: The channel to use for the CAN bus.
            bustype: The type of bus to use.
        """
        try:
            self.bus = can.Bus(channel=channel, interface=bustype)
        except can.CanError as e:
            print(f"Error creating CAN bus: {e}")
            self.bus = None

    def encode_position_data(self, latitude: float, longitude: float) -> can.Message:
        """
        Encodes the latitude and longitude into a CAN message.

        Args:
            latitude: The latitude in WGS84 decimal degrees format.
            longitude: The longitude in WGS84 decimal degrees format.

        Returns:
            A CAN message with PGN 65280 containing the encoded position data.
        """
        # PGN 65280 is 0xFE00
        arbitration_id = 0xFE00
        data = struct.pack("<dd", latitude, longitude)
        return can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=True)

    def transmit_message(self, message: can.Message):
        """
        Transmits a CAN message on the bus.

        Args:
            message: The CAN message to transmit.
        """
        if self.bus:
            try:
                self.bus.send(message)
            except can.CanError as e:
                print(f"Error sending CAN message: {e}")
