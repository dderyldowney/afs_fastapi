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
        examples=["Coordinate tractor fleet for field cultivation with safety protocols"],
    )

    service_name: str | None = Field(
        default="platform",
        description="Calling service name for tracking and configuration",
        examples=["equipment"],
    )

    optimization_level: OptimizationLevelEnum | None = Field(
        default=None,
        description="Optimization intensity (defaults to service configuration)",
        examples=["standard"],
    )

    target_format: TargetFormatEnum | None = Field(
        default=TargetFormatEnum.STANDARD, description="Desired output format", examples=["brief"]
    )

    token_budget: int | None = Field(
        default=None,
        description="Maximum token budget for processing",
        ge=100,
        le=8000,
        examples=[2000],
    )

    context_data: dict[str, Any] | None = Field(
        default=None,
        description="Additional context for agricultural operations",
        examples=[
            {"equipment_id": "TRACTOR_01", "field_id": "FIELD_A", "operation": "cultivation"}
        ],
    )


class AIProcessingResponse(BaseModel):
    """Response model for AI processing pipeline operations."""

    final_output: str = Field(
        ...,
        description="Optimized output text",
        examples=[
            "Tractor fleet coordination initiated for cultivation with ISO safety compliance"
        ],
    )

    total_tokens_saved: int = Field(
        ..., description="Total tokens saved through optimization", ge=0, examples=[150]
    )

    stages_completed: int = Field(
        ..., description="Number of pipeline stages completed", ge=0, le=4, examples=[4]
    )

    agricultural_compliance_maintained: bool = Field(
        ..., description="Whether agricultural safety compliance was preserved", examples=[True]
    )

    optimization_level: OptimizationLevelEnum = Field(
        ..., description="Applied optimization level", examples=["standard"]
    )

    optimization_applied: bool = Field(
        ..., description="Whether optimization was successfully applied", examples=[True]
    )

    estimated_tokens: int = Field(
        ..., description="Estimated token count of final output", ge=0, examples=[320]
    )

    budget_exceeded: bool = Field(
        ..., description="Whether token budget was exceeded", examples=[False]
    )

    fallback_used: bool = Field(
        ..., description="Whether fallback processing was used", examples=[False]
    )

    metrics: dict[str, Any] = Field(
        ...,
        description="Detailed processing metrics",
        examples=[
            {
                "processing_time_ms": 25.3,
                "optimization_ratio": 0.32,
                "stage_breakdown": {
                    "pre_fill": 45,
                    "prompt_processing": 23,
                    "generation": 67,
                    "decoding": 15,
                },
            }
        ],
    )


class EquipmentOptimizationRequest(BaseModel):
    """Request model for equipment communication optimization."""

    message: str = Field(
        ...,
        description="Equipment communication message (ISOBUS, safety protocols)",
        min_length=1,
        max_length=5000,
        examples=["ISOBUS: Emergency stop initiated for tractor TRC001 in field A7"],
    )

    equipment_id: str | None = Field(
        default=None, description="Equipment identifier for tracking", examples=["TRC001"]
    )

    priority: str | None = Field(
        default="high", description="Message priority level", examples=["critical"]
    )


class MonitoringOptimizationRequest(BaseModel):
    """Request model for monitoring data optimization."""

    sensor_data: str = Field(
        ...,
        description="Sensor reading or monitoring data",
        min_length=1,
        max_length=5000,
        examples=["Soil moisture: 34.2%, pH: 6.8, nitrogen: 120ppm, temperature: 22.1C"],
    )

    sensor_id: str | None = Field(
        default=None, description="Sensor identifier for tracking", examples=["SOIL_001"]
    )

    data_type: str | None = Field(
        default="general", description="Type of monitoring data", examples=["soil_quality"]
    )


class FleetOptimizationRequest(BaseModel):
    """Request model for fleet coordination optimization."""

    coordination_message: str = Field(
        ...,
        description="Fleet coordination message or command",
        min_length=1,
        max_length=5000,
        examples=[
            "Coordinate tractors TRC001, TRC002, TRC003 for parallel cultivation of field sectors A1-A5"
        ],
    )

    fleet_operation: str | None = Field(
        default="coordination", description="Type of fleet operation", examples=["cultivation"]
    )

    tractor_count: int | None = Field(
        default=None, description="Number of tractors involved", ge=1, le=20, examples=[3]
    )


class PlatformStatisticsResponse(BaseModel):
    """Response model for platform AI processing statistics."""

    global_stats: dict[str, Any] = Field(
        ...,
        description="Global processing statistics",
        examples=[
            {
                "total_requests": 1247,
                "tokens_saved": 45621,
                "agricultural_requests": 892,
                "safety_critical_requests": 156,
            }
        ],
    )

    service_stats: dict[str, Any] = Field(
        ...,
        description="Per-service processing statistics",
        examples=[
            {
                "equipment": {
                    "optimization_level": "conservative",
                    "priority": "high",
                    "requests_processed": 456,
                    "tokens_saved": 12890,
                }
            }
        ],
    )

    configuration: dict[str, Any] = Field(
        ...,
        description="Current platform configuration",
        examples=[
            {
                "agricultural_safety_mode": True,
                "default_optimization_level": "standard",
                "token_budget": 4000,
            }
        ],
    )

    pipeline_health: dict[str, Any] = Field(
        ...,
        description="Pipeline health indicators",
        examples=[
            {
                "total_services_registered": 5,
                "agricultural_request_ratio": 0.72,
                "average_tokens_saved": 36.6,
            }
        ],
    )


class HealthCheckResponse(BaseModel):
    """Response model for AI processing health check."""

    status: str = Field(..., description="Overall health status", examples=["healthy"])

    pipeline_operational: bool = Field(
        ..., description="Whether AI processing pipeline is operational", examples=[True]
    )

    services_registered: int = Field(
        ..., description="Number of registered services", ge=0, examples=[5]
    )

    total_requests_processed: int = Field(
        ..., description="Total requests processed since startup", ge=0, examples=[1247]
    )

    test_processing_success: bool = Field(
        ..., description="Whether test processing succeeded", examples=[True]
    )

    agricultural_safety_mode: bool = Field(
        ..., description="Whether agricultural safety mode is enabled", examples=[True]
    )

    error: str | None = Field(
        default=None, description="Error message if unhealthy", examples=[None]
    )
