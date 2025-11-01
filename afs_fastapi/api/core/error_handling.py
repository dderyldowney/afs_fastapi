"""
Comprehensive error handling framework for AFS FastAPI agricultural operations.

This module provides standardized error handling, validation, and response
formatting for all API endpoints with agricultural robotics context.
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Configure logging for API error handling
logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """Standardized error codes for agricultural API operations."""

    # Validation Errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FIELD_FORMAT = "INVALID_FIELD_FORMAT"

    # Authentication & Authorization
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"

    # Resource Errors
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"

    # Business Logic Errors
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"

    # Agricultural Specific Errors
    EQUIPMENT_NOT_AVAILABLE = "EQUIPMENT_NOT_AVAILABLE"
    SAFETY_PROTOCOL_VIOLATION = "SAFETY_PROTOCOL_VIOLATION"
    ISOBUS_COMMUNICATION_ERROR = "ISOBUS_COMMUNICATION_ERROR"
    FIELD_COORDINATION_CONFLICT = "FIELD_COORDINATION_CONFLICT"
    WEATHER_CONDITIONS_UNSAFE = "WEATHER_CONDITIONS_UNSAFE"
    SOIL_CONDITIONS_UNSUITABLE = "SOIL_CONDITIONS_UNSUITABLE"

    # System Errors
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIME_OUT = "TIME_OUT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Agricultural Compliance Errors
    ISO_11783_VIOLATION = "ISO_11783_VIOLATION"
    ISO_18497_VIOLATION = "ISO_18497_VIOLATION"
    AGRICULTURAL_STANDARD_VIOLATION = "AGRICULTURAL_STANDARD_VIOLATION"


class ErrorSeverity(str, Enum):
    """Error severity levels for agricultural operations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for agricultural API operations."""

    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    BUSINESS_LOGIC = "business_logic"
    AGRICULTURAL_SAFETY = "agricultural_safety"
    SYSTEM = "system"
    COMPLIANCE = "compliance"


class AgriculturalErrorDetails(BaseModel):
    """Detailed error information for agricultural compliance."""

    code: ErrorCode = Field(..., description="Standardized error code")
    severity: ErrorSeverity = Field(..., description="Error severity level")
    category: ErrorCategory = Field(..., description="Error category")
    message: str = Field(..., description="Human-readable error message")
    technical_details: str | None = Field(None, description="Technical error details")
    equipment_id: str | None = Field(None, description="Affected equipment ID")
    field_id: str | None = Field(None, description="Affected field ID")
    operation_type: str | None = Field(None, description="Type of operation")
    agricultural_context: dict[str, Any] | None = Field(
        None, description="Agricultural-specific error context"
    )
    recovery_suggestions: list[str] = Field(
        default_factory=list, description="Suggested recovery actions"
    )
    iso_violation_details: dict[str, Any] | None = Field(
        None, description="ISO standard violation details"
    )


class APIErrorResponse(BaseModel):
    """Standardized error response format for all API endpoints."""

    success: bool = Field(False, description="Request success status")
    error: AgriculturalErrorDetails = Field(..., description="Error details")
    request_id: str | None = Field(None, description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    path: str | None = Field(None, description="API endpoint path")
    method: str | None = Field(None, description="HTTP method")


class StandardResponse(BaseModel):
    """Standardized success response format for all API endpoints."""

    success: bool = Field(True, description="Request success status")
    data: Any | None = Field(None, description="Response data")
    message: str | None = Field(None, description="Success message")
    request_id: str | None = Field(None, description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    pagination: dict[str, Any] | None = Field(
        None, description="Pagination information for list responses"
    )


class PaginatedResponse(BaseModel):
    """Standardized paginated response format."""

    success: bool = Field(True, description="Request success status")
    data: list[Any] = Field(..., description="Response data items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")
    request_id: str | None = Field(None, description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class AgriculturalValidationError(Exception):
    """Exception for agricultural validation errors."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.VALIDATION_ERROR,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.VALIDATION,
        equipment_id: str | None = None,
        field_id: str | None = None,
        operation_type: str | None = None,
        agricultural_context: dict[str, Any] | None = None,
        recovery_suggestions: list[str] | None = None,
    ):
        """Initialize agricultural validation error."""
        self.error_details = AgriculturalErrorDetails(
            code=error_code,
            severity=severity,
            category=category,
            message=message,
            equipment_id=equipment_id,
            field_id=field_id,
            operation_type=operation_type,
            agricultural_context=agricultural_context,
            recovery_suggestions=recovery_suggestions or [],
        )
        super().__init__(message)


class AgriculturalBusinessError(Exception):
    """Exception for agricultural business logic errors."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        severity: ErrorSeverity = ErrorSeverity.HIGH,
        category: ErrorCategory = ErrorCategory.BUSINESS_LOGIC,
        equipment_id: str | None = None,
        field_id: str | None = None,
        operation_type: str | None = None,
        agricultural_context: dict[str, Any] | None = None,
        iso_violation_details: dict[str, Any] | None = None,
        recovery_suggestions: list[str] | None = None,
    ):
        """Initialize agricultural business error."""
        self.error_details = AgriculturalErrorDetails(
            code=error_code,
            severity=severity,
            category=category,
            message=message,
            equipment_id=equipment_id,
            field_id=field_id,
            operation_type=operation_type,
            agricultural_context=agricultural_context,
            iso_violation_details=iso_violation_details,
            recovery_suggestions=recovery_suggestions or [],
        )
        super().__init__(message)


class AgriculturalSafetyError(Exception):
    """Exception for agricultural safety-related errors."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        severity: ErrorSeverity = ErrorSeverity.CRITICAL,
        category: ErrorCategory = ErrorCategory.AGRICULTURAL_SAFETY,
        equipment_id: str | None = None,
        field_id: str | None = None,
        operation_type: str | None = None,
        agricultural_context: dict[str, Any] | None = None,
        iso_violation_details: dict[str, Any] | None = None,
        recovery_suggestions: list[str] | None = None,
    ):
        """Initialize agricultural safety error."""
        self.error_details = AgriculturalErrorDetails(
            code=error_code,
            severity=severity,
            category=category,
            message=message,
            equipment_id=equipment_id,
            field_id=field_id,
            operation_type=operation_type,
            agricultural_context=agricultural_context,
            iso_violation_details=iso_violation_details,
            recovery_suggestions=recovery_suggestions or [],
        )
        super().__init__(message)


def create_error_response(
    error_details: AgriculturalErrorDetails | None = None,
    request: Request | None = None,
    request_id: str | None = None,
    error_code: ErrorCode | None = None,
    message: str | None = None,
    severity: str = "medium",
    category: str = "validation",
    equipment_id: str | None = None,
    field_id: str | None = None,
    recovery_suggestions: list[str] | None = None,
) -> APIErrorResponse:
    """Create standardized error response."""
    # Create error details if not provided
    if error_details is None:
        if error_code is None or message is None:
            raise ValueError("Either error_details or both error_code and message must be provided")

        error_details = AgriculturalErrorDetails(
            code=error_code,
            severity=ErrorSeverity(severity),
            category=ErrorCategory(category),
            message=message,
            equipment_id=equipment_id,
            field_id=field_id,
            recovery_suggestions=recovery_suggestions or [],
        )

    response = APIErrorResponse(
        error=error_details,
        request_id=request_id or _generate_request_id(),
        path=str(request.url) if request else None,
        method=request.method if request else None,
    )

    # Convert datetime to string for JSON serialization
    response_dict = response.model_dump()
    if "timestamp" in response_dict:
        response_dict["timestamp"] = response_dict["timestamp"].isoformat()

    return response_dict


def create_success_response(
    data: Any = None,
    message: str | None = None,
    request_id: str | None = None,
    pagination: dict[str, Any] | None = None,
) -> StandardResponse:
    """Create standardized success response."""
    return StandardResponse(
        data=data,
        message=message,
        request_id=request_id or _generate_request_id(),
        pagination=pagination,
    )


def create_paginated_response(
    data: list[Any],
    total: int,
    page: int,
    page_size: int,
    request_id: str | None = None,
) -> PaginatedResponse:
    """Create standardized paginated response."""
    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
        request_id=request_id or _generate_request_id(),
    )


def _generate_request_id() -> str:
    """Generate unique request identifier."""
    import uuid

    return str(uuid.uuid4())


# Error handlers for FastAPI
def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle validation exceptions."""
    logger.warning(f"Validation error: {exc}")

    error_details = AgriculturalErrorDetails(
        error_code=ErrorCode.VALIDATION_ERROR,
        severity=ErrorSeverity.MEDIUM,
        category=ErrorCategory.VALIDATION,
        message=str(exc),
        technical_details="Input validation failed",
        recovery_suggestions=[
            "Check input data types and formats",
            "Validate required fields are present",
            "Ensure numeric values are within valid ranges",
        ],
    )

    response = create_error_response(error_details, request)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.model_dump(),
    )


def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")

    # Map HTTP status codes to our error codes
    error_mapping = {
        status.HTTP_400_BAD_REQUEST: ErrorCode.INVALID_INPUT,
        status.HTTP_401_UNAUTHORIZED: ErrorCode.UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN: ErrorCode.FORBIDDEN,
        status.HTTP_404_NOT_FOUND: ErrorCode.RESOURCE_NOT_FOUND,
        status.HTTP_409_CONFLICT: ErrorCode.RESOURCE_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_ENTITY: ErrorCode.VALIDATION_ERROR,
        status.HTTP_429_TOO_MANY_REQUESTS: ErrorCode.RATE_LIMIT_EXCEEDED,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorCode.INTERNAL_SERVER_ERROR,
        status.HTTP_503_SERVICE_UNAVAILABLE: ErrorCode.SERVICE_UNAVAILABLE,
    }

    error_code = error_mapping.get(exc.status_code, ErrorCode.INTERNAL_SERVER_ERROR)

    error_details = AgriculturalErrorDetails(
        error_code=error_code,
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.SYSTEM,
        message=str(exc.detail),
        technical_details=f"HTTP {exc.status_code}",
        recovery_suggestions=[
            "Check request parameters",
            "Verify API authentication",
            "Try again later",
        ],
    )

    response = create_error_response(error_details, request)
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(),
    )


def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    error_details = AgriculturalErrorDetails(
        error_code=ErrorCode.INTERNAL_SERVER_ERROR,
        severity=ErrorSeverity.CRITICAL,
        category=ErrorCategory.SYSTEM,
        message="An unexpected error occurred",
        technical_details="Internal server error",
        recovery_suggestions=[
            "Contact system administrator",
            "Check server logs for details",
            "Try again later",
        ],
    )

    response = create_error_response(error_details, request)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(),
    )


def agricultural_safety_exception_handler(
    request: Request, exc: AgriculturalSafetyError
) -> JSONResponse:
    """Handle agricultural safety exceptions."""
    logger.critical(f"Safety error: {exc}")

    response = create_error_response(exc.error_details, request)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=response.model_dump(),
    )


def agricultural_business_exception_handler(
    request: Request, exc: AgriculturalBusinessError
) -> JSONResponse:
    """Handle agricultural business logic exceptions."""
    logger.warning(f"Business logic error: {exc}")

    response = create_error_response(exc.error_details, request)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=response.model_dump(),
    )


def agricultural_validation_exception_handler(
    request: Request, exc: AgriculturalValidationError
) -> JSONResponse:
    """Handle agricultural validation exceptions."""
    logger.warning(f"Validation error: {exc}")

    response = create_error_response(exc.error_details, request)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.model_dump(),
    )
