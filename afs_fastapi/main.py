"""
FastAPI application module for AFS Agricultural Automation Platform.

- Provides `app` for ASGI servers (uvicorn, hypercorn, fastapi CLI).
- Keep *only* FastAPI app construction and include_routers here.
"""

from fastapi import FastAPI

from afs_fastapi.api.endpoints import equipment, fleet, safety

app = FastAPI(
    title="AFS FastAPI Agricultural Automation Platform",
    version="0.1.6",
    description="""
    **AFS FastAPI** - Comprehensive agricultural automation platform for autonomous equipment coordination.

    ## Features

    * **Equipment Management**: Control and monitor agricultural machinery (tractors, implements, sensors)
    * **Fleet Coordination**: Multi-tractor field operation coordination with safety compliance
    * **Safety Systems**: ISO 25119 compliant emergency stop and safety monitoring
    * **ISOBUS Communication**: ISO 11783 protocol implementation for equipment communication
    * **Real-time Monitoring**: Live telemetry, GPS tracking, and operational status

    ## Standards Compliance

    * **ISO 11783** (ISOBUS): Agricultural equipment communication protocol
    * **ISO 18497**: Safety requirements for autonomous agricultural machinery
    * **ISO 25119**: Functional safety lifecycle for agricultural systems
    * **SAE J1939**: CAN bus communication protocol for heavy-duty vehicles
    """,
    contact={
        "name": "AFS FastAPI Development Team",
        "url": "https://github.com/dderyldowney/afs_fastapi",
    },
    license_info={
        "name": "MIT",
    },
)

# Include API routers
app.include_router(equipment.router, prefix="/api/v1")
app.include_router(fleet.router, prefix="/api/v1")
app.include_router(safety.router, prefix="/api/v1")


@app.get("/health", tags=["System Operations"])
def health() -> dict[str, str]:
    """Liveness probe endpoint for system health monitoring."""
    return {"status": "ok", "service": "AFS FastAPI Agricultural Platform"}
