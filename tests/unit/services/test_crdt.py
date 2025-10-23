"""Unit tests for CRDT implementations.

This module follows the Test-Driven Development (TDD) methodology to build
Conflict-Free Replicated Data Types (CRDTs) for the AFS FastAPI platform.

Agricultural Context:
CRDTs are essential for multi-tractor coordination in environments with
intermittent network connectivity, which is common in rural agricultural
settings. They allow tractors to independently update their local state
(e.g., which field sections have been harvested) and merge those states later
without conflicts, ensuring eventual consistency across the entire fleet.

This test suite begins with a G-Set (Grow-only Set), the simplest CRDT,
which will serve as the foundation for more complex agricultural data types.
"""

from __future__ import annotations

from afs_fastapi.services.crdt import GSet


class TestGSet:
    """Tests for the G-Set (Grow-only Set) CRDT."""

    def test_add_item_to_set(self) -> None:
        """Test that an item can be added to the G-Set.

        Agricultural Context:
        This represents the most basic operation for tracking completed
        tasks. For example, a tractor adds the ID of a field section
        to a set to mark it as 'harvested'. The set only ever grows.
        """
        # Arrange
        g_set: GSet[str] = GSet()
        g_set.add("FIELD_A_SECTION_01")

        # Assert
        assert "FIELD_A_SECTION_01" in g_set

    def test_merge_two_gsets(self) -> None:
        """Test that two G-Sets can be merged.

        Agricultural Context:
        This represents two tractors synchronizing their state. Tractor A
        harvests section 1, and Tractor B harvests section 2. When they
        come back into network range, they merge their logs. The resulting
        merged log should show that both sections 1 and 2 are harvested.
        The merge operation for a G-Set is a simple set union.
        """
        # Arrange
        g_set_tractor_a: GSet[str] = GSet()
        g_set_tractor_a.add("FIELD_A_SECTION_01")

        g_set_tractor_b: GSet[str] = GSet()
        g_set_tractor_b.add("FIELD_B_SECTION_07")

        # Act
        g_set_tractor_a.merge(g_set_tractor_b)

        # Assert
        assert "FIELD_A_SECTION_01" in g_set_tractor_a
        assert "FIELD_B_SECTION_07" in g_set_tractor_a

    def test_add_is_idempotent(self) -> None:
        """Test that adding the same item multiple times has no extra effect.

        Agricultural Context:
        In a distributed system with unreliable networks, a tractor might
        send the same "section harvested" message multiple times to ensure
        delivery. The receiving system must handle these duplicates gracefully.
        Idempotency ensures that adding "FIELD_A_SECTION_01" twice is the
        same as adding it once.
        """
        # Arrange
        g_set: GSet[str] = GSet()
        g_set.add("FIELD_A_SECTION_01")

        # Act
        g_set.add("FIELD_A_SECTION_01")  # Add the same item again

        # Assert
        assert "FIELD_A_SECTION_01" in g_set
        assert len(g_set) == 1

    def test_merge_is_idempotent(self) -> None:
        """Test that merging the same G-Set multiple times has no extra effect.

        Agricultural Context:
        If two tractors synchronize, and due to a network retry the same
        synchronization message is processed twice, the final state must be
        the same as if it were processed only once. Idempotency of merge
        guarantees this, preventing state corruption from duplicate messages.
        """
        # Arrange
        g_set_a = GSet[str]()
        g_set_a.add("FIELD_A_SECTION_01")

        g_set_b = GSet[str]()
        g_set_b.add("FIELD_B_SECTION_07")

        # Act
        g_set_a.merge(g_set_b)
        len_after_first_merge = len(g_set_a)

        g_set_a.merge(g_set_b)  # Merge the same set again

        # Assert
        assert len(g_set_a) == len_after_first_merge
        assert len(g_set_a) == 2
