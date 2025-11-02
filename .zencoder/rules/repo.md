---
description: Repository Information Overview
alwaysApply: true
---

# Automated Farming System API Information

## Summary
AFS FastAPI is a production-ready agricultural robotics platform for multi-tractor coordination with comprehensive reliability, database persistence, and educational value. It provides equipment control APIs, monitoring interfaces, and AI processing capabilities for agricultural operations, with a focus on safety-critical systems and industry standards compliance.

## Structure
- **afs_fastapi/**: Main package containing API implementation and domain logic
  - **api/**: FastAPI endpoints and application setup
  - **equipment/**: Farm equipment models and interfaces (tractors, implements)
  - **monitoring/**: Sensor monitoring systems (soil, water, edge devices)
  - **services/**: Business logic services (fleet coordination, AI processing)
  - **safety/**: Safety compliance systems (ISO standards)
  - **protocols/**: Agricultural communication protocols (ISOBUS, SAE J1939)
  - **database/**: Data persistence and time series storage
  - **todos/**: Task management system with 12-layer framework
- **tests/**: Comprehensive test suite with unit, integration, and feature tests
- **bin/**: Utility scripts for development and session management
- **docs/**: Documentation and specifications

## Language & Runtime
**Language**: Python
**Version**: 3.12 (strict requirement, no other versions supported)
**Build System**: Hatchling
**Package Manager**: pip

## Dependencies
**Main Dependencies**:
- fastapi>=0.111: Web framework for API endpoints
- uvicorn[standard]>=0.30: ASGI server
- pydantic>=2.7: Data validation and serialization
- python-can: CAN bus communication for agricultural equipment
- SQLAlchemy>=2.0: ORM for database operations
- alembic>=1.13: Database migrations
- httpx: HTTP client for CRDT communication
- tenacity: Retry mechanism for reliable messaging

**Development Dependencies**:
- pytest>=8.0: Testing framework
- pytest-asyncio>=0.23: Async testing support
- pyright>=1.10: Static type checking (mandatory)
- ruff>=0.5: Linting (zero warnings expected)
- black>=24.0: Code formatting (enforced)
- isort: Import sorting

## Build & Installation
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Type checking and linting
pyright afs_fastapi/ tests/
black --check afs_fastapi/ tests/
ruff check afs_fastapi/ tests/
```

## Main Files & Entry Points
**API Entry Point**: `afs_fastapi/__main__.py` - CLI entry that reads env vars and starts the server
**API Definition**: `afs_fastapi/api/main.py` - API handlers and app setup
**Domain Models**: 
- `afs_fastapi/equipment/farm_tractors.py` - Core FarmTractor model with 40+ attributes
- `afs_fastapi/monitoring/` - Monitoring interfaces and schemas

## Configuration
**Environment Variables**:
- AFS_API_HOST: API host (default: 127.0.0.1)
- AFS_API_PORT: API port (default: 8000)
- AFS_API_RELOAD: Enable hot reload (default: false)
- AFS_API_LOG_LEVEL: Logging level (default: info)
- AFS_CORS_ORIGINS: Optional CORS origins (comma-separated)

## Testing
**Framework**: pytest with pytest-asyncio
**Test Location**: tests/ directory with structured subdirectories
**Naming Convention**: test_*.py files with descriptive function names
**Configuration**: pytest.ini with custom markers and options
**Run Command**:
```bash
pytest tests/
```

## Development Workflow
**Test-First Development**: Mandatory Red-Green-Refactor workflow with zero exceptions
- RED: Create failing tests first
- GREEN: Implement minimal code to pass tests
- REFACTOR: Improve code while maintaining test coverage
- All code must have tests before implementation

**Session Management**:
- Start sessions: `./bin/loadsession`
- End sessions: `./bin/savesession`
- Status check: `./bin/whereweare`

**Task Management**:
- All tasks managed through TodoWrite.md system
- 12-layer hierarchy from Goal to Command
- Single concern principle enforced

**Type Safety**:
- Mandatory type hints for all code
- Static type checking with pyright
- Zero type-related warnings allowed

## Project Features
**Agricultural Robotics**: Multi-tractor coordination with field operations
**Safety Compliance**: ISO 18497 safety standards implementation
**ISOBUS Integration**: ISO 11783 communication protocol support
**Edge Computing**: Local processing for agricultural gateways
**AI Processing**: Token optimization for agricultural communications
**Database Integration**: PostgreSQL with Alembic migrations
**Task Management**: TodoWrite system with 12-layer framework