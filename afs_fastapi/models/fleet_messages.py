from typing import Any, Literal

from pydantic import BaseModel


class TractorStatusMessage(BaseModel):
    tractor_id: str
    timestamp: float
    gps_location: dict[str, float]
    speed: float
    engine_on: bool
    implement_attached: bool
    implement_position: Literal["up", "down", "unknown"]
    # Add more status fields as needed


class CommandMessage(BaseModel):
    command_id: str
    target_tractor_id: str
    command_type: Literal[
        "start_engine",
        "stop_engine",
        "set_speed",
        "assign_segment",
        "release_segment",
        "complete_segment",
    ]
    payload: dict[str, Any] = {}
    # Add more command types and payload details as needed


class SynchronizationMessage(BaseModel):
    sync_id: str
    sender_tractor_id: str
    timestamp: float
    data: dict[str, Any] = {}
    # For example, could contain CRDT state updates or other synchronization data


class FleetBroadcastMessage(BaseModel):
    message_id: str
    sender_tractor_id: str
    timestamp: float
    message_type: Literal["alert", "info", "status_request"]
    payload: dict[str, Any] = {}
    # General broadcast messages for the entire fleet
