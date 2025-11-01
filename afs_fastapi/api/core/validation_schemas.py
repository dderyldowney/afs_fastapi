"""
Comprehensive input validation schemas for AFS FastAPI agricultural operations.

This module provides Pydantic validation schemas for all API endpoints,
ensuring data integrity and agricultural compliance.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class EquipmentType(str, Enum):
    """Types of agricultural equipment."""

    TRACTOR = "tractor"
    COMBINE = "combine"
    PLANTER = "planter"
    SPRAYER = "sprayer"
    CULTIVATOR = "cultivator"
    HARVESTER = "harvester"
    PLOUGH = "plough"
    IRRIGATION = "irrigation"
    GENERAL = "general"


class OperationType(str, Enum):
    """Types of agricultural operations."""

    PLANTING = "planting"
    CULTIVATION = "cultivation"
    FERTILIZATION = "fertilization"
    IRRIGATION = "irrigation"
    PESTICIDE_APPLICATION = "pesticide_application"
    HARVESTING = "harvesting"
    MAINTENANCE = "maintenance"
    TRANSPORT = "transport"
    LAND_PREPARATION = "land_preparation"


class FieldMode(str, Enum):
    """Field operation modes."""

    TRANSPORT = "transport"
    TILLAGE = "tillage"
    PLANTING = "planting"
    SPRAYING = "spraying"
    HARVESTING = "harvesting"
    MAINTENANCE = "maintenance"


class SafetyLevel(str, Enum):
    """ISO 18497 safety levels."""

    PERFORMANCE_LEVEL_C = "PLc"
    PERFORMANCE_LEVEL_D = "PLd"
    PERFORMANCE_LEVEL_E = "PLe"


class OptimizationLevel(str, Enum):
    """AI optimization levels."""

    CONSERVATIVE = "conservative"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"
    ADAPTIVE = "adaptive"

    @property
    def reduction_target(self) -> float:
        """Get reduction target percentage for optimization level."""
        if self == self.CONSERVATIVE:
            return 0.15
        elif self == self.STANDARD:
            return 0.30
        elif self == self.AGGRESSIVE:
            return 0.50
        else:  # ADAPTIVE
            return 0.30  # Default to standard


class TargetFormat(str, Enum):
    """AI processing target formats."""

    STANDARD = "standard"
    BRIEF = "brief"
    BULLET_POINTS = "bullet_points"


class ISOBUSAddress(BaseModel):
    """ISOBUS address validation."""

    address: int = Field(..., ge=0x80, le=0xFF, description="ISOBUS device address (128-255)")

    @field_validator("address")
    @classmethod
    def validate_address(cls, v):
        """Validate ISOBUS address format."""
        if v not in range(0x80, 0x88):  # Standard tractor range
            raise ValueError("ISOBUS address should be between 0x80-0x87 for tractors")
        return v


class GPSCoordinates(BaseModel):
    """GPS coordinates validation."""

    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees (-90 to 90)")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees (-180 to 180)")
    altitude: float | None = Field(None, ge=-500, le=8848, description="Altitude in meters")

    @field_validator("latitude", "longitude")
    @classmethod
    def validate_coordinates(cls, v):
        """Validate coordinate precision."""
        if abs(v) > 180:
            raise ValueError("Coordinates must be within valid ranges")
        return round(v, 6)  # Standard GPS precision


class FieldSegmentRequest(BaseModel):
    """Field segment creation request."""

    segment_id: str = Field(..., description="Unique segment identifier")
    field_id: str = Field(..., description="Field identifier")
    area_acres: float = Field(..., gt=0, le=1000, description="Area in acres")
    boundaries: list[GPSCoordinates] = Field(..., min_length=3, description="Boundary coordinates")
    soil_type: str | None = Field(None, description="Soil type classification")
    crop_type: str | None = Field(None, description="Crop type planted")
    elevation_change: float | None = Field(
        None, ge=-50, le=50, description="Elevation change in meters"
    )

    @field_validator("segment_id")
    @classmethod
    def validate_segment_id(cls, v):
        """Validate segment ID format."""
        if not re.match(r"^[A-Z]{1,5}-\d{3,5}$", v):
            raise ValueError("Segment ID must follow format like 'FS-001' or 'FIELD-A001'")
        return v

    @field_validator("field_id")
    @classmethod
    def validate_field_id(cls, v):
        """Validate field ID format."""
        if not re.match(r"^[A-Z]{1,5}-\d{3,5}$", v):
            raise ValueError("Field ID must follow format like 'FIELD-001' or 'A-12345'")
        return v


class EquipmentControlRequest(BaseModel):
    """Equipment control request."""

    equipment_id: str = Field(..., description="Equipment identifier")
    operation: str = Field(..., description="Operation to perform")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Operation parameters")
    priority: str = Field(default="normal", description="Operation priority")
    safety_override: bool = Field(
        False, description="Override safety checks (requires special permission)"
    )

    @field_validator("equipment_id")
    @classmethod
    def validate_equipment_id(cls, v):
        """Validate equipment ID format."""
        if not re.match(r"^[A-Z]{3,5}-\d{3}$", v):
            raise ValueError("Equipment ID must follow format like 'TRC-001' or 'PLT-123'")
        return v

    @field_validator("operation")
    @classmethod
    def validate_operation(cls, v):
        """Validate operation type."""
        valid_operations = [
            "start_engine",
            "stop_engine",
            "engage_pto",
            "disengage_pto",
            "raise_implement",
            "lower_implement",
            "set_speed",
            "change_gear",
            "enable_autosteer",
            "disable_autosteer",
            "emergency_stop",
        ]
        if v not in valid_operations:
            raise ValueError(f"Invalid operation. Must be one of: {valid_operations}")
        return v


class SoilSensorRequest(BaseModel):
    """Soil sensor reading request."""

    sensor_id: str = Field(..., description="Sensor identifier")
    location: GPSCoordinates = Field(..., description="Sensor location")
    readings: dict[str, float] = Field(..., description="Soil measurements")
    timestamp: datetime = Field(default_factory=datetime.now, description="Reading timestamp")

    @field_validator("sensor_id")
    @classmethod
    def validate_sensor_id(cls, v):
        """Validate sensor ID format."""
        if not re.match(r"^[A-Z]{3,5}-\d{3}$", v):
            raise ValueError("Sensor ID must follow format like 'SOI-001' or 'SRN-123'")
        return v

    @field_validator("readings")
    @classmethod
    def validate_soil_readings(cls, v):
        """Validate soil measurement ranges."""
        if "moisture_percent" in v:
            if not 0 <= v["moisture_percent"] <= 100:
                raise ValueError("Soil moisture must be between 0-100%")

        if "ph" in v:
            if not 0 <= v["ph"] <= 14:
                raise ValueError("Soil pH must be between 0-14")

        if "temperature_celsius" in v:
            if not -20 <= v["temperature_celsius"] <= 60:
                raise ValueError("Soil temperature must be between -20°C to 60°C")

        if "electrical_conductivity" in v:
            if not 0 <= v["electrical_conductivity"] <= 10:
                raise ValueError("Electrical conductivity must be between 0-10 dS/m")

        return v


class WaterQualityRequest(BaseModel):
    """Water quality sensor reading request."""

    sensor_id: str = Field(..., description="Sensor identifier")
    location: GPSCoordinates = Field(..., description="Sensor location")
    readings: dict[str, float] = Field(..., description="Water quality measurements")
    timestamp: datetime = Field(default_factory=datetime.now, description="Reading timestamp")

    @field_validator("sensor_id")
    @classmethod
    def validate_sensor_id(cls, v):
        """Validate sensor ID format."""
        if not re.match(r"^[A-Z]{3,5}-\d{3}$", v):
            raise ValueError("Water sensor ID must follow format like 'WAT-001' or 'WQR-123'")
        return v

    @field_validator("readings")
    @classmethod
    def validate_water_readings(cls, v):
        """Validate water quality measurements."""
        if "ph" in v:
            if not 0 <= v["ph"] <= 14:
                raise ValueError("Water pH must be between 0-14")

        if "temperature_celsius" in v:
            if not 0 <= v["temperature_celsius"] <= 100:
                raise ValueError("Water temperature must be between 0°C to 100°C")

        if "turbidity_ntu" in v:
            if not 0 <= v["turbidity_ntu"] <= 1000:
                raise ValueError("Turbidity must be between 0-1000 NTU")

        if "dissolved_oxygen_ppm" in v:
            if not 0 <= v["dissolved_oxygen_ppm"] <= 20:
                raise ValueError("Dissolved oxygen must be between 0-20 ppm")

        return v


class AIProcessingRequest(BaseModel):
    """AI processing request with agricultural context."""

    user_input: str = Field(..., min_length=1, max_length=10000, description="Text to process")
    service_name: str = Field(default="platform", description="Calling service name")
    optimization_level: OptimizationLevel = Field(
        default=OptimizationLevel.STANDARD, description="Optimization intensity"
    )
    target_format: TargetFormat = Field(default=TargetFormat.STANDARD, description="Output format")
    token_budget: int | None = Field(None, ge=100, le=8000, description="Maximum token budget")
    context_data: dict[str, Any] | None = Field(None, description="Agricultural operation context")
    safety_override: bool = Field(
        False, description="Override safety checks for emergency situations"
    )

    @field_validator("context_data")
    @classmethod
    def validate_context_data(cls, v):
        """Validate agricultural context data."""
        if v is None:
            return v

        # Validate common agricultural context fields
        if "equipment_id" in v:
            if not re.match(r"^[A-Z]{3,5}-\d{3}$", v["equipment_id"]):
                raise ValueError("Equipment ID in context must be valid format")

        if "field_id" in v:
            if not re.match(r"^[A-Z]{1,5}-\d{3,5}$", v["field_id"]):
                raise ValueError("Field ID in context must be valid format")

        if "operation_type" in v:
            valid_operations = [op.value for op in OperationType]
            if v["operation_type"] not in valid_operations:
                raise ValueError(f"Invalid operation type. Must be one of: {valid_operations}")

        return v

    @field_validator("safety_override")
    @classmethod
    def validate_safety_override(cls, v, info):
        """Validate safety override is only used for emergency situations."""
        if v is True:
            user_input = info.data.get("user_input", "")
            if not user_input:
                raise ValueError("Safety override requires user input for emergency validation")

            # Check for emergency keywords
            emergency_keywords = [
                "emergency",
                "emergency stop",
                "critical",
                "urgent",
                "immediate danger",
                "safety hazard",
                "collision",
                "accident",
                "malfunction",
                "failure",
                "unsafe condition",
                "hazard",
                "risk",
                "danger",
                "critical alert",
            ]

            user_input_lower = user_input.lower()
            is_emergency = any(keyword in user_input_lower for keyword in emergency_keywords)

            if not is_emergency:
                raise ValueError(
                    "Safety override can only be used for emergency operations. "
                    "Emergency keywords not detected in request."
                )

        return v


class FleetCoordinationRequest(BaseModel):
    """Fleet coordination request."""

    fleet_id: str = Field(..., description="Fleet identifier")
    operation_type: OperationType = Field(..., description="Type of coordination operation")
    tractor_ids: list[str] = Field(
        ..., min_length=1, max_length=20, description="Tractor IDs involved"
    )
    field_segments: list[str] = Field(default_factory=list, description="Target field segments")
    coordination_parameters: dict[str, Any] = Field(
        default_factory=dict, description="Coordination parameters"
    )
    safety_checks: bool = Field(default=True, description="Perform safety coordination checks")

    @field_validator("fleet_id")
    @classmethod
    def validate_fleet_id(cls, v):
        """Validate fleet ID format."""
        if not re.match(r"^FLT-\d{3,5}$", v):
            raise ValueError("Fleet ID must follow format like 'FLT-001' or 'FLT-12345'")
        return v

    @field_validator("tractor_ids")
    @classmethod
    def validate_tractor_ids(cls, v):
        """Validate tractor ID formats."""
        for tractor_id in v:
            if not re.match(r"^[A-Z]{3,5}-\d{3}$", tractor_id):
                raise ValueError(f"Invalid tractor ID format: {tractor_id}")
        return v


class FieldOperationRequest(BaseModel):
    """Field operation request."""

    field_id: str = Field(..., description="Field identifier")
    operation_type: OperationType = Field(..., description="Type of field operation")
    equipment_ids: list[str] = Field(
        ..., min_length=1, max_length=10, description="Equipment to assign"
    )
    start_time: datetime | None = Field(None, description="Planned start time")
    estimated_duration_hours: float | None = Field(
        None, gt=0, le=72, description="Estimated duration"
    )
    safety_parameters: dict[str, Any] = Field(default_factory=dict, description="Safety parameters")
    weather_constraints: dict[str, Any] = Field(
        default_factory=dict, description="Weather constraints"
    )

    @field_validator("field_id")
    @classmethod
    def validate_field_id(cls, v):
        """Validate field ID format."""
        if not re.match(r"^[A-Z]{1,5}-\d{3,5}$", v):
            raise ValueError("Field ID must follow format like 'FIELD-001' or 'A-12345'")
        return v


class SafetyZoneRequest(BaseModel):
    """Safety zone management request."""

    zone_id: str = Field(..., description="Safety zone identifier")
    equipment_id: str = Field(..., description="Equipment identifier")
    boundary_points: list[GPSCoordinates] = Field(
        ..., min_length=3, description="Boundary coordinates"
    )
    safety_level: SafetyLevel = Field(..., description="Safety performance level")
    max_speed_mph: float = Field(..., ge=0, le=25, description="Maximum speed limit")
    detection_required: bool = Field(True, description="Obstacle detection required")
    weather_dependent: bool = Field(False, description="Zone activation depends on weather")

    @field_validator("zone_id")
    @classmethod
    def validate_zone_id(cls, v):
        """Validate zone ID format."""
        if not re.match(r"^[A-Z]{3}-\d{3}$", v):
            raise ValueError("Zone ID must follow format like 'SZN-001' or 'ZON-123'")
        return v


class EquipmentStatusRequest(BaseModel):
    """Equipment status request."""

    equipment_ids: list[str] = Field(
        ..., min_length=1, max_length=20, description="Equipment identifiers"
    )
    include_diagnostics: bool = Field(True, description="Include diagnostic data")
    include_location: bool = Field(True, description="Include GPS location data")
    include_safety_status: bool = Field(True, description="Include safety system status")

    @field_validator("equipment_ids")
    @classmethod
    def validate_equipment_ids(cls, v):
        """Validate equipment ID formats."""
        for equipment_id in v:
            if not re.match(r"^[A-Z]{3,5}-\d{3}$", equipment_id):
                raise ValueError(f"Invalid equipment ID format: {equipment_id}")
        return v


class ComplianceCheckRequest(BaseModel):
    """Compliance check request."""

    compliance_type: str = Field(..., description="Type of compliance check")
    equipment_id: str | None = Field(None, description="Equipment to check (if applicable)")
    field_id: str | None = Field(None, description="Field to check (if applicable)")
    operation_type: OperationType | None = Field(None, description="Operation type (if applicable)")
    standards: list[str] = Field(default_factory=list, description="Standards to check against")

    @field_validator("compliance_type")
    @classmethod
    def validate_compliance_type(cls, v):
        """Validate compliance type."""
        valid_types = [
            "iso_11783",
            "iso_18497",
            "agricultural_safety",
            "equipment_safety",
            "field_safety",
        ]
        if v not in valid_types:
            raise ValueError(f"Invalid compliance type. Must be one of: {valid_types}")
        return v


class CommonQueryParams(BaseModel):
    """Common query parameters for API endpoints."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=10, ge=1, le=100, description="Items per page")
    sort_by: str | None = Field(None, description="Field to sort by")
    sort_order: str = Field(default="asc", description="Sort order (asc/desc)")
    filter_field: str | None = Field(None, description="Field to filter by")
    filter_value: str | None = Field(None, description="Filter value")

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v):
        """Validate sort order."""
        if v not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v


# Utility functions for validation
def validate_agricultural_data(data: dict[str, Any]) -> dict[str, Any]:
    """Validate agricultural data against ISO standards and best practices."""
    validated_data = data.copy()

    # Validate GPS coordinates if present
    if "latitude" in validated_data and "longitude" in validated_data:
        lat = validated_data["latitude"]
        lon = validated_data["longitude"]
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError("Invalid GPS coordinates")

    # Validate agricultural measurements
    if "moisture" in validated_data:
        if not (0 <= validated_data["moisture"] <= 100):
            raise ValueError("Moisture must be between 0-100%")

    if "ph" in validated_data:
        if not (0 <= validated_data["ph"] <= 14):
            raise ValueError("pH must be between 0-14")

    if "temperature" in validated_data:
        if not (-50 <= validated_data["temperature"] <= 60):
            raise ValueError("Temperature must be between -50°C to 60°C")

    return validated_data


def validate_equipment_operation(operation: str, equipment_type: str) -> bool:
    """Validate that equipment operation is valid for equipment type."""
    operation_equipment_map = {
        "start_engine": ["tractor", "combine", "harvester"],
        "engage_pto": ["tractor", "combine"],
        "planting": ["planter", "tractor"],
        "spraying": ["sprayer", "tractor"],
        "harvesting": ["combine", "harvester"],
        "irrigation": ["irrigation", "tractor"],
        "maintenance": ["general"],
    }

    valid_equipment = operation_equipment_map.get(operation, ["general"])
    return equipment_type in valid_equipment
