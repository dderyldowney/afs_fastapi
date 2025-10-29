from typing import Literal

from pydantic import BaseModel


class FieldSegment(BaseModel):
    segment_id: str
    coordinates: list[
        tuple[float, float]
    ]  # List of (latitude, longitude) tuples defining the segment boundary
    status: Literal["unassigned", "assigned", "completed"] = "unassigned"
    assigned_to_tractor_id: str | None = None
    last_updated: float  # Timestamp for conflict resolution (last-write-wins)
