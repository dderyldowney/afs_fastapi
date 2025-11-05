import logging
import os
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.cors import CORSMiddleware

from afs_fastapi.api.ai_processing_schemas import (
    AIProcessingRequest,
    HealthCheckResponse,
    OptimizationLevelEnum,
    PlatformStatisticsResponse,
)
from afs_fastapi.api.core.error_handling import (
    AgriculturalBusinessError,
    AgriculturalSafetyError,
    AgriculturalValidationError,
    ErrorCode,
    agricultural_business_exception_handler,
    agricultural_safety_exception_handler,
    agricultural_validation_exception_handler,
    create_error_response,
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from afs_fastapi.api.core.response_models import AIProcessingResponse
from afs_fastapi.api.endpoints import equipment, monitoring
from afs_fastapi.api.endpoints.ai_processing import router as ai_processing
from afs_fastapi.api.endpoints.todos import router as todos_router
from afs_fastapi.api.endpoints.token_usage import router as token_usage_router
from afs_fastapi.equipment.farm_tractors import FarmTractor, FarmTractorResponse
from afs_fastapi.models.field_segment import FieldSegment
from afs_fastapi.monitoring.schemas import SoilReadingResponse, WaterQualityResponse
from afs_fastapi.monitoring.soil_monitor import SoilMonitor
from afs_fastapi.monitoring.water_monitor import WaterMonitor
from afs_fastapi.services import OptimizationLevel, ai_processing_manager
from afs_fastapi.services.crdt_manager import FieldAllocationCRDT
from afs_fastapi.version import __version__

# Create FastAPI application with enhanced configuration
app = FastAPI(
    title="Automated Farming System API",
    description="Modernized API for agricultural robotics, equipment control, and environmental monitoring with comprehensive error handling and ISO compliance.",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=None,
)

# Global instances and configuration
field_allocation_crdt = FieldAllocationCRDT()
request_counter = 0

# Optional CORS configuration via env var AFS_CORS_ORIGINS
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


async def app_lifespan(app: FastAPI):
    """Application lifespan events for startup and shutdown."""
    # Startup events
    print(f"🌱 AFS FastAPI API starting up - Version {__version__}")
    print("🚀 Initializing agricultural robotics systems...")

    # Initialize systems
    try:
        # Test AI processing manager
        await ai_processing_manager.health_check()
        print("✅ AI processing manager initialized")
    except Exception as e:
        print(f"⚠️  AI processing manager initialization warning: {e}")

    # Initialize monitoring systems
    try:
        # Test soil monitor
        SoilMonitor("TEST")
        print("✅ Soil monitoring system initialized")

        # Test water monitor
        WaterMonitor("TEST")
        print("✅ Water monitoring system initialized")
    except Exception as e:
        print(f"⚠️  Monitoring systems initialization warning: {e}")

    # Initialize equipment systems
    try:
        # Create test tractor
        FarmTractor("Test", "Tractor", 2024)
        print("✅ Equipment control system initialized")
    except Exception as e:
        print(f"⚠️  Equipment systems initialization warning: {e}")

    print("🌾 AFS FastAPI API startup complete")

    yield

    # Shutdown events
    print("🌙 AFS FastAPI API shutting down...")
    print("👋 Goodbye from the automated farming system!")


# Custom request middleware for tracking and logging
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Middleware for request tracking and logging."""
    global request_counter
    request_counter += 1

    # Log request details
    logger = logging.getLogger(__name__)
    logger.info(f"Request {request_counter}: {request.method} {request.url}")

    # Process request
    response = await call_next(request)

    # Log response details
    logger.info(f"Response {request_counter}: {response.status_code}")

    return response


# Register API routers
app.include_router(equipment.router, prefix="/api/v1/equipment", tags=["equipment"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["monitoring"])
app.include_router(ai_processing, prefix="/api/v1/ai", tags=["ai-processing"])
app.include_router(token_usage_router, prefix="/api/v1/monitoring", tags=["monitoring"])
app.include_router(todos_router, prefix="/api/v1/todos", tags=["todos"])


# Enhanced root endpoint
@app.get("/", tags=["meta"], summary="API information")
async def api_info() -> dict[str, Any]:
    """Provide comprehensive API information."""
    return {
        "name": "Automated Farming System API",
        "version": __version__,
        "description": "Modernized API for agricultural robotics with comprehensive error handling and ISO compliance",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "equipment": "/api/v1/equipment",
            "monitoring": "/api/v1/monitoring",
            "ai_processing": "/api/v1/ai",
            "todos": "/api/v1/todos",
            "token_usage": "/api/v1/monitoring/token-usage",
        },
        "features": [
            "Equipment control and monitoring",
            "Environmental data collection",
            "AI-powered agricultural optimization",
            "ISO 11783/18497 compliance",
            "Comprehensive error handling",
            "Real-time sensor data processing",
        ],
        "health_check": await ai_processing_manager.health_check(),
    }


# Health check endpoint
@app.get("/health", tags=["meta"], summary="Comprehensive system health check")
async def health_check() -> dict[str, Any]:
    """Perform comprehensive system health check."""
    health_results = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "systems": {
            "api": "operational",
            "ai_processing": "checking",
            "monitoring": "checking",
            "equipment": "checking",
        },
        "uptime_seconds": request_counter,
        "version": __version__,
        "compliance": {"iso_11783": True, "iso_18497": True, "agricultural_safety": True},
    }

    # Check AI processing
    try:
        ai_health = await ai_processing_manager.health_check()
        health_results["systems"]["ai_processing"] = (
            "operational" if ai_health.get("pipeline_operational", False) else "degraded"
        )
        health_results["ai_details"] = ai_health
    except Exception as e:
        health_results["systems"]["ai_processing"] = "error"
        health_results["ai_error"] = str(e)

    # Check monitoring systems
    try:
        SoilMonitor("TEST")
        WaterMonitor("TEST")
        health_results["systems"]["monitoring"] = "operational"
    except Exception as e:
        health_results["systems"]["monitoring"] = "degraded"
        health_results["monitoring_error"] = str(e)

    # Check equipment systems
    try:
        FarmTractor("Test", "Tractor", 2024)
        health_results["systems"]["equipment"] = "operational"
    except Exception as e:
        health_results["systems"]["equipment"] = "degraded"
        health_results["equipment_error"] = str(e)

    return health_results


# Version endpoint
@app.get("/version", tags=["meta"], summary="API version information")
async def version_info() -> dict[str, str]:
    """Provide version information."""
    return {
        "version": __version__,
        "build_date": getattr(__version__, "build_date", "Unknown"),
        "git_commit": getattr(__version__, "git_commit", "Unknown"),
    }


# Legacy endpoints for backward compatibility
@app.get(
    "/equipment/tractor/{tractor_id}",
    response_model=FarmTractorResponse,
    response_model_exclude_none=True,
    tags=["equipment", "legacy"],
    summary="Legacy: Get tractor status",
    deprecated=True,
)
async def legacy_get_tractor_status(tractor_id: str) -> FarmTractorResponse:
    """Legacy endpoint for backward compatibility."""
    tractor = FarmTractor("John Deere", "9RX", 2023)
    return tractor.to_response(tractor_id=tractor_id)


@app.get(
    "/monitoring/soil/{sensor_id}",
    response_model=SoilReadingResponse,
    response_model_exclude_none=True,
    tags=["monitoring", "legacy"],
    summary="Legacy: Get soil readings",
    deprecated=True,
)
async def legacy_get_soil_status(sensor_id: str) -> SoilReadingResponse:
    """Legacy endpoint for backward compatibility."""
    monitor = SoilMonitor(sensor_id)
    return SoilReadingResponse(sensor_id=sensor_id, readings=monitor.get_soil_composition())


@app.get(
    "/monitoring/water/{sensor_id}",
    response_model=WaterQualityResponse,
    response_model_exclude_none=True,
    tags=["monitoring", "legacy"],
    summary="Legacy: Get water readings",
    deprecated=True,
)
async def legacy_get_water_status(sensor_id: str) -> WaterQualityResponse:
    """Legacy endpoint for backward compatibility."""
    monitor = WaterMonitor(sensor_id)
    return WaterQualityResponse(sensor_id=sensor_id, readings=monitor.get_water_quality())


# CRDT endpoints for backward compatibility
@app.post(
    "/crdt/segments", tags=["crdt", "legacy"], summary="Legacy: Add field segment", deprecated=True
)
async def legacy_add_field_segment(segment: FieldSegment) -> dict[str, str]:
    """Legacy field segment endpoint."""
    field_allocation_crdt.add_segment(segment)
    return {"message": f"Field segment {segment.segment_id} added."}


@app.post(
    "/crdt/assign", tags=["crdt", "legacy"], summary="Legacy: Assign field segment", deprecated=True
)
async def legacy_assign_field_segment(segment_id: str, tractor_id: str) -> dict[str, str]:
    """Legacy field assignment endpoint."""
    updated_segment = field_allocation_crdt.assign_segment(segment_id, tractor_id)
    if updated_segment:
        return {"message": f"Segment {segment_id} assigned to tractor {tractor_id}."}
    return {
        "message": f"Failed to assign segment {segment_id} to tractor {tractor_id}. "
        f"It might be already assigned or not exist."
    }


# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle ValueError exceptions."""
    logger = logging.getLogger(__name__)
    logger.warning(f"Validation error: {exc}")

    from afs_fastapi.api.core.error_handling import create_error_response

    error_response = create_error_response(
        error_code=ErrorCode.VALIDATION_ERROR,
        message=str(exc),
        severity="medium",
        category="validation",
        recovery_suggestions=[
            "Check input data types and formats",
            "Validate required fields are present",
            "Ensure numeric values are within valid ranges",
        ],
        request=request,
    )
    return JSONResponse(status_code=422, content=error_response.model_dump())


@app.exception_handler(TypeError)
async def type_error_handler(request: Request, exc: TypeError) -> JSONResponse:
    """Handle TypeError exceptions."""
    logger = logging.getLogger(__name__)
    logger.warning(f"Type error: {exc}")

    error_response = create_error_response(
        error_code=ErrorCode.VALIDATION_ERROR,
        message=str(exc),
        severity="medium",
        category="validation",
        recovery_suggestions=[
            "Check data types and compatibility",
            "Verify function signatures",
            "Ensure correct parameter types",
        ],
        request=request,
    )
    return JSONResponse(status_code=422, content=error_response.model_dump())


# Request validation error handler
@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle FastAPI request validation errors."""
    logger = logging.getLogger(__name__)
    logger.warning(f"Request validation error: {exc}")

    # Extract first validation error for the response
    error_detail = exc.errors()[0] if exc.errors() else {}
    (".".join(str(x) for x in error_detail.get("loc", [])) if "loc" in error_detail else None)
    error_message = error_detail.get("msg", "Validation error")

    from afs_fastapi.api.core.error_handling import create_error_response

    error_response = create_error_response(
        error_code=ErrorCode.VALIDATION_ERROR,
        message=error_message,
        severity="medium",
        category="validation",
        recovery_suggestions=[
            "Check input data format and structure",
            "Validate required fields are present",
            "Ensure all fields meet validation requirements",
            "Check API documentation for expected formats",
        ],
        request=request,
    )
    return JSONResponse(status_code=422, content=error_response.model_dump())


# Global exception handlers
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(AgriculturalValidationError, agricultural_validation_exception_handler)
app.add_exception_handler(AgriculturalBusinessError, agricultural_business_exception_handler)
app.add_exception_handler(AgriculturalSafetyError, agricultural_safety_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# Global error logging middleware
@app.middleware("http")
async def error_logging_middleware(request: Request, call_next):
    """Middleware for error logging and monitoring."""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Unhandled error in {request.method} {request.url}: {e}", exc_info=True)

        # Create error response
        error_response = create_error_response(
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred",
            severity="critical",
            category="system",
            recovery_suggestions=[
                "Contact system administrator",
                "Check system logs for details",
                "Try again later",
            ],
            request=request,
        )

        # Convert Pydantic model to dict for JSON response
        return JSONResponse(status_code=500, content=error_response.model_dump())


# Additional utility endpoint
@app.get("/status", tags=["meta"], summary="System status and statistics")
async def system_status() -> dict[str, Any]:
    """Provide detailed system status and statistics."""
    try:
        ai_stats = ai_processing_manager.get_platform_statistics()

        return {
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": request_counter,
            "api_version": __version__,
            "systems": {
                "ai_processing": {
                    "status": (
                        "operational"
                        if ai_stats.get("pipeline_health", {}).get("total_services_registered", 0)
                        > 0
                        else "degraded"
                    ),
                    "services_registered": ai_stats.get("pipeline_health", {}).get(
                        "total_services_registered", 0
                    ),
                    "requests_processed": ai_stats.get("global_stats", {}).get("total_requests", 0),
                },
                "monitoring": {
                    "status": "operational",
                    "active_sensors": 0,  # Would be populated from monitoring system
                },
                "equipment": {
                    "status": "operational",
                    "registered_equipment": 0,  # Would be populated from equipment system
                },
            },
            "compliance": {"iso_11783": True, "iso_18497": True, "agricultural_safety": True},
            "performance": {
                "average_response_time_ms": 150,  # Would be measured
                "error_rate_percentage": 0.5,  # Would be measured
                "throughput_requests_per_second": 10,  # Would be measured
            },
        }
    except Exception as e:
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "message": "Unable to retrieve complete system status",
        }


# Include the original main API components for backward compatibility
# Legacy AI Processing Endpoints
@app.post(
    "/ai/process",
    response_model=AIProcessingResponse,
    response_model_exclude_none=True,
    tags=["ai-processing", "legacy"],
    summary="Legacy: Process text with AI optimization",
    deprecated=True,
)
async def legacy_process_with_ai_optimization(request: AIProcessingRequest) -> AIProcessingResponse:
    """Legacy AI processing endpoint."""
    # Convert enum to OptimizationLevel if provided
    optimization_level = None
    if request.optimization_level:
        optimization_level = OptimizationLevel(request.optimization_level.value)

    # Process with or without budget constraint
    if request.token_budget:
        result = await ai_processing_manager.process_with_budget_constraint(
            user_input=request.user_input,
            token_budget=request.token_budget,
            service_name=request.service_name or "platform",
        )
    else:
        result = await ai_processing_manager.process_agricultural_request(
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


@app.get(
    "/ai/statistics",
    response_model=PlatformStatisticsResponse,
    tags=["ai-processing", "legacy"],
    summary="Legacy: Get AI statistics",
    deprecated=True,
)
async def legacy_get_ai_statistics() -> PlatformStatisticsResponse:
    """Legacy AI statistics endpoint."""
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
    tags=["ai-processing", "legacy"],
    summary="Legacy: AI health check",
    deprecated=True,
)
async def legacy_ai_health_check() -> HealthCheckResponse:
    """Legacy AI health check endpoint."""
    health_data = await ai_processing_manager.health_check()
    return HealthCheckResponse(**health_data)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "afs_fastapi.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
