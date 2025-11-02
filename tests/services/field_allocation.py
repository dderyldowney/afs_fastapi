"""CRDT for conflict-free field section allocation in agricultural fleets.

This module provides a Last-Writer-Wins (LWW) Register CRDT that uses
vector clocks for causal ordering to achieve deterministic, conflict-free
state synchronization for multi-tractor field operations.

Properties: Convergence, commutativity, associativity, idempotence.
"""

from __future__ import annotations

import time
from typing import Any

from afs_fastapi.services.synchronization import VectorClock


class FieldAllocationCRDT:
    """A state-based LWW-Register CRDT for field section allocation.

    Uses a hybrid approach of vector clocks for causality and LWW for
    concurrent updates to ensure deterministic conflict resolution.
    """

    def __init__(self, field_id: str, tractor_ids: list[str] | None = None) -> None:
        """Initialize the FieldAllocationCRDT."""
        self._field_id = field_id
        # State: {cell_id: {"owner": str, "timestamp": float, "vc": dict}}
        self._state: dict[str, dict[str, Any]] = {}
        self._vector_clock = VectorClock(tractor_ids if tractor_ids else [])

    def claim(self, cell_id: str, owner_id: str) -> None:
        """Claim a cell for a given owner."""
        if owner_id not in self._vector_clock.get_process_ids():
            self._vector_clock.add_process(owner_id)

        self._vector_clock.increment(owner_id)
        self._state[cell_id] = {
            "owner": owner_id,
            "timestamp": time.time(),
            "vc": self._vector_clock.to_dict(),
        }

    def owner_of(self, cell_id: str) -> str | None:
        """Get the current owner of a cell."""
        return self._state.get(cell_id, {}).get("owner")

    def merge(self, other: FieldAllocationCRDT) -> None:
        """Merge another CRDT replica into this one."""
        for cell_id, other_entry in other._state.items():
            local_entry = self._state.get(cell_id)

            if not local_entry:
                self._state[cell_id] = other_entry
                continue

            # Conflict resolution
            local_vc = VectorClock.from_dict(local_entry["vc"], list(local_entry["vc"].keys()))
            other_vc = VectorClock.from_dict(other_entry["vc"], list(other_entry["vc"].keys()))

            if local_vc.happens_before(other_vc):
                # Other is newer
                self._state[cell_id] = other_entry
            elif other_vc.happens_before(local_vc):
                # Local is newer, do nothing
                pass
            else:  # Concurrent update, use LWW tie-breaker
                if other_entry["timestamp"] > local_entry["timestamp"]:
                    self._state[cell_id] = other_entry
                elif other_entry["timestamp"] == local_entry["timestamp"]:
                    # Final tie-breaker: lexicographical sort of owner ID
                    if other_entry["owner"] > local_entry["owner"]:
                        self._state[cell_id] = other_entry

        # Merge vector clocks
        all_procs = set(self._vector_clock.get_process_ids()) | set(
            other._vector_clock.get_process_ids()
        )
        for proc in all_procs:
            max_time = max(
                self._vector_clock.get_time(proc) or 0,
                other._vector_clock.get_time(proc) or 0,
            )
            if proc not in self._vector_clock.get_process_ids():
                self._vector_clock.add_process(proc)
            self._vector_clock._clocks[proc] = max_time

    def serialize(self) -> dict[str, Any]:
        """Serialize the CRDT state into a dictionary."""
        return {
            "field_id": self._field_id,
            "state": self._state,
            "vector_clock": self._vector_clock.to_dict(),
        }

    @classmethod
    def deserialize(cls, payload: dict[str, Any]) -> FieldAllocationCRDT:
        """Create a CRDT instance from a serialized payload."""
        field_id = payload["field_id"]
        instance = cls(field_id)
        instance._state = payload["state"]
        instance._vector_clock = VectorClock.from_dict(
            payload["vector_clock"], list(payload["vector_clock"].keys())
        )
        return instance

    def assigned_sections(self, owner_id: str) -> set[str]:
        """Get all sections assigned to a specific owner."""
        return {cell_id for cell_id, data in self._state.items() if data.get("owner") == owner_id}

    def release(self, cell_id: str, owner_id: str) -> None:
        """Release a cell if the owner matches."""
        if self.owner_of(cell_id) == owner_id:
            if owner_id not in self._vector_clock.get_process_ids():
                self._vector_clock.add_process(owner_id)
            self._vector_clock.increment(owner_id)
            self._state[cell_id] = {
                "owner": None,
                "timestamp": time.time(),
                "vc": self._vector_clock.to_dict(),
            }
