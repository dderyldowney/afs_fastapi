"""
Standardized response models for AFS FastAPI agricultural operations.

This module provides consistent response models for all API endpoints,
ensuring proper formatting, validation, and agricultural compliance.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response model for all API responses."""

    success: bool = Field(True, description="Request success status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    request_id: str | None = Field(None, description="Unique request identifier")


class ErrorDetail(BaseModel):
    """Detailed error information."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    severity: str = Field(..., description="Error severity level")
    category: str = Field(..., description="Error category")
    field: str | None = Field(None, description="Field name (if applicable)")
    value: Any | None = Field(None, description="Invalid value (if applicable)")
    equipment_id: str | None = Field(None, description="Affected equipment ID")
    field_id: str | None = Field(None, description="Affected field ID")
    operation_type: str | None = Field(None, description="Type of operation")
    recovery_suggestions: list[str] = Field(
        default_factory=list, description="Recovery suggestions"
    )


class StandardResponse(BaseResponse):
    """Standard success response format."""

    data: Any | None = Field(None, description="Response data")
    message: str | None = Field(None, description="Success message")
    pagination: dict[str, Any] | None = Field(
        None, description="Pagination information for list responses"
    )


class ErrorResponse(BaseResponse):
    """Standard error response format."""

    success: bool = Field(False, description="Request success status")
    error: dict[str, Any] = Field(..., description="Error details")
    recovery_suggestions: list[str] = Field(
        default_factory=list, description="Suggested recovery actions"
    )


class PaginatedResponse(BaseResponse):
    """Standard paginated response format."""

    data: list[Any] = Field(..., description="Response data items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")


class EquipmentStatusResponse(BaseResponse):
    """Standardized equipment status response."""

    equipment_id: str = Field(..., description="Equipment identifier")
    equipment_type: str = Field(..., description="Type of equipment")
    status: str = Field(..., description="Equipment status")
    location: dict[str, float] | None = Field(None, description="GPS coordinates")
    metrics: dict[str, Any] = Field(default_factory=dict, description="Equipment metrics")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update time")
    isobus_compliance: bool = Field(True, description="ISOBUS compliance status")
    safety_level: str = Field("PLc", description="Safety performance level")


class FieldOperationResponse(BaseResponse):
    """Standardized field operation response."""

    field_id: str = Field(..., description="Field identifier")
    operation_type: str = Field(..., description="Type of operation")
    status: str = Field(..., description="Operation status")
    progress: float = Field(..., description="Progress percentage (0-100)")
    area_covered: float = Field(..., description="Area covered in acres")
    estimated_completion: datetime | None = Field(None, description="Estimated completion time")
    equipment_assigned: list[str] = Field(default_factory=list, description="Assigned equipment")
    safety_compliance: bool = Field(True, description="Safety compliance status")
    iso_violations: list[str] = Field(default_factory=list, description="ISO violations")


class MonitoringDataResponse(BaseResponse):
    """Standardized monitoring data response."""

    sensor_id: str = Field(..., description="Sensor identifier")
    sensor_type: str = Field(..., description="Type of sensor")
    location: dict[str, float] = Field(..., description="Sensor location coordinates")
    readings: dict[str, Any] = Field(..., description="Sensor readings")
    reading_timestamp: datetime = Field(..., description="Reading timestamp")
    data_quality: str = Field("good", description="Data quality assessment")
    calibration_due: datetime | None = Field(None, description="Next calibration due")
    agricultural_metrics: dict[str, Any] = Field(
        default_factory=dict, description="Agricultural-specific metrics"
    )


class AIProcessingResponse(BaseResponse):
    """Standardized AI processing response."""

    input_text: str = Field(..., description="Original input text")
    processed_output: str = Field(..., description="Processed output text")
    optimization_applied: bool = Field(..., description="Whether optimization was applied")
    tokens_saved: int = Field(..., description="Number of tokens saved")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    agricultural_compliance: bool = Field(True, description="Agricultural compliance maintained")
    optimization_level: str = Field(..., description="Applied optimization level")
    fallback_used: bool = Field(False, description="Whether fallback processing was used")
    metrics: dict[str, Any] = Field(default_factory=dict, description="Processing metrics")


class FleetCoordinationResponse(BaseResponse):
    """Standardized fleet coordination response."""

    fleet_id: str = Field(..., description="Fleet identifier")
    coordination_type: str = Field(..., description="Type of coordination")
    tractors_involved: list[str] = Field(..., description="Tractor IDs involved")
    status: str = Field(..., description="Coordination status")
    field_segments: list[str] = Field(default_factory=list, description="Assigned field segments")
    estimated_completion: datetime | None = Field(None, description="Estimated completion time")
    safety_check_passed: bool = Field(True, description="Safety compliance check")
    conflict_resolution: dict[str, Any] = Field(
        default_factory=dict, description="Conflict resolution details"
    )


class SystemHealthResponse(BaseResponse):
    """Standardized system health response."""

    overall_status: str = Field(..., description="Overall system status")
    services_status: dict[str, str] = Field(..., description="Individual service statuses")
    api_endpoints: dict[str, str] = Field(..., description="API endpoint statuses")
    database_status: str = Field(..., description="Database connectivity status")
    message_queue_status: str = Field(..., description="Message queue status")
    agricultural_safety_mode: bool = Field(True, description="Agricultural safety mode active")
    uptime_seconds: int = Field(..., description="System uptime in seconds")
    last_health_check: datetime = Field(..., description="Last health check time")


class ComplianceViolation(BaseModel):
    """Individual compliance violation for agricultural safety reporting."""

    code: str = Field(..., description="Violation code identifier")
    message: str = Field(..., description="Human-readable violation message")
    severity: str = Field(..., description="Violation severity level")
    category: str = Field(..., description="Violation category")
    field: str | None = Field(None, description="Field name related to violation")
    value: Any | None = Field(None, description="Value that caused violation")
    equipment_id: str | None = Field(None, description="Related equipment ID")
    field_id: str | None = Field(None, description="Related field ID")
    operation_type: str | None = Field(None, description="Related operation type")
    recovery_suggestions: list[str] = Field(
        default_factory=list, description="Suggested recovery actions"
    )


class ComplianceReportResponse(BaseResponse):
    """Standardized compliance report response."""

    report_id: str = Field(..., description="Report identifier")
    compliance_type: str = Field(..., description="Type of compliance check")
    standards_check: dict[str, bool] = Field(..., description="Standards compliance results")
    iso_11783_compliance: bool = Field(True, description="ISO 11783 compliance status")
    iso_18497_compliance: bool = Field(True, description="ISO 18497 compliance status")
    agricultural_safety_compliance: bool = Field(True, description="Agricultural safety compliance")
    violations: list[dict[str, str]] = Field(  # type: ignore[reportUnknownVariableType]
        default_factory=list, description="Compliance violations"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Compliance recommendations"
    )
    generated_at: datetime = Field(..., description="Report generation timestamp")


class APIValidationError(Exception):
    """Exception for API validation errors."""

    def __init__(self, message: str, details: ErrorDetail | None = None):
        """Initialize API validation error."""
        self.message = message
        self.details = details or ErrorDetail(
            code="VALIDATION_ERROR",
            message=message,
            severity="medium",
            category="validation",
            field=None,
            value=None,
            equipment_id=None,
            field_id=None,
            operation_type=None,
        )
        super().__init__(message)


class AgriculturalValidationError(APIValidationError):
    """Exception for agricultural-specific validation errors."""

    def __init__(self, message: str, equipment_id: str | None = None, field_id: str | None = None):
        """Initialize agricultural validation error."""
        details = ErrorDetail(
            code="AGRICULTURAL_VALIDATION_ERROR",
            message=message,
            severity="high",
            category="agricultural_validation",
            field=None,
            value=None,
            equipment_id=equipment_id,
            field_id=field_id,
            operation_type="agricultural_operation",
        )
        super().__init__(message, details)


class SafetyProtocolViolationError(Exception):
    """Exception for safety protocol violations."""

    def __init__(self, message: str, violation_details: dict[str, Any]):
        """Initialize safety protocol violation error."""
        self.message = message
        self.violation_details = violation_details
        super().__init__(message)


# Common validation utilities
class AgriculturalValidators:
    """Agricultural-specific validation utilities."""

    @staticmethod
    def validate_gps_coordinates(latitude: float, longitude: float) -> bool:
        """Validate GPS coordinates for agricultural operations."""
        return -90 <= latitude <= 90 and -180 <= longitude <= 180

    @staticmethod
    def validate_field_id(field_id: str) -> bool:
        """Validate field identifier format."""
        import re

        pattern = r"^[A-Z]{1,5}-\d{3,5}$"  # e.g., "FIELD-A001", "A-12345"
        return bool(re.match(pattern, field_id))

    @staticmethod
    def validate_equipment_id(equipment_id: str) -> bool:
        """Validate equipment identifier format."""
        import re

        pattern = r"^[A-Z]{3,5}-\d{3}$"  # e.g., "TRC-001", "PLT-123"
        return bool(re.match(pattern, equipment_id))

    @staticmethod
    def validate_soil_moisture(value: float) -> bool:
        """Validate soil moisture percentage."""
        return 0 <= value <= 100

    @staticmethod
    def validate_soil_ph(value: float) -> bool:
        """Validate soil pH value."""
        return 0 <= value <= 14

    @staticmethod
    def validate_temperature_celsius(value: float) -> bool:
        """Validate temperature in Celsius."""
        return -50 <= value <= 60

    @staticmethod
    def validate_pressure_psi(value: float) -> bool:
        """Validate pressure in PSI."""
        return 0 <= value <= 5000

    @staticmethod
    def validate_speed_mph(value: float) -> bool:
        """Validate speed in miles per hour."""
        return 0 <= value <= 50


# Response helper functions
def create_success_response(
    data: Any = None,
    message: str | None = None,
    pagination: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> StandardResponse:
    """Create a standardized success response."""
    return StandardResponse(
        success=True,
        data=data,
        message=message,
        pagination=pagination,
        request_id=request_id,
    )


def create_error_response(
    error_code: str,
    message: str,
    severity: str = "medium",
    category: str = "validation",
    field: str | None = None,
    value: Any | None = None,
    equipment_id: str | None = None,
    field_id: str | None = None,
    operation_type: str | None = None,
    recovery_suggestions: list[str] | None = None,
    request_id: str | None = None,
) -> ErrorResponse:
    """Create a standardized error response."""
    error_detail = ErrorDetail(
        code=error_code,
        message=message,
        severity=severity,
        category=category,
        field=field,
        value=value,
        equipment_id=equipment_id,
        field_id=field_id,
        operation_type=operation_type,
        recovery_suggestions=recovery_suggestions or [],
    )

    return ErrorResponse(
        success=False,
        error=error_detail.model_dump(),
        recovery_suggestions=error_detail.recovery_suggestions,
        request_id=request_id,
    )


def create_paginated_response(
    data: list[Any], total: int, page: int, page_size: int, request_id: str | None = None
) -> PaginatedResponse:
    """Create a standardized paginated response."""
    total_pages = max(1, (total + page_size - 1) // page_size)

    return PaginatedResponse(
        success=True,
        data=data,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
        request_id=request_id,
    )
