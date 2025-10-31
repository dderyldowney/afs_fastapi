"""
Equipment Management API Endpoints

Provides RESTful API access to agricultural equipment control and monitoring,
leveraging the sophisticated FarmTractor class and equipment infrastructure.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from afs_fastapi.equipment.farm_tractors import FarmTractor

router = APIRouter(prefix="/equipment", tags=["Equipment Management"])

# Global equipment registry for demo/development
# In production, this would be backed by database
_equipment_registry: dict[str, FarmTractor] = {}


class EquipmentStatus(BaseModel):
    """Equipment operational status response model."""

    equipment_id: str = Field(..., description="Unique equipment identifier")
    equipment_type: str = Field(..., description="Type of agricultural equipment")
    make: str = Field(..., description="Equipment manufacturer")
    model: str = Field(..., description="Equipment model number")
    year: int = Field(..., description="Manufacturing year")
    manual_url: str | None = Field(None, description="URL to operator manual")
    isobus_address: int = Field(..., description="ISOBUS device address")
    field_mode: str = Field(..., description="Current field operation mode")
    safety_level: str = Field(..., description="Current safety level")

    # Engine status
    engine_on: bool = Field(..., description="Engine operational status")
    engine_rpm: int = Field(..., description="Current engine RPM")
    engine_temp: float = Field(..., description="Engine temperature (°F)")
    fuel_level: float = Field(..., description="Fuel level percentage (0-100)")

    # Movement status
    speed: int = Field(..., description="Current speed in MPH")
    ground_speed: float = Field(..., description="Actual ground speed")
    gear: int = Field(..., description="Current transmission gear")
    heading: float = Field(..., description="Current heading in degrees")

    # GPS position
    gps_latitude: float | None = Field(None, description="Current GPS latitude")
    gps_longitude: float | None = Field(None, description="Current GPS longitude")

    # Implement status
    implement_position: str = Field(..., description="Implement position (RAISED/LOWERED)")
    implement_depth: float = Field(..., description="Current working depth (inches)")
    implement_width: float = Field(..., description="Current working width (feet)")
    power_takeoff: bool = Field(..., description="Power Take-Off engagement status")
    hydraulic_pressure: float = Field(..., description="Hydraulic system pressure (PSI)")
    hydraulic_flow: float = Field(..., description="Hydraulic flow rate (GPM)")

    # Field operations
    work_rate: float = Field(..., description="Current work rate (acres/hour)")
    area_covered: float = Field(..., description="Total area covered (acres)")
    wheel_slip: float = Field(..., description="Wheel slip percentage")
    draft_load: float = Field(..., description="Draft load (lbs)")

    # Safety systems
    emergency_stop_active: bool = Field(..., description="Emergency stop system status")
    autonomous_mode: bool = Field(..., description="Autonomous operation mode")
    auto_steer_enabled: bool = Field(..., description="Auto-steering system status")
    obstacle_detection: bool = Field(..., description="Obstacle detection system status")
    safety_system_active: bool = Field(..., description="Overall safety system status")


class EngineControlRequest(BaseModel):
    """Engine control command request."""

    action: str = Field(..., description="Engine action: start, stop")


class MovementControlRequest(BaseModel):
    """Movement control command request."""

    action: str = Field(..., description="Movement action: accelerate, brake")
    increase: int | None = Field(None, description="Speed increase for accelerate action")
    decrease: int | None = Field(None, description="Speed decrease for brake action")


class ImplementControlRequest(BaseModel):
    """Implement control command request."""

    action: str = Field(
        ..., description="Implement action: raise, lower, engage_pto, disengage_pto"
    )
    depth: float | None = Field(6.0, description="Working depth in inches for lower action")


class SafetyControlRequest(BaseModel):
    """Safety system control request."""

    action: str = Field(
        ...,
        description="Safety action: emergency_stop, reset_emergency, enable_autonomous, disable_autonomous",
    )


@router.get("/", response_model=list[str])
async def list_equipment() -> list[str]:
    """List all registered equipment IDs."""
    return list(_equipment_registry.keys())


@router.post("/{equipment_id}/register")
async def register_equipment(
    equipment_id: str,
    make: str = "John Deere",
    model: str = "8RX-410",
    year: int = 2024,
    manual_url: str | None = None,
) -> dict[str, str | int]:
    """Register new agricultural equipment in the system."""

    if equipment_id in _equipment_registry:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Equipment {equipment_id} already registered",
        )

    # Create new FarmTractor instance with specified parameters
    tractor = FarmTractor(make=make, model=model, year=year, manual_url=manual_url)

    _equipment_registry[equipment_id] = tractor

    return {
        "message": f"Equipment {equipment_id} registered successfully",
        "equipment_id": equipment_id,
        "type": "FarmTractor",
        "make": make,
        "model": model,
        "year": year,
    }


@router.get("/{equipment_id}/status", response_model=EquipmentStatus)
async def get_equipment_status(equipment_id: str) -> EquipmentStatus:
    """Get comprehensive status of agricultural equipment."""

    if equipment_id not in _equipment_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment {equipment_id} not found"
        )

    tractor = _equipment_registry[equipment_id]

    return EquipmentStatus(
        equipment_id=equipment_id,
        equipment_type="FarmTractor",
        make=tractor.make,
        model=tractor.model,
        year=tractor.year,
        manual_url=tractor.manual_url,
        isobus_address=tractor.isobus_address,
        field_mode=tractor.field_mode.value,
        safety_level=tractor.safety_level.value,
        # Engine status
        engine_on=tractor.engine_on,
        engine_rpm=tractor.engine_rpm,
        engine_temp=tractor.engine_temp,
        fuel_level=tractor.fuel_level,
        # Movement status
        speed=tractor.speed,
        ground_speed=tractor.ground_speed,
        gear=tractor.gear,
        heading=tractor.current_heading,
        # GPS position
        gps_latitude=tractor.gps_latitude,
        gps_longitude=tractor.gps_longitude,
        # Implement status
        implement_position=tractor.implement_position.value,
        implement_depth=tractor.implement_depth,
        implement_width=tractor.implement_width,
        power_takeoff=tractor.power_takeoff,
        hydraulic_pressure=tractor.hydraulic_pressure,
        hydraulic_flow=tractor.hydraulic_flow,
        # Field operations
        work_rate=tractor.work_rate,
        area_covered=tractor.area_covered,
        wheel_slip=tractor.wheel_slip,
        draft_load=tractor.draft_load,
        # Safety systems
        emergency_stop_active=tractor.emergency_stop_active,
        autonomous_mode=tractor.autonomous_mode,
        auto_steer_enabled=tractor.auto_steer_enabled,
        obstacle_detection=tractor.obstacle_detection,
        safety_system_active=tractor.safety_system_active,
    )


@router.post("/{equipment_id}/engine/control")
async def control_engine(equipment_id: str, request: EngineControlRequest) -> dict[str, str]:
    """Control engine operations for agricultural equipment."""

    if equipment_id not in _equipment_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment {equipment_id} not found"
        )

    tractor = _equipment_registry[equipment_id]

    try:
        if request.action == "start":
            result = tractor.start_engine()
        elif request.action == "stop":
            result = tractor.stop_engine()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown engine action: {request.action}. Available actions: start, stop",
            )

        return {
            "message": f"Engine {request.action} executed successfully",
            "equipment_id": equipment_id,
            "action": request.action,
            "result": str(result),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Engine control failed: {str(e)}",
        ) from e


@router.post("/{equipment_id}/movement/control")
async def control_movement(equipment_id: str, request: MovementControlRequest) -> dict[str, str]:
    """Control movement operations for agricultural equipment."""

    if equipment_id not in _equipment_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment {equipment_id} not found"
        )

    tractor = _equipment_registry[equipment_id]

    try:
        if request.action == "accelerate":
            if request.increase is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="increase parameter required for accelerate action",
                )
            result = tractor.accelerate(request.increase)
        elif request.action == "brake":
            if request.decrease is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="decrease parameter required for brake action",
                )
            result = tractor.brake(request.decrease)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown movement action: {request.action}. Available actions: accelerate, brake",
            )

        return {
            "message": f"Movement {request.action} executed successfully",
            "equipment_id": equipment_id,
            "action": request.action,
            "result": str(result),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Movement control failed: {str(e)}",
        ) from e


@router.post("/{equipment_id}/implement/control")
async def control_implement(equipment_id: str, request: ImplementControlRequest) -> dict[str, str]:
    """Control implement operations for agricultural equipment."""

    if equipment_id not in _equipment_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment {equipment_id} not found"
        )

    tractor = _equipment_registry[equipment_id]

    try:
        if request.action == "raise":
            result = tractor.raise_implement()
        elif request.action == "lower":
            depth = request.depth if request.depth is not None else 6.0
            result = tractor.lower_implement(depth=depth)
        elif request.action == "engage_pto":
            result = tractor.engage_power_takeoff()
        elif request.action == "disengage_pto":
            result = tractor.disengage_power_takeoff()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown implement action: {request.action}. Available actions: raise, lower, engage_pto, disengage_pto",
            )

        return {
            "message": f"Implement {request.action} executed successfully",
            "equipment_id": equipment_id,
            "action": request.action,
            "result": str(result),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Implement control failed: {str(e)}",
        ) from e


@router.post("/{equipment_id}/safety/control")
async def control_safety(equipment_id: str, request: SafetyControlRequest) -> dict[str, str]:
    """Control safety systems for agricultural equipment."""

    if equipment_id not in _equipment_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment {equipment_id} not found"
        )

    tractor = _equipment_registry[equipment_id]

    try:
        if request.action == "emergency_stop":
            tractor.emergency_stop()
            result = "Emergency stop activated"
        elif request.action == "reset_emergency":
            tractor.reset_emergency_stop()
            result = "Emergency stop reset"
        elif request.action == "enable_autonomous":
            tractor.enable_autonomous_mode()
            result = "Autonomous mode enabled"
        elif request.action == "disable_autonomous":
            tractor.disable_autonomous_mode()
            result = "Autonomous mode disabled"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown safety action: {request.action}. Available actions: emergency_stop, reset_emergency, enable_autonomous, disable_autonomous",
            )

        return {
            "message": f"Safety {request.action} executed successfully",
            "equipment_id": equipment_id,
            "action": request.action,
            "result": str(result),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Safety control failed: {str(e)}",
        ) from e


@router.delete("/{equipment_id}")
async def unregister_equipment(equipment_id: str) -> dict[str, str]:
    """Unregister equipment from the system."""

    if equipment_id not in _equipment_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment {equipment_id} not found"
        )

    del _equipment_registry[equipment_id]

    return {
        "message": f"Equipment {equipment_id} unregistered successfully",
        "equipment_id": equipment_id,
    }
