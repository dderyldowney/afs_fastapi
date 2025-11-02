"""
Tests for agricultural ISOBUS integration with guaranteed delivery.

This module demonstrates and validates the integration of guaranteed delivery
with existing agricultural equipment functionality, showing how backward
compatibility is maintained while new reliability features are available.

Agricultural Integration Scenarios
----------------------------------
- Legacy ISOBUS operation (simulation mode)
- Enhanced reliable ISOBUS operation (guaranteed delivery mode)
- Multi-implement coordination with field allocation CRDTs
- Priority-based message handling for agricultural safety
"""

import unittest
from datetime import datetime
from unittest.mock import Mock

from afs_fastapi.equipment.farm_tractors import FarmTractor, ISOBUSMessage
from afs_fastapi.services.field_allocation import FieldAllocationCRDT


class TestAgriculturalISOBUSIntegration(unittest.TestCase):
    """Test integration of guaranteed delivery with agricultural operations."""

    def setUp(self):
        self.tractor = FarmTractor("John Deere", "8R", 2024)
        self.tractor.start_engine()

    def test_legacy_isobus_operation_compatibility(self):
        """Test that existing ISOBUS operations remain functional."""
        # Test basic message sending (legacy mode)
        test_message = ISOBUSMessage(
            pgn=0xFE48,
            source_address=0x80,
            destination_address=0xFF,
            data=b"\x03\x15\x07\x64\x01",
            timestamp=datetime.now(),
        )

        # Should work with original API
        result = self.tractor.send_message(test_message)
        self.assertTrue(result)

        # Status sending should work with original API
        status_result = self.tractor.send_tractor_status()
        self.assertTrue(status_result)

    def test_enhanced_reliable_isobus_operation(self):
        """Test new guaranteed delivery capabilities."""
        # Test reliable message sending
        test_message = ISOBUSMessage(
            pgn=0xFE48,
            source_address=0x80,
            destination_address=0xFF,
            data=b"\x03\x15\x07\x64\x01",
            timestamp=datetime.now(),
        )

        # Should work with new reliable flag
        result = self.tractor.send_message(test_message, use_reliable=True)
        self.assertTrue(result)

        # Status sending should work with reliable delivery
        status_result = self.tractor.send_tractor_status(use_reliable=True)
        self.assertTrue(status_result)

    def test_implement_command_integration(self):
        """Test agricultural implement command integration."""
        # Test implement command without guaranteed delivery
        basic_result = self.tractor.send_implement_command(
            implement_address=0x82,
            command_type="lower",
            parameters={"depth": 6.0, "speed": 8.0},
            use_reliable=False,
        )
        self.assertTrue(basic_result)

        # Test implement command with guaranteed delivery
        callback = Mock()
        reliable_result = self.tractor.send_implement_command(
            implement_address=0x83,
            command_type="enable",
            parameters={"seed_rate": 32000, "row_spacing": 30},
            use_reliable=True,
            delivery_callback=callback,
        )
        # Should return message ID for tracking
        self.assertIsInstance(reliable_result, str)

    def test_field_operation_coordination(self):
        """Test coordinated field operation with multiple implements."""
        # Create field allocation CRDT
        field_crdt = FieldAllocationCRDT("test_field", ["tractor_8r"])
        field_crdt.claim("section_A1", "tractor_8r")
        field_crdt.claim("section_A2", "tractor_8r")

        # Coordinate planting operation with multiple implements
        implement_addresses = [0x82, 0x83, 0x84]  # Planter, fertilizer, cultivator

        message_ids = self.tractor.coordinate_field_operation(
            field_crdt=field_crdt,
            operation_type="planting",
            implement_addresses=implement_addresses,
            use_reliable=True,
        )

        # Should return message IDs for tracking
        self.assertGreater(len(message_ids), 0)
        for msg_id in message_ids:
            self.assertIsInstance(msg_id, str)

    def test_priority_based_message_handling(self):
        """Test agricultural priority system integration."""
        # Test that different message types get appropriate priorities

        # Get priorities through the internal method
        emergency_priority = self.tractor._get_message_priority(0xFE49)
        status_priority = self.tractor._get_message_priority(0xFE48)

        # Emergency should have higher priority (lower number)
        self.assertLess(emergency_priority, status_priority)

    def test_acknowledgment_processing_integration(self):
        """Test acknowledgment processing in receive_message."""
        # Create an acknowledgment message
        ack_message = ISOBUSMessage(
            pgn=0xE800,  # ACK PGN
            source_address=0x81,
            destination_address=0x80,
            data=b"test_message_id",
            timestamp=datetime.now(),
        )

        # Add to message queue
        self.tractor.message_queue.append(ack_message)

        # Should process ACK and return None (internal processing)
        result = self.tractor.receive_message()
        self.assertIsNone(result)  # ACKs are processed internally

    def test_agricultural_implement_command_encoding(self):
        """Test agricultural command parameter encoding."""
        # Test various implement commands
        test_commands = [
            ("lower", {"depth": 6.0, "speed": 8.0}),
            ("raise", {"speed": 5.0}),
            ("enable", {"seed_rate": 32000, "rate": 250}),
            ("configure", {"depth": 4.5, "rate": 200, "speed": 7.5}),
        ]

        for command_type, parameters in test_commands:
            encoded_data = self.tractor._encode_implement_command(command_type, parameters)

            # Should return 8-byte command structure
            self.assertEqual(len(encoded_data), 8)
            self.assertIsInstance(encoded_data, bytes)

            # First byte should be command code
            self.assertGreaterEqual(encoded_data[0], 0x00)
            self.assertLessEqual(encoded_data[0], 0x05)

    def test_comprehensive_agricultural_workflow(self):
        """Test complete agricultural workflow with guaranteed delivery."""
        # 1. Setup field allocation
        field_crdt = FieldAllocationCRDT("corn_field_2024", ["john_deere_8r"])
        field_crdt.claim("section_north", "john_deere_8r")

        # 2. Send reliable status update
        self.tractor.set_gps_position(40.0, -73.0)
        status_result = self.tractor.send_tractor_status(use_reliable=True)
        self.assertTrue(status_result)

        # 3. Coordinate planting operation
        planters = [0x82, 0x83]  # Two precision planters
        planting_msg_ids = self.tractor.coordinate_field_operation(
            field_crdt=field_crdt,
            operation_type="planting",
            implement_addresses=planters,
            use_reliable=True,
        )
        self.assertGreater(len(planting_msg_ids), 0)

        # 4. Send individual implement commands with callbacks
        callback = Mock()
        cultivator_msg_id = self.tractor.send_implement_command(
            implement_address=0x84,
            command_type="lower",
            parameters={"depth": 8.0, "speed": 6.0},
            use_reliable=True,
            delivery_callback=callback,
        )
        self.assertIsInstance(cultivator_msg_id, str)

        # 5. Broadcast field allocation update
        allocation_msg_id = self.tractor.broadcast_field_allocation_reliable(field_crdt)
        self.assertIsInstance(allocation_msg_id, str)

    def test_backward_compatibility_with_existing_tests(self):
        """Ensure integration doesn't break existing functionality."""
        # These should work exactly as before
        device_name = self.tractor.get_device_name()
        self.assertIsInstance(device_name, str)

        # Message queue handling should work as before
        test_message = ISOBUSMessage(
            pgn=0xFE48,
            source_address=0x80,
            destination_address=0xFF,
            data=b"\x01\x02\x03",
            timestamp=datetime.now(),
        )

        # Add to queue and retrieve
        self.tractor.message_queue.append(test_message)
        received = self.tractor.receive_message()
        self.assertEqual(received, test_message)

        # Empty queue should return None
        empty_result = self.tractor.receive_message()
        self.assertIsNone(empty_result)

    def test_integration_with_emergency_stop_system(self):
        """Test integration of reliable messaging with safety systems."""
        # Setup autonomous operation
        self.tractor.set_gps_position(40.0, -73.0)
        self.tractor.enable_auto_steer()
        self.tractor.add_waypoint(40.1, -73.1)
        self.tractor.enable_autonomous_mode()

        # Test emergency stop with reliable broadcasting
        callback = Mock()
        message_ids = self.tractor.emergency_stop_reliable(delivery_callback=callback)

        # Should broadcast to multiple recipients
        self.assertGreater(len(message_ids), 0)
        for msg_id in message_ids:
            self.assertIsInstance(msg_id, str)

        # Verify safety state
        self.assertTrue(self.tractor.emergency_stop_active)
        self.assertFalse(self.tractor.autonomous_mode)


class TestAgriculturalPrioritySystem(unittest.TestCase):
    """Test agricultural message priority handling."""

    def setUp(self):
        self.tractor = FarmTractor("Case IH", "Magnum", 2024)

    def test_agricultural_priority_constants(self):
        """Test that agricultural priority constants are properly defined."""
        from afs_fastapi.equipment.reliable_isobus import ISOBUSPriority

        # Emergency should be highest priority (0)
        self.assertEqual(ISOBUSPriority.EMERGENCY_STOP, 0)
        self.assertEqual(ISOBUSPriority.COLLISION_AVOIDANCE, 1)
        self.assertEqual(ISOBUSPriority.FIELD_COORDINATION, 2)
        self.assertEqual(ISOBUSPriority.IMPLEMENT_CONTROL, 3)
        self.assertEqual(ISOBUSPriority.STATUS_UPDATE, 4)
        self.assertEqual(ISOBUSPriority.DIAGNOSTICS, 5)

    def test_pgn_to_priority_mapping(self):
        """Test PGN to priority mapping for agricultural operations."""
        # Test various PGN mappings
        test_mappings = [
            (0xFE49, 0),  # Emergency -> EMERGENCY_STOP
            (0xFE47, 1),  # Collision avoidance -> COLLISION_AVOIDANCE
            (0xEF00, 2),  # Field allocation -> FIELD_COORDINATION
            (0xCF00, 3),  # Implement control -> IMPLEMENT_CONTROL
            (0xFE48, 4),  # Status update -> STATUS_UPDATE
            (0x1234, 5),  # Unknown -> DIAGNOSTICS
        ]

        for pgn, expected_priority in test_mappings:
            actual_priority = self.tractor._get_message_priority(pgn)
            self.assertEqual(
                actual_priority,
                expected_priority,
                f"PGN {pgn:04X} should map to priority {expected_priority}",
            )


if __name__ == "__main__":
    unittest.main()
