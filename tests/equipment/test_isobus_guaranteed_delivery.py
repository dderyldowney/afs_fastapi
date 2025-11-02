"""
Tests for ISOBUS guaranteed delivery enhancement.

This module defines the required behavior for reliable ISOBUS message delivery
in agricultural robotics scenarios where message loss could cause equipment
collisions, work duplication, or safety violations.

Test-First Development (RED Phase)
----------------------------------
These tests define the desired behavior before implementation. They will fail
initially and guide the implementation of the guaranteed delivery system.

Agricultural Context
--------------------
- Field section allocation requires confirmed delivery to prevent conflicts
- Emergency stop messages must be guaranteed for safety compliance
- Implement coordination depends on reliable communication protocols
- Network partitions are common in agricultural environments
"""

import time
import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from afs_fastapi.equipment.farm_tractors import FarmTractor, ISOBUSMessage
from afs_fastapi.equipment.reliable_isobus import (
    MessageDeliveryTracker,
    ReliableISOBUSDevice,
    ReliableISOBUSMessage,
)
from afs_fastapi.services.field_allocation import FieldAllocationCRDT


class TestReliableISOBUSMessage(unittest.TestCase):
    """Test reliable ISOBUS message structure and behavior."""

    def test_reliable_message_creation(self):
        """Test creation of reliable ISOBUS message with tracking."""
        base_message = ISOBUSMessage(
            pgn=0xFE48,
            source_address=0x80,
            destination_address=0xFF,
            data=b"\x01\x02\x03",
            timestamp=datetime.now(),
        )

        reliable_msg = ReliableISOBUSMessage(
            message_id="MSG_001",
            base_message=base_message,
            requires_ack=True,
            max_retries=3,
            retry_interval=0.1,
            timeout=2.0,
            priority=1,
        )

        self.assertEqual(reliable_msg.message_id, "MSG_001")
        self.assertEqual(reliable_msg.base_message, base_message)
        self.assertTrue(reliable_msg.requires_ack)
        self.assertEqual(reliable_msg.max_retries, 3)
        self.assertEqual(reliable_msg.retry_interval, 0.1)
        self.assertEqual(reliable_msg.timeout, 2.0)
        self.assertEqual(reliable_msg.priority, 1)

    def test_reliable_message_defaults(self):
        """Test reliable message creation with default parameters."""
        base_message = ISOBUSMessage(
            pgn=0xFE48,
            source_address=0x80,
            destination_address=0xFF,
            data=b"\x01\x02\x03",
            timestamp=datetime.now(),
        )

        reliable_msg = ReliableISOBUSMessage(message_id="MSG_002", base_message=base_message)

        self.assertTrue(reliable_msg.requires_ack)
        self.assertEqual(reliable_msg.max_retries, 3)
        self.assertEqual(reliable_msg.retry_interval, 0.1)
        self.assertEqual(reliable_msg.timeout, 2.0)
        self.assertEqual(reliable_msg.priority, 0)

    def test_emergency_message_priority(self):
        """Test high-priority emergency message configuration."""
        emergency_data = b"\xFF\x00\x00\x00\x01"  # Emergency stop pattern
        base_message = ISOBUSMessage(
            pgn=0xFE49,  # Emergency PGN
            source_address=0x80,
            destination_address=0xFF,
            data=emergency_data,
            timestamp=datetime.now(),
        )

        emergency_msg = ReliableISOBUSMessage(
            message_id="EMERGENCY_001",
            base_message=base_message,
            priority=0,  # Highest priority
            max_retries=5,  # More retries for safety
            retry_interval=0.05,  # Faster retries
            timeout=1.0,  # Shorter timeout for urgency
        )

        self.assertEqual(emergency_msg.priority, 0)
        self.assertEqual(emergency_msg.max_retries, 5)
        self.assertEqual(emergency_msg.retry_interval, 0.05)
        self.assertEqual(emergency_msg.timeout, 1.0)


class TestMessageDeliveryTracker(unittest.TestCase):
    """Test message delivery tracking and retry coordination."""

    def setUp(self):
        self.tracker = MessageDeliveryTracker()
        self.base_message = ISOBUSMessage(
            pgn=0xFE48,
            source_address=0x80,
            destination_address=0xFF,
            data=b"\x01\x02\x03",
            timestamp=datetime.now(),
        )

    def test_tracker_initialization(self):
        """Test delivery tracker initialization."""
        self.assertEqual(len(self.tracker._pending_messages), 0)
        self.assertEqual(len(self.tracker._acknowledgments), 0)
        self.assertEqual(len(self.tracker._retry_queue), 0)

    def test_track_message_basic(self):
        """Test tracking a message for delivery confirmation."""
        reliable_msg = ReliableISOBUSMessage(message_id="MSG_001", base_message=self.base_message)

        self.tracker.track_message(reliable_msg)

        self.assertIn("MSG_001", self.tracker._pending_messages)
        self.assertEqual(self.tracker._pending_messages["MSG_001"], reliable_msg)

    def test_track_message_with_retry_schedule(self):
        """Test message tracking includes retry scheduling."""
        reliable_msg = ReliableISOBUSMessage(
            message_id="MSG_002",
            base_message=self.base_message,
            retry_interval=0.1,
        )

        current_time = time.time()
        with patch("time.time", return_value=current_time):
            self.tracker.track_message(reliable_msg)

        # Should schedule first retry in priority queue
        self.assertEqual(len(self.tracker._retry_queue), 1)
        retry_time, priority, sequence, message_id = self.tracker._retry_queue[0]
        self.assertEqual(message_id, "MSG_002")
        self.assertAlmostEqual(retry_time, current_time + 0.1, places=2)
        self.assertEqual(priority, 0)  # Default priority

    def test_handle_acknowledgment_success(self):
        """Test processing successful message acknowledgment."""
        reliable_msg = ReliableISOBUSMessage(message_id="MSG_003", base_message=self.base_message)

        self.tracker.track_message(reliable_msg)
        result = self.tracker.handle_acknowledgment("MSG_003")

        self.assertTrue(result)
        self.assertNotIn("MSG_003", self.tracker._pending_messages)
        self.assertIn("MSG_003", self.tracker._acknowledgments)

    def test_handle_acknowledgment_unknown_message(self):
        """Test acknowledgment for unknown message ID."""
        result = self.tracker.handle_acknowledgment("UNKNOWN_MSG")

        self.assertFalse(result)
        self.assertNotIn("UNKNOWN_MSG", self.tracker._acknowledgments)

    def test_process_retries_timing(self):
        """Test retry processing based on timing."""
        reliable_msg = ReliableISOBUSMessage(
            message_id="MSG_004",
            base_message=self.base_message,
            retry_interval=0.1,
        )

        current_time = time.time()
        with patch("time.time", return_value=current_time):
            self.tracker.track_message(reliable_msg)

        # Before retry time - no retries
        with patch("time.time", return_value=current_time + 0.05):
            retries = self.tracker.process_retries()
            self.assertEqual(len(retries), 0)

        # After retry time - should return message for retry
        with patch("time.time", return_value=current_time + 0.15):
            retries = self.tracker.process_retries()
            self.assertEqual(len(retries), 1)
            self.assertEqual(retries[0].message_id, "MSG_004")

    def test_exponential_backoff_retry_intervals(self):
        """Test exponential backoff for retry intervals."""
        reliable_msg = ReliableISOBUSMessage(
            message_id="MSG_005",
            base_message=self.base_message,
            retry_interval=0.1,
            max_retries=3,
        )

        self.tracker.track_message(reliable_msg)

        # Simulate multiple retry attempts
        base_time = time.time()
        expected_intervals = [0.1, 0.2, 0.4]  # Exponential backoff

        for i, _expected_interval in enumerate(expected_intervals):
            with patch("time.time", return_value=base_time + sum(expected_intervals[: i + 1])):
                retries = self.tracker.process_retries()
                if i < len(expected_intervals) - 1:
                    self.assertEqual(len(retries), 1)
                else:
                    # Should stop retrying after max_retries
                    break

    def test_timeout_handling(self):
        """Test message timeout and cleanup."""
        reliable_msg = ReliableISOBUSMessage(
            message_id="MSG_006",
            base_message=self.base_message,
            timeout=1.0,
        )

        current_time = time.time()
        with patch("time.time", return_value=current_time):
            self.tracker.track_message(reliable_msg)

        # After timeout period
        with patch("time.time", return_value=current_time + 1.5):
            timed_out = self.tracker.cleanup_timed_out_messages()
            self.assertEqual(len(timed_out), 1)
            self.assertEqual(timed_out[0], "MSG_006")
            self.assertNotIn("MSG_006", self.tracker._pending_messages)


class TestReliableISOBUSDevice(unittest.TestCase):
    """Test enhanced ISOBUS device with guaranteed delivery."""

    def setUp(self):
        self.device = ReliableISOBUSDevice(device_address=0x80)
        self.base_message = ISOBUSMessage(
            pgn=0xFE48,
            source_address=0x80,
            destination_address=0xFF,
            data=b"\x01\x02\x03",
            timestamp=datetime.now(),
        )

    def test_device_initialization(self):
        """Test reliable ISOBUS device initialization."""
        self.assertEqual(self.device.device_address, 0x80)
        self.assertIsInstance(self.device.delivery_tracker, MessageDeliveryTracker)
        self.assertEqual(len(self.device._outbound_queue), 0)
        self.assertEqual(len(self.device._inbound_queue), 0)

    def test_send_message_with_reliability(self):
        """Test sending message with delivery guarantee."""
        callback = Mock()

        message_id = self.device.send_reliable_message(
            self.base_message,
            delivery_callback=callback,
            requires_ack=True,
            max_retries=3,
        )

        self.assertIsNotNone(message_id)
        self.assertIn(message_id, self.device.delivery_tracker._pending_messages)

    def test_send_message_fire_and_forget(self):
        """Test sending message without delivery guarantee."""
        message_id = self.device.send_reliable_message(
            self.base_message,
            requires_ack=False,
        )

        self.assertIsNotNone(message_id)
        # Should not be tracked since no ack required
        self.assertNotIn(message_id, self.device.delivery_tracker._pending_messages)

    def test_receive_message_with_auto_ack(self):
        """Test receiving message with automatic acknowledgment."""
        # Simulate incoming message
        incoming_msg = ReliableISOBUSMessage(
            message_id="INCOMING_001",
            base_message=self.base_message,
            requires_ack=True,
        )

        ack_sent = self.device.receive_reliable_message(incoming_msg)

        self.assertTrue(ack_sent)
        # Should have queued acknowledgment for transmission
        self.assertGreater(len(self.device._outbound_queue), 0)

    def test_duplicate_message_handling(self):
        """Test handling of duplicate messages during retries."""
        original_msg = ReliableISOBUSMessage(
            message_id="DUP_001",
            base_message=self.base_message,
            requires_ack=True,
        )

        # Receive original message
        ack1 = self.device.receive_reliable_message(original_msg)
        self.assertTrue(ack1)

        # Receive duplicate (retry scenario)
        ack2 = self.device.receive_reliable_message(original_msg)
        self.assertTrue(ack2)  # Should still ack but not reprocess

        # Verify only one processing occurred (would check callback counts in real implementation)

    def test_process_acknowledgments(self):
        """Test processing received acknowledgments."""
        # Send a message that requires ack
        message_id = self.device.send_reliable_message(
            self.base_message,
            requires_ack=True,
        )

        # Simulate receiving acknowledgment
        ack_message = ISOBUSMessage(
            pgn=0xE800,  # ACK PGN
            source_address=0xFF,
            destination_address=0x80,
            data=message_id.encode(),
            timestamp=datetime.now(),
        )

        result = self.device.process_acknowledgment(ack_message)
        self.assertTrue(result)
        self.assertNotIn(message_id, self.device.delivery_tracker._pending_messages)


class TestAgriculturalScenarios(unittest.TestCase):
    """Test guaranteed delivery in agricultural robotics scenarios."""

    def setUp(self):
        self.tractor_a = FarmTractor("John Deere", "8R", 2024)
        self.tractor_b = FarmTractor("Case IH", "Magnum", 2024)

        # Enhance tractors with reliable messaging
        self.tractor_a.reliable_isobus = ReliableISOBUSDevice(device_address=0x80)
        self.tractor_b.reliable_isobus = ReliableISOBUSDevice(device_address=0x81)

    def test_emergency_stop_guaranteed_delivery(self):
        """Test emergency stop message guaranteed delivery."""
        # Tractor A triggers emergency stop
        emergency_data = b"\xFF\x00\x00\x00\x01"
        emergency_msg = ISOBUSMessage(
            pgn=0xFE49,
            source_address=0x80,
            destination_address=0xFF,
            data=emergency_data,
            timestamp=datetime.now(),
        )

        # Send with high priority and guaranteed delivery
        callback = Mock()
        message_id = self.tractor_a.reliable_isobus.send_reliable_message(
            emergency_msg,
            delivery_callback=callback,
            priority=0,  # Highest priority
            max_retries=5,
            retry_interval=0.05,
        )

        # Verify emergency message is tracked with priority
        pending = self.tractor_a.reliable_isobus.delivery_tracker._pending_messages
        self.assertIn(message_id, pending)
        self.assertEqual(pending[message_id].priority, 0)

    def test_field_allocation_guaranteed_delivery(self):
        """Test field section allocation with guaranteed delivery."""
        # Create field allocation CRDT
        field_crdt = FieldAllocationCRDT("field_001", ["tractor_a", "tractor_b"])
        field_crdt.claim("section_001", "tractor_a")

        # Serialize for transmission
        serialized_data = field_crdt.serialize()
        allocation_msg = ISOBUSMessage(
            pgn=0xEF00,  # Custom PGN for field allocation
            source_address=0x80,
            destination_address=0x81,
            data=str(serialized_data).encode(),
            timestamp=datetime.now(),
        )

        # Send with guaranteed delivery
        callback = Mock()
        message_id = self.tractor_a.reliable_isobus.send_reliable_message(
            allocation_msg,
            delivery_callback=callback,
            requires_ack=True,
        )

        # Simulate successful delivery
        ack_msg = ISOBUSMessage(
            pgn=0xE800,
            source_address=0x81,
            destination_address=0x80,
            data=message_id.encode(),
            timestamp=datetime.now(),
        )

        result = self.tractor_a.reliable_isobus.process_acknowledgment(ack_msg)
        self.assertTrue(result)
        callback.assert_called_once_with(message_id, "delivered")

    def test_implement_coordination_retry_logic(self):
        """Test implement coordination with retry logic."""
        # Tractor coordinating with implement
        implement_msg = ISOBUSMessage(
            pgn=0xCF00,  # Implement control PGN
            source_address=0x80,
            destination_address=0x82,  # Implement address
            data=b"\x01\x05\x00\x64",  # Lower implement to 5 inches
            timestamp=datetime.now(),
        )

        callback = Mock()
        message_id = self.tractor_a.reliable_isobus.send_reliable_message(
            implement_msg,
            delivery_callback=callback,
            max_retries=3,
            retry_interval=0.2,
        )

        # Simulate network partition - no ack received
        current_time = time.time()
        with patch("time.time", return_value=current_time + 0.3):
            retries = self.tractor_a.reliable_isobus.delivery_tracker.process_retries()
            self.assertEqual(len(retries), 1)
            self.assertEqual(retries[0].message_id, message_id)

    def test_fleet_synchronization_priority_handling(self):
        """Test fleet synchronization with message priority handling."""
        # Multiple tractors sending different priority messages
        high_priority_msg = ISOBUSMessage(
            pgn=0xFE49,  # Emergency
            source_address=0x80,
            destination_address=0xFF,
            data=b"\xFF\x00\x00\x00\x01",
            timestamp=datetime.now(),
        )

        low_priority_msg = ISOBUSMessage(
            pgn=0xFE48,  # Status update
            source_address=0x80,
            destination_address=0xFF,
            data=b"\x03\x15\x07\x64\x01",
            timestamp=datetime.now(),
        )

        # Send messages with different priorities
        high_id = self.tractor_a.reliable_isobus.send_reliable_message(
            high_priority_msg, priority=0
        )
        low_id = self.tractor_a.reliable_isobus.send_reliable_message(low_priority_msg, priority=10)

        # Verify priority ordering in processing
        pending = self.tractor_a.reliable_isobus.delivery_tracker._pending_messages
        self.assertEqual(pending[high_id].priority, 0)
        self.assertEqual(pending[low_id].priority, 10)


class TestIntegrationWithFarmTractor(unittest.TestCase):
    """Test integration of guaranteed delivery with existing FarmTractor class."""

    def setUp(self):
        self.tractor = FarmTractor("Test", "Enhanced", 2024)

    def test_enhanced_send_tractor_status(self):
        """Test enhanced tractor status with guaranteed delivery."""
        # Start engine for realistic status
        self.tractor.start_engine()
        self.tractor.change_gear(3)
        self.tractor.accelerate(15)

        # Send status with guaranteed delivery
        callback = Mock()
        message_id = self.tractor.send_tractor_status_reliable(
            delivery_callback=callback,
            requires_ack=True,
        )

        self.assertIsNotNone(message_id)
        # Should be tracked for delivery confirmation
        self.assertTrue(hasattr(self.tractor, "reliable_isobus"))

    def test_enhanced_field_allocation_integration(self):
        """Test guaranteed delivery integration with field allocation."""
        # Create field allocation scenario
        field_crdt = FieldAllocationCRDT("test_field", ["test_tractor"])
        field_crdt.claim("section_A1", "test_tractor")

        # Send allocation update with guaranteed delivery
        message_id = self.tractor.broadcast_field_allocation_reliable(
            field_crdt,
            requires_ack=True,
        )

        self.assertIsNotNone(message_id)

    def test_enhanced_emergency_stop_integration(self):
        """Test enhanced emergency stop with guaranteed delivery."""
        # Setup active systems
        self.tractor.start_engine()
        self.tractor.set_gps_position(40.0, -73.0)
        self.tractor.enable_auto_steer()
        self.tractor.add_waypoint(40.1, -73.1)
        self.tractor.enable_autonomous_mode()

        # Trigger emergency stop with guaranteed delivery
        callback = Mock()
        message_ids = self.tractor.emergency_stop_reliable(delivery_callback=callback)

        # Should broadcast to multiple recipients
        self.assertGreater(len(message_ids), 0)
        # Should use highest priority for safety
        for msg_id in message_ids:
            self.assertIsNotNone(msg_id)


if __name__ == "__main__":
    unittest.main()
