#!/usr/bin/env python3
"""
AI Processing API Schemas for AFS FastAPI Platform.

Pydantic models for AI processing pipeline endpoints, providing type-safe
request/response schemas for agricultural robotics AI optimization services.

Agricultural Context:
Defines data structures for safety-critical AI processing operations,
ensuring proper validation and serialization of agricultural equipment
communication, monitoring data, and fleet coordination messages.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class OptimizationLevelEnum(str, Enum):
    """AI processing optimization intensity levels."""

    CONSERVATIVE = "conservative"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"
    ADAPTIVE = "adaptive"


class TargetFormatEnum(str, Enum):
    """Target output format for AI processing."""

    STANDARD = "standard"
    BRIEF = "brief"
    BULLET_POINTS = "bullet_points"


class AIProcessingRequest(BaseModel):
    """Request model for AI processing pipeline operations."""

    user_input: str = Field(
        ...,
        description="Input text to process (equipment commands, monitoring data, fleet coordination)",
        min_length=1,
        max_length=10000,
        example="Coordinate tractor fleet for field cultivation with safety protocols",
    )

    service_name: str | None = Field(
        default="platform",
        description="Calling service name for tracking and configuration",
        example="equipment",
    )

    optimization_level: OptimizationLevelEnum | None = Field(
        default=None,
        description="Optimization intensity (defaults to service configuration)",
        example="standard",
    )

    target_format: TargetFormatEnum | None = Field(
        default="standard", description="Desired output format", example="brief"
    )

    token_budget: int | None = Field(
        default=None,
        description="Maximum token budget for processing",
        ge=100,
        le=8000,
        example=2000,
    )

    context_data: dict[str, Any] | None = Field(
        default=None,
        description="Additional context for agricultural operations",
        example={"equipment_id": "TRACTOR_01", "field_id": "FIELD_A", "operation": "cultivation"},
    )


class AIProcessingResponse(BaseModel):
    """Response model for AI processing pipeline operations."""

    final_output: str = Field(
        ...,
        description="Optimized output text",
        example="Tractor fleet coordination initiated for cultivation with ISO safety compliance",
    )

    total_tokens_saved: int = Field(
        ..., description="Total tokens saved through optimization", ge=0, example=150
    )

    stages_completed: int = Field(
        ..., description="Number of pipeline stages completed", ge=0, le=4, example=4
    )

    agricultural_compliance_maintained: bool = Field(
        ..., description="Whether agricultural safety compliance was preserved", example=True
    )

    optimization_level: OptimizationLevelEnum = Field(
        ..., description="Applied optimization level", example="standard"
    )

    optimization_applied: bool = Field(
        ..., description="Whether optimization was successfully applied", example=True
    )

    estimated_tokens: int = Field(
        ..., description="Estimated token count of final output", ge=0, example=320
    )

    budget_exceeded: bool = Field(
        ..., description="Whether token budget was exceeded", example=False
    )

    fallback_used: bool = Field(
        ..., description="Whether fallback processing was used", example=False
    )

    metrics: dict[str, Any] = Field(
        ...,
        description="Detailed processing metrics",
        example={
            "processing_time_ms": 25.3,
            "optimization_ratio": 0.32,
            "stage_breakdown": {
                "pre_fill": 45,
                "prompt_processing": 23,
                "generation": 67,
                "decoding": 15,
            },
        },
    )


class EquipmentOptimizationRequest(BaseModel):
    """Request model for equipment communication optimization."""

    message: str = Field(
        ...,
        description="Equipment communication message (ISOBUS, safety protocols)",
        min_length=1,
        max_length=5000,
        example="ISOBUS: Emergency stop initiated for tractor TRC001 in field A7",
    )

    equipment_id: str | None = Field(
        default=None, description="Equipment identifier for tracking", example="TRC001"
    )

    priority: str | None = Field(
        default="high", description="Message priority level", example="critical"
    )


class MonitoringOptimizationRequest(BaseModel):
    """Request model for monitoring data optimization."""

    sensor_data: str = Field(
        ...,
        description="Sensor reading or monitoring data",
        min_length=1,
        max_length=5000,
        example="Soil moisture: 34.2%, pH: 6.8, nitrogen: 120ppm, temperature: 22.1C",
    )

    sensor_id: str | None = Field(
        default=None, description="Sensor identifier for tracking", example="SOIL_001"
    )

    data_type: str | None = Field(
        default="general", description="Type of monitoring data", example="soil_quality"
    )


class FleetOptimizationRequest(BaseModel):
    """Request model for fleet coordination optimization."""

    coordination_message: str = Field(
        ...,
        description="Fleet coordination message or command",
        min_length=1,
        max_length=5000,
        example="Coordinate tractors TRC001, TRC002, TRC003 for parallel cultivation of field sectors A1-A5",
    )

    fleet_operation: str | None = Field(
        default="coordination", description="Type of fleet operation", example="cultivation"
    )

    tractor_count: int | None = Field(
        default=None, description="Number of tractors involved", ge=1, le=20, example=3
    )


class PlatformStatisticsResponse(BaseModel):
    """Response model for platform AI processing statistics."""

    global_stats: dict[str, Any] = Field(
        ...,
        description="Global processing statistics",
        example={
            "total_requests": 1247,
            "tokens_saved": 45621,
            "agricultural_requests": 892,
            "safety_critical_requests": 156,
        },
    )

    service_stats: dict[str, Any] = Field(
        ...,
        description="Per-service processing statistics",
        example={
            "equipment": {
                "optimization_level": "conservative",
                "priority": "high",
                "requests_processed": 456,
                "tokens_saved": 12890,
            }
        },
    )

    configuration: dict[str, Any] = Field(
        ...,
        description="Current platform configuration",
        example={
            "agricultural_safety_mode": True,
            "default_optimization_level": "standard",
            "token_budget": 4000,
        },
    )

    pipeline_health: dict[str, Any] = Field(
        ...,
        description="Pipeline health indicators",
        example={
            "total_services_registered": 5,
            "agricultural_request_ratio": 0.72,
            "average_tokens_saved": 36.6,
        },
    )


class HealthCheckResponse(BaseModel):
    """Response model for AI processing health check."""

    status: str = Field(..., description="Overall health status", example="healthy")

    pipeline_operational: bool = Field(
        ..., description="Whether AI processing pipeline is operational", example=True
    )

    services_registered: int = Field(
        ..., description="Number of registered services", ge=0, example=5
    )

    total_requests_processed: int = Field(
        ..., description="Total requests processed since startup", ge=0, example=1247
    )

    test_processing_success: bool = Field(
        ..., description="Whether test processing succeeded", example=True
    )

    agricultural_safety_mode: bool = Field(
        ..., description="Whether agricultural safety mode is enabled", example=True
    )

    error: str | None = Field(default=None, description="Error message if unhealthy", example=None)
