"""
Fleet Coordination API Endpoints

Provides RESTful API access to multi-tractor fleet coordination services,
leveraging the sophisticated FleetCoordinationEngine for agricultural operations.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from afs_fastapi.services.field_allocation import FieldAllocationCRDT
from afs_fastapi.services.fleet import TractorState

router = APIRouter(prefix="/fleet", tags=["Fleet Coordination"])


# Simple fleet management registry for API demo
# In production, this would be backed by database and proper fleet management
class SimpleFleetManager:
    """Simple fleet management for API demonstration."""

    def __init__(self):
        self.tractors: dict[str, dict[str, Any]] = {}
        self.emergency_mode_active: bool = False
        self.active_operations: list[str] = []

    def add_tractor(self, tractor_id: str, make: str, model: str, year: int):
        """Add a tractor to the fleet."""
        self.tractors[tractor_id] = {
            "tractor_id": tractor_id,
            "make": make,
            "model": model,
            "year": year,
            "state": TractorState.IDLE,
            "assigned_field": None,
            "last_heartbeat": None,
            "coordination_active": True,
        }

    def get_connected_tractors(self) -> list[str]:
        """Get list of connected tractor IDs."""
        return [
            tid
            for tid, tractor in self.tractors.items()
            if tractor["state"] != TractorState.DISCONNECTED
        ]

    def get_fleet_state(self) -> str:
        """Get overall fleet state."""
        if self.emergency_mode_active:
            return "EMERGENCY"
        if any(t["state"] == TractorState.WORKING for t in self.tractors.values()):
            return "WORKING"
        if any(t["state"] == TractorState.SYNCHRONIZING for t in self.tractors.values()):
            return "SYNCHRONIZING"
        return "IDLE"

    def get_active_operations(self) -> list[str]:
        """Get list of active operations."""
        return self.active_operations.copy()

    def start_coordinated_operation(
        self, operation_type: str, field_id: str, tractor_ids: list[str], priority: str
    ) -> str:
        """Start a coordinated operation."""
        operation_id = f"OP_{operation_type}_{field_id}_{len(self.active_operations)}"
        self.active_operations.append(operation_id)

        # Update tractor states
        for tractor_id in tractor_ids:
            if tractor_id in self.tractors:
                self.tractors[tractor_id]["state"] = TractorState.WORKING
                self.tractors[tractor_id]["assigned_field"] = field_id

        return operation_id

    def remove_tractor(self, tractor_id: str):
        """Remove a tractor from the fleet."""
        if tractor_id in self.tractors:
            del self.tractors[tractor_id]


# Global fleet manager instance
_fleet_manager = SimpleFleetManager()


class TractorInfo(BaseModel):
    """Tractor information for fleet operations."""

    tractor_id: str = Field(..., description="Unique tractor identifier")
    make: str = Field(..., description="Tractor manufacturer")
    model: str = Field(..., description="Tractor model")
    year: int = Field(..., description="Manufacturing year")
    current_field: str | None = Field(None, description="Current field assignment")


class FleetStatus(BaseModel):
    """Fleet operational status response."""

    total_tractors: int = Field(..., description="Total number of tractors in fleet")
    active_tractors: int = Field(..., description="Number of active tractors")
    connected_tractors: list[str] = Field(..., description="List of connected tractor IDs")
    fleet_state: str = Field(..., description="Overall fleet coordination state")
    current_operations: list[str] = Field(..., description="Active field operations")
    emergency_status: bool = Field(..., description="Fleet emergency status")


class TractorStatusInFleet(BaseModel):
    """Individual tractor status within fleet context."""

    tractor_id: str = Field(..., description="Tractor identifier")
    state: str = Field(..., description="Current tractor state")
    assigned_field: str | None = Field(None, description="Assigned field ID")
    work_allocation: dict[str, float] | None = Field(None, description="Work area allocation")
    last_heartbeat: str | None = Field(None, description="Last communication timestamp")
    coordination_active: bool = Field(..., description="Fleet coordination status")


class FieldOperationRequest(BaseModel):
    """Field operation coordination request."""

    operation_type: str = Field(
        ..., description="Type of operation: tillage, planting, spraying, harvesting"
    )
    field_id: str = Field(..., description="Target field identifier")
    tractor_ids: list[str] = Field(..., description="Tractors to assign to operation")
    priority: str = Field("medium", description="Operation priority: low, medium, high")
    estimated_duration: float | None = Field(
        None, description="Estimated operation duration in hours"
    )


class CoordinationCommand(BaseModel):
    """Fleet coordination command."""

    command: str = Field(
        ..., description="Coordination command: start, stop, pause, resume, emergency_stop"
    )
    target_tractors: list[str] | None = Field(None, description="Target tractors (all if None)")
    parameters: dict[str, str] | None = Field(None, description="Additional command parameters")


@router.get("/status", response_model=FleetStatus)
async def get_fleet_status() -> FleetStatus:
    """Get comprehensive fleet coordination status."""

    connected_tractors = _fleet_manager.get_connected_tractors()
    fleet_state = _fleet_manager.get_fleet_state()

    return FleetStatus(
        total_tractors=len(_fleet_manager.tractors),
        active_tractors=len(
            [t for t in _fleet_manager.tractors.values() if t["state"] != TractorState.DISCONNECTED]
        ),
        connected_tractors=connected_tractors,
        fleet_state=fleet_state,
        current_operations=_fleet_manager.get_active_operations(),
        emergency_status=_fleet_manager.emergency_mode_active,
    )


@router.post("/tractors/{tractor_id}/register")
async def register_tractor_to_fleet(tractor_id: str, tractor_info: TractorInfo) -> dict[str, str]:
    """Register a tractor with the fleet coordination system."""

    try:
        # Register tractor with the fleet manager
        _fleet_manager.add_tractor(
            tractor_id=tractor_id,
            make=tractor_info.make,
            model=tractor_info.model,
            year=tractor_info.year,
        )

        return {
            "message": f"Tractor {tractor_id} registered with fleet successfully",
            "tractor_id": tractor_id,
            "fleet_status": "registered",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register tractor with fleet: {str(e)}",
        ) from e


@router.get("/tractors", response_model=list[TractorStatusInFleet])
async def get_fleet_tractors() -> list[TractorStatusInFleet]:
    """Get status of all tractors in the fleet."""

    tractor_statuses = []

    for tractor_id, tractor in _fleet_manager.tractors.items():
        tractor_statuses.append(
            TractorStatusInFleet(
                tractor_id=tractor_id,
                state=tractor["state"].value,
                assigned_field=tractor["assigned_field"],
                work_allocation=None,  # Not implemented in simple manager
                last_heartbeat=(
                    tractor["last_heartbeat"].isoformat() if tractor["last_heartbeat"] else None
                ),
                coordination_active=tractor["coordination_active"],
            )
        )

    return tractor_statuses


@router.get("/tractors/{tractor_id}/status", response_model=TractorStatusInFleet)
async def get_tractor_fleet_status(tractor_id: str) -> TractorStatusInFleet:
    """Get specific tractor status within fleet context."""

    if tractor_id not in _fleet_manager.tractors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Tractor {tractor_id} not found in fleet"
        )

    tractor = _fleet_manager.tractors[tractor_id]

    return TractorStatusInFleet(
        tractor_id=tractor_id,
        state=tractor["state"].value,
        assigned_field=tractor["assigned_field"],
        work_allocation=None,  # Not implemented in simple manager
        last_heartbeat=tractor["last_heartbeat"].isoformat() if tractor["last_heartbeat"] else None,
        coordination_active=tractor["coordination_active"],
    )


@router.post("/operations/start")
async def start_field_operation(request: FieldOperationRequest) -> dict[str, str]:
    """Start coordinated field operation with specified tractors."""

    try:
        # Validate that all requested tractors are available
        for tractor_id in request.tractor_ids:
            if tractor_id not in _fleet_manager.tractors:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tractor {tractor_id} not found in fleet",
                )

            tractor = _fleet_manager.tractors[tractor_id]
            if tractor["state"] not in [TractorState.IDLE, TractorState.SYNCHRONIZING]:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Tractor {tractor_id} is not available (current state: {tractor['state'].value})",
                )

        # Start the coordinated operation
        operation_id = _fleet_manager.start_coordinated_operation(
            operation_type=request.operation_type,
            field_id=request.field_id,
            tractor_ids=request.tractor_ids,
            priority=request.priority,
        )

        return {
            "message": "Field operation started successfully",
            "operation_id": operation_id,
            "operation_type": request.operation_type,
            "field_id": request.field_id,
            "assigned_tractors": str(len(request.tractor_ids)),
        }

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start field operation: {str(e)}",
        ) from e


@router.post("/coordination/command")
async def send_coordination_command(request: CoordinationCommand) -> dict[str, str]:
    """Send coordination command to fleet or specific tractors."""

    try:
        target_tractors = (
            request.target_tractors
            if request.target_tractors
            else list(_fleet_manager.tractors.keys())
        )

        # Validate target tractors exist
        for tractor_id in target_tractors:
            if tractor_id not in _fleet_manager.tractors:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tractor {tractor_id} not found in fleet",
                )

        # Execute coordination command (simplified implementation)
        if request.command == "start":
            for tractor_id in target_tractors:
                _fleet_manager.tractors[tractor_id]["state"] = TractorState.SYNCHRONIZING
            result = "Coordination started"
        elif request.command == "stop":
            for tractor_id in target_tractors:
                _fleet_manager.tractors[tractor_id]["state"] = TractorState.IDLE
            result = "Coordination stopped"
        elif request.command == "pause":
            # Implementation would pause current operations
            result = "Coordination paused"
        elif request.command == "resume":
            # Implementation would resume paused operations
            result = "Coordination resumed"
        elif request.command == "emergency_stop":
            _fleet_manager.emergency_mode_active = True
            for tractor_id in target_tractors:
                _fleet_manager.tractors[tractor_id]["state"] = TractorState.EMERGENCY_STOP
            result = "Emergency stop activated"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown coordination command: {request.command}. Available: start, stop, pause, resume, emergency_stop",
            )

        return {
            "message": f"Coordination command '{request.command}' executed successfully",
            "command": request.command,
            "target_tractors": str(len(target_tractors)),
            "result": str(result),
        }

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute coordination command: {str(e)}",
        ) from e


@router.get("/field-allocation/{field_id}")
async def get_field_allocation(field_id: str) -> dict[str, Any]:
    """Get field work allocation status for conflict-free coordination."""

    try:
        # Create or get field allocation CRDT
        field_allocation = FieldAllocationCRDT(field_id=field_id)

        # Get allocation data using available methods
        allocation_data = field_allocation.serialize()

        # Calculate allocated sections by checking all tractors
        all_tractors = _fleet_manager.get_connected_tractors()
        allocated_sections: list[str] = []
        for tractor_id in all_tractors:
            sections = field_allocation.assigned_sections(tractor_id)
            allocated_sections.extend(sections)

        # For demo purposes, simulate available sections
        total_sections = 100  # Simulate 100 sections in a field
        available_sections = [
            f"section_{i}"
            for i in range(total_sections)
            if f"section_{i}" not in allocated_sections
        ]

        return {
            "field_id": field_id,
            "allocation_status": allocation_data,
            "allocated_sections": allocated_sections,
            "available_sections": available_sections[:10],  # Limit to first 10 for demo
            "total_sections": total_sections,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get field allocation: {str(e)}",
        ) from e


@router.post("/field-allocation/{field_id}/allocate")
async def allocate_field_section(field_id: str, tractor_id: str, section_id: str) -> dict[str, str]:
    """Allocate a field section to a specific tractor using CRDT conflict resolution."""

    try:
        if tractor_id not in _fleet_manager.tractors:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tractor {tractor_id} not found in fleet",
            )

        # Create or get field allocation CRDT
        field_allocation = FieldAllocationCRDT(field_id=field_id)

        # Check if section is already allocated
        current_owner = field_allocation.owner_of(section_id)
        if current_owner is not None and current_owner != tractor_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Section {section_id} is already allocated to {current_owner}",
            )

        # Claim the section using CRDT
        field_allocation.claim(section_id, tractor_id)

        return {
            "message": "Field section allocated successfully",
            "field_id": field_id,
            "section_id": section_id,
            "allocated_to": tractor_id,
        }

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to allocate field section: {str(e)}",
        ) from e


@router.delete("/tractors/{tractor_id}")
async def remove_tractor_from_fleet(tractor_id: str) -> dict[str, str]:
    """Remove a tractor from the fleet coordination system."""

    if tractor_id not in _fleet_manager.tractors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Tractor {tractor_id} not found in fleet"
        )

    try:
        _fleet_manager.remove_tractor(tractor_id)

        return {
            "message": f"Tractor {tractor_id} removed from fleet successfully",
            "tractor_id": tractor_id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove tractor from fleet: {str(e)}",
        ) from e
