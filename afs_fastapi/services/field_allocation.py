"""CRDT Implementation for Field Section Allocation.

This module implements a Conflict-Free Replicated Data Type (CRDT) using
Last-Writer-Wins (LWW) semantics with vector clock causality to coordinate
field section allocation across multiple tractors under intermittent connectivity.

Agricultural Context
--------------------
- Multiple tractors (heterogeneous fleet) claim/release sections in a field.
- Must converge without central coordination and tolerate network partitions.
- Safety-critical operations require deterministic, auditable resolution rules.
- Implements ISO 11783 compatible serialization for ISOBUS messaging.

CRDT Design
-----------
- Type: LWW-Register with vector clock causality
- Conflict Resolution: Vector clock → LWW timestamp → lexicographic owner_id
- Data Structure: Each section stores (owner_id, vector_clock, lww_timestamp)
- Properties: Convergence, commutativity, associativity, idempotence
"""

from __future__ import annotations

import time
from typing import Any

from afs_fastapi.services.synchronization import VectorClock


class FieldAllocationCRDT:
    """Field allocation CRDT with LWW-Register and vector clock causality.

    Implements an eventually consistent, conflict-free replica that assigns
    field sections (cells) to equipment owners (tractors) with deterministic
    conflict resolution and efficient serialization for ISOBUS constraints.

    Parameters
    ----------
    field_id : str
        Unique identifier for the field (e.g., "field_001").
    tractor_ids : list[str], optional
        Initial list of tractor IDs for vector clock initialization.
        If not provided, tractors are added dynamically as they appear.

    Notes
    -----
    - CRDT properties: convergence, commutativity, associativity, idempotence.
    - Conflict resolution: vector clock → LWW timestamp → lexicographic owner_id.
    - Each section stores: (owner_id, vector_clock, lww_timestamp).
    - See tests in ``tests/unit/services/test_field_allocation_crdt.py``.
    """

    def __init__(self, field_id: str, tractor_ids: list[str] | None = None) -> None:
        self._field_id = field_id

        # Initialize vector clock for causal ordering
        self._vector_clock = VectorClock(tractor_ids or ["system"])

        # Section allocation state: section_id -> (owner_id, vector_clock, lww_timestamp)
        # None owner_id indicates unallocated section
        self._sections: dict[str, tuple[str | None, VectorClock, float]] = {}

    # Mutation API
    def claim(self, section_id: str, owner_id: str) -> None:
        """Claim a field section for an owner.

        This operation creates a CRDT entry that claims the section for the
        specified owner. The claim includes vector clock causality and LWW
        timestamp for deterministic conflict resolution.

        Parameters
        ----------
        section_id : str
            Section (cell) identifier within the field grid.
        owner_id : str
            Equipment/tractor identifier claiming the section.

        Agricultural Context
        --------------------
        When a tractor begins work on a field section, it claims that section
        to prevent conflicts with other tractors. The CRDT ensures consistent
        allocation even if multiple tractors attempt to claim the same section
        under network partitions.
        """
        # Ensure the claiming tractor is known to our vector clock
        if owner_id not in self._vector_clock.get_process_ids():
            self._vector_clock.add_process(owner_id)

        # Increment vector clock for this local event
        self._vector_clock.increment(owner_id)

        # Create section entry with current state
        current_time = time.time()
        section_clock = VectorClock(self._vector_clock.get_process_ids())

        # Copy current vector clock state
        for process_id in self._vector_clock.get_process_ids():
            section_clock_time = self._vector_clock.get_time(process_id)
            for _ in range(section_clock_time):
                section_clock.increment(process_id)

        # Store the allocation entry
        self._sections[section_id] = (owner_id, section_clock, current_time)

    def release(self, section_id: str, owner_id: str) -> None:
        """Release a previously claimed section.

        This operation creates a CRDT entry that releases the section, setting
        the owner to None. The release includes vector clock causality and LWW
        timestamp for deterministic conflict resolution.

        Parameters
        ----------
        section_id : str
            Section (cell) identifier within the field grid.
        owner_id : str
            Equipment/tractor identifier releasing the section.

        Agricultural Context
        --------------------
        When a tractor completes work on a field section, it releases that
        section to make it available for other operations. The CRDT ensures
        consistent release tracking even under network partitions.
        """
        # Ensure the releasing tractor is known to our vector clock
        if owner_id not in self._vector_clock.get_process_ids():
            self._vector_clock.add_process(owner_id)

        # Check if the owner_id matches the current owner before releasing
        current_owner, _, _ = self._sections.get(section_id, (None, None, None))
        if current_owner != owner_id:
            # If the current owner is different, or section is not claimed, do not release
            # This ensures a tractor cannot release a section it doesn't own.
            return

        # Increment vector clock for this local event
        self._vector_clock.increment(owner_id)

        # Create section entry with released state (None owner)
        current_time = time.time()
        section_clock = VectorClock(self._vector_clock.get_process_ids())

        # Copy current vector clock state
        for process_id in self._vector_clock.get_process_ids():
            section_clock_time = self._vector_clock.get_time(process_id)
            for _ in range(section_clock_time):
                section_clock.increment(process_id)

        # Store the release entry (None indicates released/unallocated)
        self._sections[section_id] = (None, section_clock, current_time)

    def merge(self, other: FieldAllocationCRDT) -> None:
        """Merge another replica into this one deterministically.

        Implements CRDT merge semantics with deterministic conflict resolution:
        1. Vector clock causality (happens-before relationship)
        2. LWW timestamp comparison for concurrent events
        3. Lexicographic owner_id comparison for tie-breaking

        Parameters
        ----------
        other : FieldAllocationCRDT
            Another replica of the same field CRDT.

        Agricultural Context
        --------------------
        When tractors synchronize their field allocation state, this merge
        ensures deterministic convergence. Critical for safety as all tractors
        must agree on which sections are allocated to which equipment.
        """
        if self._field_id != other._field_id:
            msg = f"Cannot merge different fields: {self._field_id} != {other._field_id}"
            raise ValueError(msg)

        # Merge vector clocks deterministically (take max of each process time)
        for process_id in other._vector_clock.get_process_ids():
            if process_id not in self._vector_clock.get_process_ids():
                self._vector_clock.add_process(process_id)

        # Update vector clock by taking max of each process time (idempotent merge)
        for process_id in self._vector_clock.get_process_ids():
            our_time = self._vector_clock.get_time(process_id)
            other_time = (
                other._vector_clock.get_time(process_id)
                if process_id in other._vector_clock.get_process_ids()
                else 0
            )
            max_time = max(our_time, other_time)

            # Set clock to max time without incrementing
            self._vector_clock._clocks[process_id] = max_time

        # Merge section allocations using deterministic conflict resolution
        for section_id, (other_owner, other_clock, other_timestamp) in other._sections.items():
            if section_id not in self._sections:
                # We don't have this section, adopt their allocation
                self._sections[section_id] = (other_owner, other_clock, other_timestamp)
            else:
                # We both have this section, apply conflict resolution
                our_owner, our_clock, our_timestamp = self._sections[section_id]

                # Deterministic conflict resolution hierarchy
                winner_entry = self._resolve_conflict(
                    (our_owner, our_clock, our_timestamp),
                    (other_owner, other_clock, other_timestamp),
                )

                self._sections[section_id] = winner_entry

    def _resolve_conflict(
        self,
        our_entry: tuple[str | None, VectorClock, float],
        other_entry: tuple[str | None, VectorClock, float],
    ) -> tuple[str | None, VectorClock, float]:
        """Resolve conflict between two section entries deterministically.

        Conflict resolution hierarchy:
        1. Vector clock causality (happens-before)
        2. LWW timestamp (later wins)
        3. Lexicographic owner_id comparison (deterministic tie-break)
        """
        our_owner, our_clock, our_timestamp = our_entry
        other_owner, other_clock, other_timestamp = other_entry

        # Rule 1: Vector clock causality
        if our_clock.happens_before(other_clock):
            # Their event causally follows ours
            return other_entry
        elif other_clock.happens_before(our_clock):
            # Our event causally follows theirs
            return our_entry

        # Rule 2: Concurrent events - use LWW timestamp
        if our_timestamp < other_timestamp:
            # Their timestamp is later
            return other_entry
        elif our_timestamp > other_timestamp:
            # Our timestamp is later
            return our_entry

        # Rule 3: Same timestamp - lexicographic comparison for determinism
        our_owner_str = our_owner or ""
        other_owner_str = other_owner or ""

        if our_owner_str <= other_owner_str:
            return our_entry
        else:
            return other_entry

    # Query API
    def owner_of(self, section_id: str) -> str | None:
        """Return the current owner of a section, if any.

        Parameters
        ----------
        section_id : str
            Section (cell) identifier within the field grid.

        Returns
        -------
        str | None
            Owner identifier or None if unassigned.

        Agricultural Context
        --------------------
        Used by tractors to check if a field section is available before
        beginning work. Critical for preventing conflicts and ensuring
        coordinated field operations.
        """
        if section_id not in self._sections:
            return None

        owner, _, _ = self._sections[section_id]
        return owner

    def assigned_sections(self, owner_id: str) -> set[str]:
        """Return the set of sections assigned to an owner.

        Parameters
        ----------
        owner_id : str
            Equipment/tractor identifier.

        Returns
        -------
        set of str
            Sections owned by the specified owner.

        Agricultural Context
        --------------------
        Used by fleet management systems to track which sections each
        tractor is responsible for, enabling efficient work coordination
        and progress monitoring.
        """
        assigned = set()
        for section_id, (owner, _, _) in self._sections.items():
            if owner == owner_id:
                assigned.add(section_id)
        return assigned

    # Serialization API
    def serialize(self) -> dict[str, Any]:
        """Serialize CRDT state into a compact structure.

        Returns
        -------
        dict
            Compact representation suitable for ISOBUS message constraints.
            Includes field_id, vector_clock, and section allocations with
            causal context for proper merge operations.

        Agricultural Context
        --------------------
        Serialized data is transmitted via ISOBUS messages between tractors
        for distributed coordination. Must be compact due to ISO 11783
        message size constraints while preserving causal ordering information.
        """
        # Serialize section allocations
        sections_data = {}
        for section_id, (owner, clock, timestamp) in self._sections.items():
            sections_data[section_id] = {
                "owner": owner,
                "vector_clock": clock.to_dict(),
                "timestamp": timestamp,
            }

        return {
            "field_id": self._field_id,
            "vector_clock": self._vector_clock.to_dict(),
            "sections": sections_data,
        }

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> FieldAllocationCRDT:
        """Create a replica from serialized data.

        Parameters
        ----------
        data : dict
            Serialized CRDT state containing field_id, vector_clock, and sections.

        Returns
        -------
        FieldAllocationCRDT
            New replica instance initialized from serialized data.

        Agricultural Context
        --------------------
        Used to reconstruct CRDT state from received ISOBUS messages,
        enabling tractors to synchronize their field allocation knowledge
        after network partitions or when joining ongoing operations.
        """
        field_id = data["field_id"]
        vector_clock_data = data["vector_clock"]
        sections_data = data["sections"]

        # Reconstruct vector clock
        process_ids = list(vector_clock_data.keys())
        crdt = cls(field_id, process_ids)
        crdt._vector_clock = VectorClock.from_dict(vector_clock_data, process_ids)

        # Reconstruct section allocations
        for section_id, section_data in sections_data.items():
            owner = section_data["owner"]
            clock_data = section_data["vector_clock"]
            timestamp = section_data["timestamp"]

            # Reconstruct section vector clock
            section_process_ids = list(clock_data.keys())
            section_clock = VectorClock.from_dict(clock_data, section_process_ids)

            crdt._sections[section_id] = (owner, section_clock, timestamp)

        return crdt
