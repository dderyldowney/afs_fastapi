"""
Modernized monitoring API endpoints with comprehensive error handling and validation.

This module provides RESTful endpoints for agricultural environmental monitoring
with proper validation, error handling, and ISO compliance.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from afs_fastapi.api.core.error_handling import (
    AgriculturalValidationError,
    ErrorCode,
    create_error_response,
)
from afs_fastapi.api.core.response_models import (
    MonitoringDataResponse,
    PaginatedResponse,
    StandardResponse,
)
from afs_fastapi.api.core.validation_schemas import (
    CommonQueryParams,
    SoilSensorRequest,
    WaterQualityRequest,
    validate_agricultural_data,
)
from afs_fastapi.monitoring.soil_monitor import SoilMonitor
from afs_fastapi.monitoring.water_monitor import WaterMonitor

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/soil/readings",
    response_model=MonitoringDataResponse,
    tags=["monitoring"],
    summary="Submit soil sensor readings",
    description="Submit soil quality measurements from field sensors for agricultural monitoring.",
)
async def submit_soil_reading(
    request: Request, soil_request: SoilSensorRequest
) -> MonitoringDataResponse:
    """
    Submit soil sensor readings for agricultural monitoring.

    Accepts comprehensive soil data including:
    - Moisture content and distribution
    - pH levels and acidity/alkalinity
    - Nutrient levels (NPK, micronutrients)
    - Temperature and soil composition
    - Electrical conductivity and salinity
    - Organic matter content

    Agricultural Context:
    Supports precision agriculture practices, irrigation scheduling,
    fertilization optimization, and soil health monitoring.

    ISO Compliance:
    Follows ISO 11783 agricultural data standards for sensor
    readings and soil measurement protocols.
    """
    try:
        # Validate agricultural data
        validated_data = validate_agricultural_data(soil_request.readings)

        # Create soil monitor instance
        SoilMonitor(soil_request.sensor_id)

        # Validate soil-specific measurements
        moisture = validated_data.get("moisture_percent", 0)
        ph = validated_data.get("ph", 7.0)
        temperature = validated_data.get("temperature_celsius", 20.0)

        # Agricultural-specific validation
        if moisture < 10 and ph > 7.5:
            raise AgriculturalValidationError(
                "Low moisture with high pH may indicate poor soil conditions",
                field_id=soil_request.location if hasattr(soil_request, "field_id") else None,
            )

        # Store the reading (in real implementation)
        logger.info(f"Received soil reading from {soil_request.sensor_id}: {validated_data}")

        # Prepare response with agricultural metrics
        agricultural_metrics = {
            "irrigation_recommendation": "optimal" if 30 <= moisture <= 70 else "required",
            "fertilization_needs": "high" if ph < 6.0 or ph > 8.0 else "normal",
            "planting_readiness": "suitable" if temperature >= 10 else "unsuitable",
            "soil_health_score": calculate_soil_health_score(validated_data),
            "seasonal_adjustment": get_seasonal_adjustment(),
        }

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "sensor_id": soil_request.sensor_id,
                    "agricultural_metrics": agricultural_metrics,
                },
                "timestamp": "2024-01-01T12:00:00Z",
                "request_id": str(request.url),
            },
        )

    except AgriculturalValidationError as e:
        response = create_error_response(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=str(e),
            severity="medium",
            category="validation",
            recovery_suggestions=[
                "Check sensor calibration status",
                "Verify soil measurement procedures",
                "Consult soil science guidelines",
                "Validate sensor location",
            ],
        )
        return JSONResponse(status_code=422, content=response.model_dump())

    except Exception as e:
        logger.error(f"Error processing soil reading from {soil_request.sensor_id}: {e}")
        response = create_error_response(
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=f"Failed to process soil reading: {str(e)}",
            severity="high",
            category="system",
            recovery_suggestions=[
                "Check sensor connectivity",
                "Verify data transmission integrity",
                "Validate sensor maintenance schedule",
                "Contact technical support",
            ],
        )
        return JSONResponse(status_code=500, content=response.model_dump())


@router.get(
    "/soil/readings",
    response_model=PaginatedResponse,
    tags=["monitoring"],
    summary="Get soil sensor readings",
    description="Retrieve soil quality measurements from field sensors with filtering and pagination.",
)
async def get_soil_readings(
    request: Request,
    sensor_id: str | None = None,
    field_id: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    data_quality: str | None = None,
    page: int = 1,
    page_size: int = 20,
    query_params: CommonQueryParams = Depends(),
) -> PaginatedResponse:
    """
    Retrieve soil sensor readings with comprehensive filtering.

    Provides filtered access to soil monitoring data including:
    - Historical moisture and temperature data
    - pH and nutrient level trends
    - Soil composition changes over time
    - Data quality assessments
    - Agricultural recommendations based on readings

    Agricultural Context:
    Supports trend analysis, seasonal monitoring, and data-driven
    agricultural decision making for soil management.
    """
    try:
        # Simulate soil readings database
        all_readings = [
            {
                "sensor_id": "SOI-001",
                "location": {"latitude": 40.7128, "longitude": -74.0060},
                "readings": {
                    "moisture_percent": 34.2,
                    "ph": 6.8,
                    "temperature_celsius": 22.1,
                    "nitrogen_ppm": 120,
                    "phosphorus_ppm": 45,
                    "potassium_ppm": 180,
                },
                "timestamp": "2024-01-01T12:00:00Z",
                "data_quality": "good",
            },
            {
                "sensor_id": "SOI-002",
                "location": {"latitude": 40.7589, "longitude": -73.9851},
                "readings": {
                    "moisture_percent": 28.5,
                    "ph": 7.2,
                    "temperature_celsius": 21.8,
                    "nitrogen_ppm": 95,
                    "phosphorus_ppm": 38,
                    "potassium_ppm": 165,
                },
                "timestamp": "2024-01-01T11:30:00Z",
                "data_quality": "good",
            },
        ]

        # Apply filters
        filtered_readings = all_readings

        if sensor_id:
            filtered_readings = [r for r in filtered_readings if r["sensor_id"] == sensor_id]

        if data_quality:
            filtered_readings = [r for r in filtered_readings if r["data_quality"] == data_quality]

        if start_time:
            filtered_readings = [
                r
                for r in filtered_readings
                if datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")) >= start_time
            ]

        if end_time:
            filtered_readings = [
                r
                for r in filtered_readings
                if datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")) <= end_time
            ]

        # Sort results
        sort_key = query_params.sort_by or "timestamp"
        reverse_order = query_params.sort_order == "desc"
        filtered_readings.sort(key=lambda x: x.get(sort_key, ""), reverse=reverse_order)

        # Apply pagination
        len(filtered_readings)
        start_idx = (query_params.page - 1) * query_params.page_size
        end_idx = start_idx + query_params.page_size
        paginated_readings = filtered_readings[start_idx:end_idx]

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": paginated_readings,
                "pagination": {
                    "page": query_params.page,
                    "page_size": query_params.page_size,
                },
                "timestamp": "2024-01-01T12:00:00Z",
                "request_id": str(request.url),
            },
        )

    except Exception as e:
        logger.error(f"Error retrieving soil readings: {e}")
        response = create_error_response(
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=f"Failed to retrieve soil readings: {str(e)}",
            severity="high",
            category="system",
            recovery_suggestions=[
                "Check database connectivity",
                "Verify query parameters",
                "Contact system administrator",
            ],
        )
        return JSONResponse(status_code=500, content=response.model_dump())


@router.post(
    "/water/readings",
    response_model=MonitoringDataResponse,
    tags=["monitoring"],
    summary="Submit water quality readings",
    description="Submit water quality measurements from irrigation and drainage monitoring systems.",
)
async def submit_water_reading(
    request: Request, water_request: WaterQualityRequest
) -> MonitoringDataResponse:
    """
    Submit water quality readings for agricultural monitoring.

    Accepts comprehensive water quality data including:
    - pH levels and acidity/alkalinity
    - Temperature and dissolved oxygen
    - Turbidity and clarity measurements
    - Nutrient content (nitrates, phosphates)
    - Electrical conductivity and TDS
    - Contaminant levels and pollutants

    Agricultural Context:
    Supports irrigation water quality monitoring, environmental
    compliance tracking, and sustainable water management practices.

    ISO Compliance:
    Follows ISO 11783 water quality monitoring standards and
    agricultural water usage guidelines.
    """
    try:
        # Validate agricultural water data
        validated_data = validate_agricultural_data(water_request.readings)

        # Create water monitor instance
        WaterMonitor(water_request.sensor_id)

        # Validate water-specific measurements
        ph = validated_data.get("ph", 7.0)
        turbidity = validated_data.get("turbidity_ntu", 0)
        dissolved_oxygen = validated_data.get("dissolved_oxygen_ppm", 8.0)

        # Agricultural-specific validation
        if ph < 6.0 or ph > 9.0:
            raise AgriculturalValidationError(
                "Water pH outside optimal range for agricultural use",
                field_id=water_request.location if hasattr(water_request, "field_id") else None,
            )

        if dissolved_oxygen < 5.0:
            raise AgriculturalValidationError(
                "Low dissolved oxygen may indicate poor water quality",
                field_id=water_request.location if hasattr(water_request, "field_id") else None,
            )

        # Store the reading (in real implementation)
        logger.info(f"Received water reading from {water_request.sensor_id}: {validated_data}")

        # Prepare response with agricultural metrics
        agricultural_metrics = {
            "irrigation_suitability": (
                "excellent" if 6.5 <= ph <= 8.5 and turbidity < 10 else "moderate"
            ),
            "environmental_compliance": "compliant" if turbidity < 25 else "requires_attention",
            "aeration_required": "yes" if dissolved_oxygen < 6.0 else "no",
            "water_quality_score": calculate_water_quality_score(validated_data),
            "seasonal_adjustment": get_seasonal_adjustment(),
        }

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "sensor_id": water_request.sensor_id,
                    "agricultural_metrics": agricultural_metrics,
                },
                "timestamp": "2024-01-01T12:00:00Z",
                "request_id": str(request.url),
            },
        )

    except AgriculturalValidationError as e:
        response = create_error_response(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=str(e),
            severity="high",
            category="validation",
            recovery_suggestions=[
                "Check water source quality",
                "Verify irrigation system maintenance",
                "Consult water quality guidelines",
                "Test water supply regularly",
            ],
        )
        return JSONResponse(status_code=422, content=response.model_dump())

    except Exception as e:
        logger.error(f"Error processing water reading from {water_request.sensor_id}: {e}")
        response = create_error_response(
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=f"Failed to process water reading: {str(e)}",
            severity="high",
            category="system",
            recovery_suggestions=[
                "Check water sensor connectivity",
                "Verify data transmission integrity",
                "Validate sensor maintenance schedule",
                "Contact technical support",
            ],
        )
        return JSONResponse(status_code=500, content=response.model_dump())


@router.get(
    "/water/readings",
    response_model=PaginatedResponse,
    tags=["monitoring"],
    summary="Get water quality readings",
    description="Retrieve water quality measurements from irrigation and drainage systems with filtering.",
)
async def get_water_readings(
    request: Request,
    sensor_id: str | None = Query(None, description="Filter by sensor ID"),
    location: str | None = Query(None, description="Filter by location"),
    start_time: datetime | None = Query(None, description="Start time filter"),
    end_time: datetime | None = Query(None, description="End time filter"),
    quality_threshold: float | None = Query(None, description="Quality threshold filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    query_params: CommonQueryParams = Depends(),
) -> PaginatedResponse:
    """
    Retrieve water quality readings with comprehensive filtering.

    Provides filtered access to water monitoring data including:
    - Historical water quality trends
    - Irrigation system performance
    - Environmental compliance monitoring
    - Water usage efficiency metrics
    - Contaminant level tracking

    Agricultural Context:
    Supports sustainable water management, environmental compliance,
    and irrigation optimization for agricultural operations.
    """
    try:
        # Simulate water readings database
        all_readings = [
            {
                "sensor_id": "WAT-001",
                "location": {"latitude": 40.7128, "longitude": -74.0060},
                "readings": {
                    "ph": 7.2,
                    "turbidity_ntu": 12.5,
                    "temperature_celsius": 18.7,
                    "dissolved_oxygen_ppm": 8.4,
                    "nitrate_ppm": 5.2,
                    "phosphate_ppm": 0.8,
                },
                "timestamp": "2024-01-01T12:00:00Z",
                "data_quality": "good",
            },
            {
                "sensor_id": "WAT-002",
                "location": {"latitude": 40.7589, "longitude": -73.9851},
                "readings": {
                    "ph": 6.9,
                    "turbidity_ntu": 8.3,
                    "temperature_celsius": 19.2,
                    "dissolved_oxygen_ppm": 7.8,
                    "nitrate_ppm": 4.1,
                    "phosphate_ppm": 0.6,
                },
                "timestamp": "2024-01-01T11:30:00Z",
                "data_quality": "excellent",
            },
        ]

        # Apply filters
        filtered_readings = all_readings

        if sensor_id:
            filtered_readings = [r for r in filtered_readings if r["sensor_id"] == sensor_id]

        if quality_threshold:
            filtered_readings = [
                r
                for r in filtered_readings
                if calculate_water_quality_score(r["readings"]) >= quality_threshold
            ]

        if start_time:
            filtered_readings = [
                r
                for r in filtered_readings
                if datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")) >= start_time
            ]

        if end_time:
            filtered_readings = [
                r
                for r in filtered_readings
                if datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")) <= end_time
            ]

        # Sort results
        sort_key = query_params.sort_by or "timestamp"
        reverse_order = query_params.sort_order == "desc"
        filtered_readings.sort(key=lambda x: x.get(sort_key, ""), reverse=reverse_order)

        # Apply pagination
        len(filtered_readings)
        start_idx = (query_params.page - 1) * query_params.page_size
        end_idx = start_idx + query_params.page_size
        paginated_readings = filtered_readings[start_idx:end_idx]

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": paginated_readings,
                "pagination": {
                    "page": query_params.page,
                    "page_size": query_params.page_size,
                },
                "timestamp": "2024-01-01T12:00:00Z",
                "request_id": str(request.url),
            },
        )

    except Exception as e:
        logger.error(f"Error retrieving water readings: {e}")
        response = create_error_response(
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=f"Failed to retrieve water readings: {str(e)}",
            severity="high",
            category="system",
            recovery_suggestions=[
                "Check database connectivity",
                "Verify query parameters",
                "Contact system administrator",
            ],
        )
        return JSONResponse(status_code=500, content=response.model_dump())


@router.get(
    "/sensor-status",
    tags=["monitoring"],
    summary="Get sensor network status",
    description="Get status information about all monitoring sensors in the agricultural network.",
)
async def get_sensor_status(request: Request) -> StandardResponse:
    """
    Get comprehensive sensor network status.

    Provides sensor network information including:
    - Individual sensor status and connectivity
    - Data transmission quality and reliability
    - Battery power levels and maintenance needs
    - Calibration schedules and last calibration dates
    - Sensor deployment locations and coverage
    - Alert conditions and warnings

    Agricultural Context:
    Supports sensor network management, maintenance scheduling,
    and ensuring continuous environmental monitoring coverage.
    """
    try:
        # Simulate sensor status data
        sensor_status_data = {
            "soil_sensors": [
                {
                    "sensor_id": "SOI-001",
                    "location": {"latitude": 40.7128, "longitude": -74.0060},
                    "status": "online",
                    "battery_level": 85,
                    "last_transmission": "2024-01-01T12:00:00Z",
                    "next_calibration": "2024-04-01T12:00:00Z",
                    "data_quality": "excellent",
                    "alerts": [],
                },
                {
                    "sensor_id": "SOI-002",
                    "location": {"latitude": 40.7589, "longitude": -73.9851},
                    "status": "online",
                    "battery_level": 45,
                    "last_transmission": "2024-01-01T11:30:00Z",
                    "next_calibration": "2024-03-15T12:00:00Z",
                    "data_quality": "good",
                    "alerts": ["Low battery warning"],
                },
            ],
            "water_sensors": [
                {
                    "sensor_id": "WAT-001",
                    "location": {"latitude": 40.7128, "longitude": -74.0060},
                    "status": "online",
                    "battery_level": 72,
                    "last_transmission": "2024-01-01T12:00:00Z",
                    "next_calibration": "2024-06-01T12:00:00Z",
                    "data_quality": "excellent",
                    "alerts": [],
                },
                {
                    "sensor_id": "WAT-002",
                    "location": {"latitude": 40.7129, "longitude": -74.0061},
                    "status": "offline",
                    "battery_level": 0,
                    "last_transmission": "2024-01-01T10:30:00Z",
                    "next_calibration": "2024-05-15T12:00:00Z",
                    "data_quality": "unknown",
                    "alerts": ["Sensor offline", "Low battery"],
                },
            ],
        }

        # Calculate summary statistics
        total_sensors = len(sensor_status_data["soil_sensors"]) + len(
            sensor_status_data["water_sensors"]
        )
        online_sensors = sum(
            1
            for sensor in sensor_status_data["soil_sensors"] + sensor_status_data["water_sensors"]
            if sensor["status"] == "online"
        )
        alert_count = sum(
            len(sensor["alerts"])
            for sensor in sensor_status_data["soil_sensors"] + sensor_status_data["water_sensors"]
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "sensor_network": sensor_status_data,
                    "summary": {
                        "total_sensors": total_sensors,
                        "online_sensors": online_sensors,
                        "offline_sensors": total_sensors - online_sensors,
                        "alert_count": alert_count,
                        "network_health": (
                            "good" if online_sensors >= total_sensors * 0.8 else "needs_attention"
                        ),
                    },
                },
                "timestamp": "2024-01-01T12:00:00Z",
                "request_id": str(request.url),
            },
        )

    except Exception as e:
        logger.error(f"Error retrieving sensor status: {e}")
        response = create_error_response(
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=f"Failed to retrieve sensor status: {str(e)}",
            severity="high",
            category="system",
            recovery_suggestions=[
                "Check sensor network connectivity",
                "Verify communication infrastructure",
                "Contact network administrator",
            ],
        )
        return JSONResponse(status_code=500, content=response.model_dump())


# Helper functions
def calculate_soil_health_score(readings: dict[str, float]) -> float:
    """Calculate soil health score from sensor readings."""
    score = 100.0

    # Moisture contribution (30% weight)
    moisture = readings.get("moisture_percent", 0)
    if 30 <= moisture <= 70:
        score += 10
    elif moisture < 20 or moisture > 80:
        score -= 20

    # pH contribution (30% weight)
    ph = readings.get("ph", 7.0)
    if 6.0 <= ph <= 7.5:
        score += 10
    elif ph < 5.5 or ph > 8.5:
        score -= 20

    # Nutrient levels (40% weight)
    nitrogen = readings.get("nitrogen_ppm", 0)
    phosphorus = readings.get("phosphorus_ppm", 0)
    potassium = readings.get("potassium_ppm", 0)

    if 100 <= nitrogen <= 200:
        score += 5
    else:
        score -= 5

    if 30 <= phosphorus <= 60:
        score += 5
    else:
        score -= 5

    if 100 <= potassium <= 200:
        score += 5
    else:
        score -= 5

    return max(0, min(100, score))


def calculate_water_quality_score(readings: dict[str, float]) -> float:
    """Calculate water quality score from sensor readings."""
    score = 100.0

    # pH contribution (25% weight)
    ph = readings.get("ph", 7.0)
    if 6.5 <= ph <= 8.5:
        score += 10
    elif ph < 6.0 or ph > 9.0:
        score -= 25

    # Turbidity contribution (25% weight)
    turbidity = readings.get("turbidity_ntu", 0)
    if turbidity < 10:
        score += 10
    elif turbidity < 25:
        score += 5
    else:
        score -= 20

    # Dissolved oxygen contribution (25% weight)
    dissolved_oxygen = readings.get("dissolved_oxygen_ppm", 8.0)
    if dissolved_oxygen >= 6.0:
        score += 10
    elif dissolved_oxygen >= 4.0:
        score += 5
    else:
        score -= 25

    # Temperature contribution (25% weight)
    temperature = readings.get("temperature_celsius", 20.0)
    if 10 <= temperature <= 25:
        score += 10
    elif temperature < 5 or temperature > 30:
        score -= 10

    return max(0, min(100, score))


def validate_reading_quality(readings: dict[str, float]) -> bool:
    """Validate the quality of soil sensor readings."""
    # Check for reasonable ranges
    if readings.get("moisture_percent", 0) < 0 or readings.get("moisture_percent", 0) > 100:
        return False

    if readings.get("ph", 0) < 0 or readings.get("ph", 0) > 14:
        return False

    if readings.get("temperature_celsius", 0) < -50 or readings.get("temperature_celsius", 0) > 60:
        return False

    return True


def validate_water_quality(readings: dict[str, float]) -> bool:
    """Validate the quality of water sensor readings."""
    # Check for reasonable ranges
    if readings.get("ph", 0) < 0 or readings.get("ph", 0) > 14:
        return False

    if readings.get("turbidity_ntu", 0) < 0 or readings.get("turbidity_ntu", 0) > 1000:
        return False

    if readings.get("dissolved_oxygen_ppm", 0) < 0 or readings.get("dissolved_oxygen_ppm", 0) > 20:
        return False

    return True


def get_seasonal_adjustment() -> dict[str, Any]:
    """Get seasonal adjustment factors for agricultural metrics."""
    # This would typically use actual seasonal data
    return {
        "season": "winter",
        "irrigation_adjustment": 0.8,
        "fertilization_adjustment": 0.6,
        "planting_readiness": "low",
        "recommended_actions": [
            "Monitor soil moisture",
            "Prepare equipment for spring",
            "Review planting schedule",
        ],
    }
