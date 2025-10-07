import os

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from ..equipment.farm_tractors import FarmTractor, FarmTractorResponse
from models.field_segment import FieldSegment  # type: ignore
from ..monitoring.schemas import SoilReadingResponse, WaterQualityResponse
from ..monitoring.soil_monitor import SoilMonitor
from ..monitoring.water_monitor import WaterMonitor
from ..services import OptimizationLevel, ai_processing_manager
from ..services.crdt_manager import FieldAllocationCRDT  # type: ignore
from ..version import __version__
from .ai_processing_schemas import (
    AIProcessingRequest,
    AIProcessingResponse,
    EquipmentOptimizationRequest,
    FleetOptimizationRequest,
    HealthCheckResponse,
    MonitoringOptimizationRequest,
    OptimizationLevelEnum,
    PlatformStatisticsResponse,
)

app = FastAPI(
    title="Automated Farming System API",
    description="API for controlling farm equipment and monitoring conditions",
    version=__version__,
)

# Global instance of the FieldAllocationCRDT
field_allocation_crdt = FieldAllocationCRDT()

# Optional CORS configuration via env var AFS_CORS_ORIGINS (comma-separated)
_cors_origins = os.getenv("AFS_CORS_ORIGINS")
if _cors_origins:
    origins = [o.strip() for o in _cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/", tags=["meta"], summary="Welcome message")
async def read_root() -> dict[str, str]:
    """Root endpoint returning welcome message."""
    return {"message": "Welcome to the Agricultural Farm System API"}


@app.get("/health", tags=["meta"], summary="Health check")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/version", tags=["meta"], summary="API version")
async def api_version() -> dict[str, str]:
    """Version information endpoint."""
    return {"version": __version__}


@app.get(
    "/equipment/tractor/{tractor_id}",
    response_model=FarmTractorResponse,
    response_model_exclude_none=True,
    tags=["equipment"],
    summary="Get tractor status",
)
async def get_tractor_status(tractor_id: str) -> FarmTractorResponse:
    """Get status of a specific tractor.

    Notes
    -----
    This returns a Pydantic model (`FarmTractorResponse`) suitable for API clients.
    """
    # Implementation would fetch actual tractor status
    tractor = FarmTractor("John Deere", "9RX", 2023)
    return tractor.to_response(tractor_id=tractor_id)


@app.get(
    "/monitoring/soil/{sensor_id}",
    response_model=SoilReadingResponse,
    response_model_exclude_none=True,
    tags=["monitoring"],
    summary="Get soil readings",
)
async def get_soil_status(sensor_id: str) -> SoilReadingResponse:
    """Get soil monitoring data from a specific sensor."""
    monitor = SoilMonitor(sensor_id)
    return SoilReadingResponse(sensor_id=sensor_id, readings=monitor.get_soil_composition())


@app.get(
    "/monitoring/water/{sensor_id}",
    response_model=WaterQualityResponse,
    response_model_exclude_none=True,
    tags=["monitoring"],
    summary="Get water readings",
)
async def get_water_status(sensor_id: str) -> WaterQualityResponse:
    """Get water quality data from a specific sensor."""
    monitor = WaterMonitor(sensor_id)
    return WaterQualityResponse(sensor_id=sensor_id, readings=monitor.get_water_quality())


# ============================================================================
# AI Processing Pipeline Endpoints
# ============================================================================


@app.post(
    "/ai/process",
    response_model=AIProcessingResponse,
    response_model_exclude_none=True,
    tags=["ai-processing"],
    summary="Process text with AI optimization",
)
async def process_with_ai_optimization(request: AIProcessingRequest) -> AIProcessingResponse:
    """
    Process text input with AI optimization pipeline.

    Applies sophisticated token optimization while preserving agricultural
    safety compliance and technical accuracy. Supports multiple optimization
    levels and output formats for different use cases.

    Agricultural Context:
    Optimizes communication for multi-tractor coordination, equipment commands,
    monitoring data processing, and safety protocol messaging while maintaining
    compliance with ISO 11783 and ISO 18497 agricultural standards.
    """
    # Convert enum to OptimizationLevel if provided
    optimization_level = None
    if request.optimization_level:
        optimization_level = OptimizationLevel(request.optimization_level.value)

    # Process with or without budget constraint
    if request.token_budget:
        result = ai_processing_manager.process_with_budget_constraint(
            user_input=request.user_input,
            token_budget=request.token_budget,
            service_name=request.service_name or "platform",
        )
    else:
        result = ai_processing_manager.process_agricultural_request(
            user_input=request.user_input,
            service_name=request.service_name or "platform",
            optimization_level=optimization_level,
            context_data=request.context_data,
        )

    return AIProcessingResponse(
        final_output=result.final_output,
        total_tokens_saved=result.total_tokens_saved,
        stages_completed=result.stages_completed,
        agricultural_compliance_maintained=result.agricultural_compliance_maintained,
        optimization_level=OptimizationLevelEnum(result.optimization_level.value),
        optimization_applied=result.optimization_applied,
        estimated_tokens=result.estimated_tokens,
        budget_exceeded=result.budget_exceeded,
        fallback_used=result.fallback_used,
        metrics=result.metrics,
    )


@app.post(
    "/ai/equipment/optimize",
    response_model=AIProcessingResponse,
    response_model_exclude_none=True,
    tags=["ai-processing", "equipment"],
    summary="Optimize equipment communication",
)
async def optimize_equipment_communication(
    request: EquipmentOptimizationRequest,
) -> AIProcessingResponse:
    """
    Optimize equipment communication messages for ISOBUS and safety protocols.

    Uses conservative optimization to ensure safety-critical equipment
    communication remains accurate and compliant with agricultural standards.
    Ideal for tractor commands, emergency protocols, and equipment status updates.
    """
    result = ai_processing_manager.optimize_equipment_communication(request.message)

    return AIProcessingResponse(
        final_output=result.final_output,
        total_tokens_saved=result.total_tokens_saved,
        stages_completed=result.stages_completed,
        agricultural_compliance_maintained=result.agricultural_compliance_maintained,
        optimization_level=OptimizationLevelEnum(result.optimization_level.value),
        optimization_applied=result.optimization_applied,
        estimated_tokens=result.estimated_tokens,
        budget_exceeded=result.budget_exceeded,
        fallback_used=result.fallback_used,
        metrics=result.metrics,
    )


@app.post(
    "/ai/monitoring/optimize",
    response_model=AIProcessingResponse,
    response_model_exclude_none=True,
    tags=["ai-processing", "monitoring"],
    summary="Optimize monitoring data",
)
async def optimize_monitoring_data(request: MonitoringOptimizationRequest) -> AIProcessingResponse:
    """
    Optimize monitoring data processing for sensor readings and analysis.

    Uses standard optimization for soil quality, water monitoring, and environmental
    sensor data while preserving critical measurement values and agricultural context.
    """
    result = ai_processing_manager.optimize_monitoring_data(request.sensor_data)

    return AIProcessingResponse(
        final_output=result.final_output,
        total_tokens_saved=result.total_tokens_saved,
        stages_completed=result.stages_completed,
        agricultural_compliance_maintained=result.agricultural_compliance_maintained,
        optimization_level=OptimizationLevelEnum(result.optimization_level.value),
        optimization_applied=result.optimization_applied,
        estimated_tokens=result.estimated_tokens,
        budget_exceeded=result.budget_exceeded,
        fallback_used=result.fallback_used,
        metrics=result.metrics,
    )


@app.post(
    "/ai/fleet/optimize",
    response_model=AIProcessingResponse,
    response_model_exclude_none=True,
    tags=["ai-processing", "fleet"],
    summary="Optimize fleet coordination",
)
async def optimize_fleet_coordination(request: FleetOptimizationRequest) -> AIProcessingResponse:
    """
    Optimize fleet coordination messages and multi-tractor commands.

    Uses aggressive optimization for routine fleet coordination while preserving
    essential operational details. Ideal for coordinating multiple tractors,
    field assignments, and synchronized agricultural operations.
    """
    result = ai_processing_manager.optimize_fleet_coordination(request.coordination_message)

    return AIProcessingResponse(
        final_output=result.final_output,
        total_tokens_saved=result.total_tokens_saved,
        stages_completed=result.stages_completed,
        agricultural_compliance_maintained=result.agricultural_compliance_maintained,
        optimization_level=OptimizationLevelEnum(result.optimization_level.value),
        optimization_applied=result.optimization_applied,
        estimated_tokens=result.estimated_tokens,
        budget_exceeded=result.budget_exceeded,
        fallback_used=result.fallback_used,
        metrics=result.metrics,
    )


@app.get(
    "/ai/statistics",
    response_model=PlatformStatisticsResponse,
    response_model_exclude_none=True,
    tags=["ai-processing"],
    summary="Get AI processing statistics",
)
async def get_ai_processing_statistics() -> PlatformStatisticsResponse:
    """
    Get comprehensive AI processing pipeline statistics.

    Returns global processing metrics, per-service statistics, configuration
    details, and pipeline health indicators for monitoring platform performance
    and token optimization effectiveness.
    """
    stats = ai_processing_manager.get_platform_statistics()

    return PlatformStatisticsResponse(
        global_stats=stats["global_stats"],
        service_stats=stats["service_stats"],
        configuration=stats["configuration"],
        pipeline_health=stats["pipeline_health"],
    )


@app.get(
    "/ai/health",
    response_model=HealthCheckResponse,
    response_model_exclude_none=True,
    tags=["ai-processing"],
    summary="AI processing health check",
)
async def ai_processing_health_check() -> HealthCheckResponse:
    """
    Perform comprehensive AI processing pipeline health check.

    Tests pipeline functionality, validates service registrations, and verifies
    agricultural safety compliance mode. Essential for monitoring the health
    of AI optimization capabilities in production agricultural environments.
    """
    health_data = ai_processing_manager.health_check()

    return HealthCheckResponse(**health_data)


# ============================================================================
# CRDT Field Allocation Endpoints
# ============================================================================


@app.post(
    "/crdt/segments",
    tags=["crdt"],
    summary="Add a new field segment to the CRDT",
)
async def add_field_segment(segment: FieldSegment) -> dict[str, str]:
    field_allocation_crdt.add_segment(segment)
    return {"message": f"Field segment {segment.segment_id} added."}


@app.post(
    "/crdt/assign",
    tags=["crdt"],
    summary="Assign a field segment to a tractor",
)
async def assign_field_segment(segment_id: str, tractor_id: str) -> dict[str, str]:
    updated_segment = field_allocation_crdt.assign_segment(segment_id, tractor_id)
    if updated_segment:
        return {"message": f"Segment {segment_id} assigned to tractor {tractor_id}."}
    return {
        "message": f"Failed to assign segment {segment_id} to tractor {tractor_id}. It might be already assigned or not exist."
    }


@app.post(
    "/crdt/release",
    tags=["crdt"],
    summary="Release a field segment from a tractor",
)
async def release_field_segment(segment_id: str, tractor_id: str) -> dict[str, str]:
    updated_segment = field_allocation_crdt.release_segment(segment_id, tractor_id)
    if updated_segment:
        return {"message": f"Segment {segment_id} released from tractor {tractor_id}."}
    return {
        "message": f"Failed to release segment {segment_id} from tractor {tractor_id}. It might not be assigned to this tractor or not exist."
    }


@app.post(
    "/crdt/complete",
    tags=["crdt"],
    summary="Mark a field segment as completed by a tractor",
)
async def complete_field_segment(segment_id: str, tractor_id: str) -> dict[str, str]:
    updated_segment = field_allocation_crdt.complete_segment(segment_id, tractor_id)
    if updated_segment:
        return {"message": f"Segment {segment_id} marked as completed by tractor {tractor_id}."}
    return {
        "message": f"Failed to mark segment {segment_id} as completed by tractor {tractor_id}. It might not be assigned to this tractor or not exist."
    }


@app.get(
    "/crdt/segments/allocated/{tractor_id}",
    response_model=list[FieldSegment],
    tags=["crdt"],
    summary="Get segments allocated to a specific tractor",
)
async def get_allocated_segments(tractor_id: str) -> list[FieldSegment]:
    return field_allocation_crdt.get_allocated_segments(tractor_id)


@app.get(
    "/crdt/segments/unallocated",
    response_model=list[FieldSegment],
    tags=["crdt"],
    summary="Get unallocated field segments",
)
async def get_unallocated_segments() -> list[FieldSegment]:
    return field_allocation_crdt.get_unallocated_segments()


@app.get(
    "/crdt/segments/completed",
    response_model=list[FieldSegment],
    tags=["crdt"],
    summary="Get completed field segments",
)
async def get_completed_segments() -> list[FieldSegment]:
    return field_allocation_crdt.get_completed_segments()


@app.post(
    "/crdt/merge",
    tags=["crdt"],
    summary="Merge state from another CRDT replica",
)
async def merge_crdt_state(other_state: dict[str, FieldSegment]) -> dict[str, str]:
    # Create a temporary CRDT to load the other state for merging
    other_crdt = FieldAllocationCRDT()
    for _segment_id, segment_data in other_state.items():
        other_crdt.add_segment(segment_data)

    field_allocation_crdt.merge(other_crdt)
    return {"message": "CRDT state merged successfully."}
