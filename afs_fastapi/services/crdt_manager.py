import time

from ..models.field_segment import FieldSegment


class FieldAllocationCRDT:
    """
    An Operation-based CRDT for managing field segment allocations.
    Uses a last-write-wins strategy for conflict resolution.
    """

    def __init__(self) -> None:
        self._segments: dict[str, FieldSegment] = {}

    def add_segment(self, segment: FieldSegment) -> None:
        """
        Adds a new field segment to the CRDT.
        """
        if segment.segment_id in self._segments:
            # Only update if the new segment is more recent
            if segment.last_updated > self._segments[segment.segment_id].last_updated:
                self._segments[segment.segment_id] = segment
        else:
            self._segments[segment.segment_id] = segment

    def assign_segment(self, segment_id: str, tractor_id: str) -> FieldSegment | None:
        """
        Assigns a field segment to a tractor.
        Returns the updated FieldSegment if successful, None otherwise.
        """
        if segment_id not in self._segments:
            return None

        segment = self._segments[segment_id]
        if segment.status == "unassigned" or segment.assigned_to_tractor_id == tractor_id:
            segment.status = "assigned"
            segment.assigned_to_tractor_id = tractor_id
            segment.last_updated = time.time()
            self._segments[segment_id] = segment
            return segment
        return None  # Segment already assigned to another tractor

    def release_segment(self, segment_id: str, tractor_id: str) -> FieldSegment | None:
        """
        Releases a field segment from a tractor.
        Returns the updated FieldSegment if successful, None otherwise.
        """
        if segment_id not in self._segments:
            return None

        segment = self._segments[segment_id]
        if segment.status == "assigned" and segment.assigned_to_tractor_id == tractor_id:
            segment.status = "unassigned"
            segment.assigned_to_tractor_id = None
            segment.last_updated = time.time()
            self._segments[segment_id] = segment
            return segment
        return None  # Segment not assigned to this tractor or already unassigned

    def complete_segment(self, segment_id: str, tractor_id: str) -> FieldSegment | None:
        """
        Marks a field segment as completed by a tractor.
        Returns the updated FieldSegment if successful, None otherwise.
        """
        if segment_id not in self._segments:
            return None

        segment = self._segments[segment_id]
        if segment.status == "assigned" and segment.assigned_to_tractor_id == tractor_id:
            segment.status = "completed"
            segment.assigned_to_tractor_id = None  # No longer assigned after completion
            segment.last_updated = time.time()
            self._segments[segment_id] = segment
            return segment
        return None  # Segment not assigned to this tractor or already completed/unassigned

    def get_allocated_segments(self, tractor_id: str) -> list[FieldSegment]:
        """
        Returns a list of segments currently allocated to a specific tractor.
        """
        return [
            s
            for s in self._segments.values()
            if s.assigned_to_tractor_id == tractor_id and s.status == "assigned"
        ]

    def get_unallocated_segments(self) -> list[FieldSegment]:
        """
        Returns a list of segments not currently allocated.
        """
        return [s for s in self._segments.values() if s.status == "unassigned"]

    def get_completed_segments(self) -> list[FieldSegment]:
        """
        Returns a list of segments that have been completed.
        """
        return [s for s in self._segments.values() if s.status == "completed"]

    def get_segment_by_id(self, segment_id: str) -> FieldSegment | None:
        """
        Returns a specific field segment by its ID.
        """
        return self._segments.get(segment_id)

    def merge(self, other_crdt: "FieldAllocationCRDT") -> None:
        """
        Merges the state of another FieldAllocationCRDT into this one.
        Uses a last-write-wins strategy for conflicts on the same segment_id.
        """
        for segment_id, other_segment in other_crdt._segments.items():
            if segment_id not in self._segments:
                self._segments[segment_id] = other_segment
            else:
                current_segment = self._segments[segment_id]
                if other_segment.last_updated > current_segment.last_updated:
                    self._segments[segment_id] = other_segment

    def get_state(self) -> dict[str, FieldSegment]:
        """
        Returns the current state of the CRDT (all segments).
        """
        return self._segments
