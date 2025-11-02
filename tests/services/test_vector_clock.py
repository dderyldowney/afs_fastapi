"""
Test-First Development Example: Vector Clock for Multi-Tractor Synchronization

This module demonstrates the Red-Green-Refactor methodology applied to
distributed systems components in agricultural robotics. Vector clocks
provide the foundation for ordering events across multiple tractors
operating in the same field without requiring centralized coordination.

Agricultural Context:
- Multiple tractors must coordinate field operations (planting, harvesting)
- Network connectivity may be intermittent in rural areas
- Operations must be sequenced correctly even with communication delays
- Safety requires precise ordering of equipment movements
"""

import unittest

# Import VectorClock - now available after TDD Green phase completion
from afs_fastapi.services.synchronization import VectorClock


class TestVectorClock(unittest.TestCase):
    """
    Test suite for Vector Clock implementation using TDD methodology.

    Each test follows the Red-Green-Refactor pattern:
    1. Red: Write failing test that describes desired behavior
    2. Green: Implement minimal code to make test pass
    3. Refactor: Improve code quality while maintaining test coverage
    """

    def setUp(self):
        """
        Set up test fixtures for vector clock testing.

        Agricultural Context: Simulates a field with three tractors
        that need to coordinate their operations.
        """
        # VectorClock is now implemented (Green phase completed)

        self.tractor_ids = ["tractor_001", "tractor_002", "tractor_003"]
        self.clock = VectorClock(self.tractor_ids)

    def test_vector_clock_initialization(self):
        """
        RED PHASE TEST: Vector clock should initialize with zero values.

        Agricultural Context: When tractors start field operations,
        their logical clocks should begin at zero to establish
        a consistent baseline for event ordering.
        """
        # Test that clock initializes with all zeros
        for tractor_id in self.tractor_ids:
            self.assertEqual(
                self.clock.get_time(tractor_id), 0, f"Clock for {tractor_id} should initialize to 0"
            )

        # Test that clock knows about all tractors
        self.assertEqual(
            set(self.clock.get_process_ids()),
            set(self.tractor_ids),
            "Clock should track all tractor IDs",
        )

    def test_vector_clock_increment(self):
        """
        RED PHASE TEST: Vector clock should increment for local events.

        Agricultural Context: When a tractor performs an operation
        (e.g., starts planting a section), it increments its logical clock
        to establish ordering with other operations.
        """
        # Increment tractor_001's clock
        self.clock.increment("tractor_001")

        # Verify only tractor_001's time increased
        self.assertEqual(self.clock.get_time("tractor_001"), 1)
        self.assertEqual(self.clock.get_time("tractor_002"), 0)
        self.assertEqual(self.clock.get_time("tractor_003"), 0)

        # Multiple increments should work
        self.clock.increment("tractor_001")
        self.assertEqual(self.clock.get_time("tractor_001"), 2)

    def test_vector_clock_update_with_received_message(self):
        """
        RED PHASE TEST: Vector clock should update when receiving messages.

        Agricultural Context: When a tractor receives an ISOBUS message
        from another tractor (e.g., work completion status), it must
        update its clock to maintain causal ordering of field operations.
        """
        # Create a second clock representing another tractor's state
        other_clock = VectorClock(self.tractor_ids)
        other_clock.increment("tractor_002")  # Other tractor performs operation
        other_clock.increment("tractor_002")  # And another operation

        # Original clock receives message with other_clock's timestamp
        self.clock.update_with_received_message("tractor_001", other_clock)

        # Verify proper vector clock update rules:
        # 1. Receiving process increments its own clock
        self.assertEqual(self.clock.get_time("tractor_001"), 1)
        # 2. For each other process, take max of current and received time
        self.assertEqual(self.clock.get_time("tractor_002"), 2)
        self.assertEqual(self.clock.get_time("tractor_003"), 0)

    def test_vector_clock_comparison_concurrent_events(self):
        """
        RED PHASE TEST: Vector clocks should detect concurrent events.

        Agricultural Context: Two tractors working different field sections
        simultaneously create concurrent events. The system must detect
        this to avoid false ordering assumptions that could affect
        equipment coordination.
        """
        clock_a = VectorClock(self.tractor_ids)
        clock_b = VectorClock(self.tractor_ids)

        # Simulate concurrent operations
        clock_a.increment("tractor_001")  # Tractor 1 starts planting section A
        clock_b.increment("tractor_002")  # Tractor 2 starts planting section B

        # Neither event should be ordered before the other
        self.assertFalse(clock_a.happens_before(clock_b))
        self.assertFalse(clock_b.happens_before(clock_a))

        # Events should be detected as concurrent
        self.assertTrue(clock_a.is_concurrent_with(clock_b))

    def test_vector_clock_comparison_causal_ordering(self):
        """
        RED PHASE TEST: Vector clocks should detect causal relationships.

        Agricultural Context: If tractor A completes a field section and
        sends a message to tractor B, then tractor B's subsequent operations
        are causally related to A's completion. This ordering is critical
        for operations like coordinated harvesting or sequential planting.
        """
        clock_a = VectorClock(self.tractor_ids)
        clock_b = VectorClock(self.tractor_ids)

        # Tractor A performs operation
        clock_a.increment("tractor_001")

        # Tractor B receives message from A and performs operation
        clock_b.update_with_received_message("tractor_002", clock_a)

        # A's event should happen before B's event
        self.assertTrue(clock_a.happens_before(clock_b))
        self.assertFalse(clock_b.happens_before(clock_a))
        self.assertFalse(clock_a.is_concurrent_with(clock_b))

    def test_vector_clock_serialization(self):
        """
        RED PHASE TEST: Vector clocks should serialize for ISOBUS messages.

        Agricultural Context: Vector clock timestamps must be included
        in ISOBUS messages for distributed coordination. This requires
        efficient serialization that fits within ISO 11783 message
        size constraints.
        """
        # Set up clock state
        self.clock.increment("tractor_001")
        self.clock.increment("tractor_002")

        # Serialize to dictionary for JSON transmission
        serialized = self.clock.to_dict()

        # Verify serialization format
        expected = {"tractor_001": 1, "tractor_002": 1, "tractor_003": 0}
        self.assertEqual(serialized, expected)

        # Test deserialization
        new_clock = VectorClock.from_dict(serialized, self.tractor_ids)
        self.assertEqual(new_clock.to_dict(), serialized)

    def test_vector_clock_invalid_process_id(self):
        """
        RED PHASE TEST: Vector clock should handle invalid tractor IDs.

        Agricultural Context: Field operations must be robust against
        configuration errors, unknown equipment, or corrupted messages.
        The system should gracefully handle invalid tractor identifiers.
        """
        with self.assertRaises(ValueError) as context:
            self.clock.increment("unknown_tractor")

        self.assertIn("unknown_tractor", str(context.exception))
        self.assertIn("not found", str(context.exception).lower())

    def test_vector_clock_performance_constraints(self):
        """
        RED PHASE TEST: Vector clock operations should meet performance requirements.

        Agricultural Context: Tractor computers have limited processing power
        and operations must complete quickly to maintain real-time coordination.
        Vector clock operations should complete in sub-millisecond timeframes.
        """
        import time

        # Test increment performance
        start_time = time.perf_counter()
        for _ in range(1000):
            self.clock.increment("tractor_001")
        increment_time = time.perf_counter() - start_time

        # Should complete 1000 increments in less than 10ms
        self.assertLess(
            increment_time,
            0.01,
            "Vector clock increments too slow for agricultural real-time requirements",
        )

        # Test comparison performance
        other_clock = VectorClock(self.tractor_ids)
        other_clock.increment("tractor_002")

        start_time = time.perf_counter()
        for _ in range(1000):
            self.clock.happens_before(other_clock)
        comparison_time = time.perf_counter() - start_time

        # Should complete 1000 comparisons in less than 10ms
        self.assertLess(
            comparison_time,
            0.01,
            "Vector clock comparisons too slow for agricultural real-time requirements",
        )


class TestVectorClockEdgeCases(unittest.TestCase):
    """
    Edge case testing for vector clock robustness.

    Agricultural Context: Field operations encounter various edge cases
    including network failures, equipment restarts, and message corruption.
    The vector clock implementation must handle these gracefully.
    """

    def setUp(self):
        # VectorClock is now implemented (Green phase completed)

        self.tractor_ids = ["tractor_001", "tractor_002"]

    def test_empty_process_list(self):
        """
        RED PHASE TEST: Vector clock should handle empty process lists.

        Agricultural Context: System should gracefully handle configuration
        errors where no tractors are registered for field operations.
        """
        with self.assertRaises(ValueError) as context:
            VectorClock([])

        self.assertIn("empty", str(context.exception).lower())

    def test_duplicate_process_ids(self):
        """
        RED PHASE TEST: Vector clock should handle duplicate tractor IDs.

        Agricultural Context: Configuration errors might result in
        duplicate tractor registrations. System should detect and
        handle this gracefully.
        """
        duplicate_ids = ["tractor_001", "tractor_001", "tractor_002"]

        # Should either accept and deduplicate, or raise clear error
        try:
            clock = VectorClock(duplicate_ids)
            # If accepted, should have deduplicated
            unique_ids = clock.get_process_ids()
            self.assertEqual(len(unique_ids), 2)
            self.assertIn("tractor_001", unique_ids)
            self.assertIn("tractor_002", unique_ids)
        except ValueError as e:
            # If error raised, should be clear about duplication
            self.assertIn("duplicate", str(e).lower())

    def test_large_clock_values(self):
        """
        RED PHASE TEST: Vector clock should handle large timestamp values.

        Agricultural Context: Long-running field operations or high-frequency
        events could result in large clock values. System should handle
        these without integer overflow or performance degradation.
        """
        clock = VectorClock(self.tractor_ids)

        # Simulate many operations
        large_value = 1000000
        for _ in range(large_value):
            clock.increment("tractor_001")

        self.assertEqual(clock.get_time("tractor_001"), large_value)

        # Operations should still work correctly with large values
        other_clock = VectorClock(self.tractor_ids)
        other_clock.increment("tractor_002")

        # For proper causal ordering, other_clock should happen before a future state of clock
        future_clock = VectorClock(self.tractor_ids)
        future_clock.update_with_received_message("tractor_001", other_clock)
        future_clock.increment("tractor_001")  # Additional local event

        self.assertTrue(other_clock.happens_before(future_clock))


if __name__ == "__main__":
    unittest.main()


class TestVectorClockDynamicComposition(unittest.TestCase):
    """
    Dynamic team composition tests (robots joining/leaving the fleet).

    Agricultural Context: Fleet composition can change in the field as
    tractors enter/exit operation zones or recover from connectivity loss.
    Vector clocks must gracefully handle joining/leaving processes and adopt
    unknown processes encountered during synchronization.
    """

    def setUp(self):
        self.initial_ids = ["tractor_001", "tractor_002"]

    def test_add_process_and_increment(self):
        """Vector clock supports adding a new process at runtime."""
        clock = VectorClock(self.initial_ids)

        # Add a new tractor to the fleet
        clock.add_process("tractor_003")

        # New tractor appears with time 0 and can be incremented
        self.assertIn("tractor_003", set(clock.get_process_ids()))
        self.assertEqual(clock.get_time("tractor_003"), 0)

        clock.increment("tractor_003")
        self.assertEqual(clock.get_time("tractor_003"), 1)

    def test_remove_process(self):
        """Vector clock supports removing a process at runtime."""
        clock = VectorClock(["tractor_001", "tractor_002", "tractor_003"])

        # Remove a tractor leaving the operation
        clock.remove_process("tractor_003")

        self.assertNotIn("tractor_003", set(clock.get_process_ids()))

        # Removed tractor lookups should raise a clear error
        with self.assertRaises(ValueError):
            clock.get_time("tractor_003")

        # Serialization should not include removed tractor
        serialized = clock.to_dict()
        self.assertNotIn("tractor_003", serialized)

    def test_adopt_unknown_process_on_update(self):
        """
        Clock adopts unknown processes found in received messages and
        applies max-time rule before incrementing the receiver.
        """
        receiver = VectorClock(["tractor_001", "tractor_002"])
        sender = VectorClock(["tractor_001", "tractor_002", "tractor_004"])

        # New tractor performs an operation unknown to receiver
        sender.increment("tractor_004")

        # Receiver updates from sender and should adopt tractor_004
        receiver.update_with_received_message("tractor_001", sender)

        # Adopted with correct timestamp and receiver incremented
        self.assertIn("tractor_004", set(receiver.get_process_ids()))
        self.assertEqual(receiver.get_time("tractor_004"), 1)
        self.assertEqual(receiver.get_time("tractor_001"), 1)
