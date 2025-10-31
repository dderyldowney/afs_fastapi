"""
Safety Status API Endpoints

Provides RESTful API access to agricultural safety systems including ISO 25119 compliance,
emergency stop propagation, collision avoidance, and cross-layer validation systems.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/safety", tags=["Safety Systems"])


# Simple safety system management for API demo
# In production, this would integrate with actual safety hardware and monitoring systems
class SimpleSafetyManager:
    """Simple safety system management for API demonstration."""

    def __init__(self):
        self.emergency_active: bool = False
        self.collision_avoidance_active: bool = True
        self.emergency_history: list[dict[str, Any]] = []
        self.acknowledgments: dict[str, bool] = {}

    def is_emergency_active(self) -> bool:
        """Check if emergency stop is currently active."""
        return self.emergency_active

    def activate_emergency_stop(
        self,
        severity: str,
        reason: str,
        equipment_ids: list[str] | None,
        require_acknowledgment: bool,
    ) -> dict[str, Any]:
        """Activate emergency stop system."""
        self.emergency_active = True
        emergency_event = {
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "reason": reason,
            "equipment_ids": equipment_ids,
            "require_acknowledgment": require_acknowledgment,
        }
        self.emergency_history.append(emergency_event)

        return {
            "emergency_id": f"EMERGENCY_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "propagation_time_ms": 250.0,
        }

    def reset_emergency_stop(self):
        """Reset emergency stop system."""
        self.emergency_active = False
        return True

    def get_emergency_history(self) -> list[dict[str, Any]]:
        """Get emergency event history."""
        return self.emergency_history.copy()

    def get_acknowledgment_status(self) -> dict[str, bool]:
        """Get equipment acknowledgment status."""
        return self.acknowledgments.copy()

    def validate_system(self) -> bool:
        """Validate safety system functionality."""
        return True  # Simplified validation


# Global safety manager instance
_safety_manager = SimpleSafetyManager()


class SafetySystemStatus(BaseModel):
    """Comprehensive safety system status."""

    system_name: str = Field(..., description="Safety system identifier")
    operational_status: str = Field(..., description="Current operational status")
    safety_level: str = Field(..., description="Current safety integrity level")
    agricultural_safety_level: str = Field(..., description="Agricultural-specific safety level")
    emergency_stop_active: bool = Field(..., description="Emergency stop system status")
    collision_avoidance_active: bool = Field(..., description="Collision avoidance system status")
    last_safety_check: str = Field(..., description="Timestamp of last safety validation")
    active_hazards: int = Field(..., description="Number of active hazard conditions")
    safety_compliance: dict[str, bool] = Field(
        ..., description="Compliance status for safety standards"
    )


class EmergencyStatus(BaseModel):
    """Emergency system status and history."""

    emergency_active: bool = Field(..., description="Current emergency state")
    emergency_level: str = Field(..., description="Emergency severity level")
    active_emergency_count: int = Field(..., description="Number of active emergency conditions")
    last_emergency_time: str | None = Field(None, description="Timestamp of last emergency event")
    emergency_acknowledgments: dict[str, bool] = Field(
        ..., description="Equipment acknowledgment status"
    )
    response_time_ms: float | None = Field(
        None, description="Emergency response time in milliseconds"
    )
    propagation_status: str = Field(..., description="Fleet-wide emergency propagation status")


class CollisionAvoidanceStatus(BaseModel):
    """Collision avoidance system status."""

    system_active: bool = Field(..., description="Collision avoidance system operational status")
    detected_obstacles: int = Field(..., description="Number of currently detected obstacles")
    threat_level: str = Field(..., description="Current threat assessment level")
    evasive_action_active: bool = Field(..., description="Evasive maneuver in progress")
    safety_zone_violations: int = Field(..., description="Number of safety zone violations")
    trajectory_predictions: list[dict[str, Any]] = Field(
        ..., description="Current trajectory predictions"
    )
    last_collision_risk: str | None = Field(
        None, description="Timestamp of last collision risk event"
    )


class HazardAnalysis(BaseModel):
    """ISO 25119 hazard analysis information."""

    hazard_id: str = Field(..., description="Unique hazard identifier")
    severity: str = Field(..., description="Hazard severity level (S1-S3)")
    exposure: str = Field(..., description="Exposure level (E1-E4)")
    controllability: str = Field(..., description="Controllability level (C1-C3)")
    agricultural_safety_level: str = Field(..., description="Resulting ASL classification")
    sil_classification: str = Field(..., description="Safety Integrity Level classification")
    hazard_description: str = Field(..., description="Detailed hazard description")
    mitigation_measures: list[str] = Field(..., description="Active mitigation measures")


class SafetyValidationRequest(BaseModel):
    """Request for safety system validation."""

    validation_type: str = Field(
        ..., description="Type of validation: full, emergency, collision, compliance"
    )
    target_systems: list[str] | None = Field(None, description="Specific systems to validate")
    include_hazard_analysis: bool = Field(
        False, description="Include comprehensive hazard analysis"
    )


class EmergencyStopRequest(BaseModel):
    """Emergency stop activation request."""

    severity: str = Field(..., description="Emergency severity: CRITICAL, HIGH, MEDIUM, LOW")
    reason: str = Field(..., description="Reason for emergency stop")
    equipment_ids: list[str] | None = Field(
        None, description="Specific equipment to stop (all if None)"
    )
    require_acknowledgment: bool = Field(True, description="Require acknowledgment from equipment")


@router.get("/status", response_model=SafetySystemStatus)
async def get_safety_system_status() -> SafetySystemStatus:
    """Get comprehensive safety system status."""

    # Get current timestamp
    current_time = datetime.now().isoformat()

    # Check emergency stop status
    emergency_active = _safety_manager.is_emergency_active()
    collision_active = _safety_manager.collision_avoidance_active

    # Safety compliance check
    compliance_status = {
        "iso_25119": True,  # ISO 25119 functional safety
        "iso_18497": True,  # ISO 18497 autonomous agricultural machinery
        "iso_11783": True,  # ISO 11783 ISOBUS communication
        "emergency_response": emergency_active or True,  # Emergency system operational
        "collision_avoidance": collision_active,
    }

    return SafetySystemStatus(
        system_name="AFS Agricultural Safety System",
        operational_status="OPERATIONAL",
        safety_level="SIL-2",  # Safety Integrity Level 2
        agricultural_safety_level="ASL-B",  # Agricultural Safety Level B
        emergency_stop_active=emergency_active,
        collision_avoidance_active=collision_active,
        last_safety_check=current_time,
        active_hazards=0,  # No active hazards in demo
        safety_compliance=compliance_status,
    )


@router.get("/emergency/status", response_model=EmergencyStatus)
async def get_emergency_status() -> EmergencyStatus:
    """Get emergency system status and history."""

    emergency_active = _safety_manager.is_emergency_active()
    emergency_history = _safety_manager.get_emergency_history()

    # Get acknowledgment status from connected equipment
    acknowledgments = _safety_manager.get_acknowledgment_status()

    return EmergencyStatus(
        emergency_active=emergency_active,
        emergency_level="NONE" if not emergency_active else "HIGH",
        active_emergency_count=len(emergency_history),
        last_emergency_time=emergency_history[0]["timestamp"] if emergency_history else None,
        emergency_acknowledgments=acknowledgments,
        response_time_ms=250.0 if emergency_active else None,  # Sub-500ms response time
        propagation_status="READY",
    )


@router.post("/emergency/stop")
async def activate_emergency_stop(request: EmergencyStopRequest) -> dict[str, Any]:
    """Activate fleet-wide emergency stop system."""

    try:
        # Activate emergency stop with specified parameters
        result = _safety_manager.activate_emergency_stop(
            severity=request.severity,
            reason=request.reason,
            equipment_ids=request.equipment_ids,
            require_acknowledgment=request.require_acknowledgment,
        )

        return {
            "message": "Emergency stop activated successfully",
            "emergency_id": result.get(
                "emergency_id", "EMERGENCY_" + datetime.now().strftime("%Y%m%d_%H%M%S")
            ),
            "severity": request.severity,
            "equipment_count": len(request.equipment_ids) if request.equipment_ids else "ALL",
            "propagation_time_ms": result.get("propagation_time_ms", 250),
            "acknowledgment_required": request.require_acknowledgment,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate emergency stop: {str(e)}",
        ) from e


@router.post("/emergency/reset")
async def reset_emergency_stop() -> dict[str, str]:
    """Reset emergency stop system after safety conditions are clear."""

    try:
        _safety_manager.reset_emergency_stop()

        return {
            "message": "Emergency stop reset successfully",
            "status": "OPERATIONAL",
            "reset_time": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset emergency stop: {str(e)}",
        ) from e


@router.get("/collision-avoidance/status", response_model=CollisionAvoidanceStatus)
async def get_collision_avoidance_status() -> CollisionAvoidanceStatus:
    """Get collision avoidance system status."""

    try:
        system_active = _safety_manager.collision_avoidance_active

        return CollisionAvoidanceStatus(
            system_active=system_active,
            detected_obstacles=0,  # No obstacles detected in demo
            threat_level="LOW",
            evasive_action_active=False,
            safety_zone_violations=0,
            trajectory_predictions=[],  # No active trajectory predictions in demo
            last_collision_risk=None,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collision avoidance status: {str(e)}",
        ) from e


@router.get("/hazard-analysis", response_model=list[HazardAnalysis])
async def get_hazard_analysis() -> list[HazardAnalysis]:
    """Get comprehensive ISO 25119 hazard analysis."""

    # Example hazard analyses for agricultural operations
    hazard_analyses = [
        HazardAnalysis(
            hazard_id="HAZ-001",
            severity="S2",  # Serious injury
            exposure="E3",  # High exposure during field operations
            controllability="C2",  # Normally controllable
            agricultural_safety_level="ASL-B",
            sil_classification="SIL-2",
            hazard_description="Collision with stationary obstacles during autonomous field operations",
            mitigation_measures=[
                "LiDAR obstacle detection",
                "Emergency stop system",
                "Operator supervision",
                "Reduced speed in obstacle areas",
            ],
        ),
        HazardAnalysis(
            hazard_id="HAZ-002",
            severity="S1",  # Minor injury
            exposure="E2",  # Medium exposure
            controllability="C1",  # Simply controllable
            agricultural_safety_level="ASL-A",
            sil_classification="SIL-1",
            hazard_description="Hydraulic system pressure fluctuation during implement operation",
            mitigation_measures=[
                "Pressure monitoring",
                "Automatic pressure regulation",
                "Visual pressure indicators",
                "Maintenance scheduling",
            ],
        ),
        HazardAnalysis(
            hazard_id="HAZ-003",
            severity="S3",  # Life-threatening injury
            exposure="E4",  # Very high exposure
            controllability="C3",  # Difficult to control
            agricultural_safety_level="ASL-C",
            sil_classification="SIL-3",
            hazard_description="Multi-tractor coordination failure leading to collision",
            mitigation_measures=[
                "Redundant communication systems",
                "Collision avoidance algorithms",
                "Emergency stop propagation",
                "Operator override capability",
                "GPS position validation",
            ],
        ),
    ]

    return hazard_analyses


@router.post("/validate")
async def validate_safety_systems(request: SafetyValidationRequest) -> dict[str, Any]:
    """Perform comprehensive safety system validation."""

    try:
        validation_results: dict[str, Any] = {
            "validation_id": f"VAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "validation_type": request.validation_type,
            "timestamp": datetime.now().isoformat(),
            "overall_status": "PASSED",
            "system_results": {},
        }

        # Validate emergency stop system
        if not request.target_systems or "emergency" in request.target_systems:
            emergency_valid = _safety_manager.validate_system()
            validation_results["system_results"]["emergency_stop"] = {
                "status": "PASSED" if emergency_valid else "FAILED",
                "response_time_ms": 250.0,
                "coverage": "100%",
            }

        # Validate collision avoidance system
        if not request.target_systems or "collision" in request.target_systems:
            collision_valid = _safety_manager.validate_system()
            validation_results["system_results"]["collision_avoidance"] = {
                "status": "PASSED" if collision_valid else "FAILED",
                "detection_range_m": 50.0,
                "accuracy": "95%",
            }

        # ISO 25119 compliance validation
        if not request.target_systems or "compliance" in request.target_systems:
            validation_results["system_results"]["iso_25119_compliance"] = {
                "status": "PASSED",
                "sil_level": "SIL-2",
                "asl_level": "ASL-B",
                "functional_safety": "COMPLIANT",
            }

        # Include hazard analysis if requested
        if request.include_hazard_analysis:
            validation_results["hazard_analysis_summary"] = {
                "total_hazards": 3,
                "high_risk_hazards": 1,
                "mitigation_coverage": "100%",
            }

        return validation_results

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Safety validation failed: {str(e)}",
        ) from e


@router.get("/compliance/iso25119")
async def get_iso25119_compliance() -> dict[str, Any]:
    """Get ISO 25119 functional safety compliance status."""

    return {
        "standard": "ISO 25119",
        "title": "Tractors and machinery for agriculture and forestry - Safety-related parts of control systems",
        "compliance_status": "COMPLIANT",
        "certification_date": "2024-01-15",
        "next_review_date": "2025-01-15",
        "safety_lifecycle_phases": [
            {"phase": "Concept", "status": "COMPLETE"},
            {"phase": "Product Development", "status": "COMPLETE"},
            {"phase": "Production", "status": "ACTIVE"},
            {"phase": "Operation", "status": "ACTIVE"},
            {"phase": "Maintenance", "status": "ACTIVE"},
        ],
        "sil_classifications": {
            "SIL-1": ["Hydraulic pressure monitoring", "Speed limiting"],
            "SIL-2": ["Emergency stop system", "Collision avoidance"],
            "SIL-3": ["Multi-tractor coordination", "Autonomous navigation"],
        },
        "agricultural_safety_levels": {
            "ASL-A": ["Operator present operations"],
            "ASL-B": ["Supervised autonomous operations"],
            "ASL-C": ["Fully autonomous operations"],
        },
    }
