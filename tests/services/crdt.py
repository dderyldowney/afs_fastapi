"""Conflict-Free Replicated Data Type (CRDT) implementations.

This module provides CRDTs for the AFS FastAPI agricultural robotics platform,
developed following Test-Driven Development (TDD) principles.

Agricultural Context:
CRDTs are fundamental for enabling robust, multi-tractor coordination in
environments with unreliable network connectivity, a common challenge in
rural agricultural settings. They allow for convergent, conflict-free state
synchronization without a central coordinator.
"""

from __future__ import annotations

from typing import Any


class GSet:
    """A Grow-only Set (G-Set) CRDT.

    This is a state-based CRDT where elements can only be added. It is the
    simplest CRDT and serves as a foundational data type for tracking
    monotonic events, such as which field sections have been harvested.

    The state is a set of elements, and the merge operation is a set union.
    """

    def __init__(self) -> None:
        """Initialize an empty G-Set."""
        self.payload: set[Any] = set()

    def add(self, item: Any) -> None:
        """Add an item to the set.

        This operation is idempotent.
        """
        self.payload.add(item)

    def merge(self, other: GSet) -> None:
        """Merge another G-Set into this one.

        The merge operation is a set union of the payloads.
        """
        self.payload.update(other.payload)
