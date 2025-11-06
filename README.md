# AFS FastAPI - Agricultural Robotics Platform

**A comprehensive FastAPI-based platform for agricultural robotics, farm equipment coordination, and precision farming operations.**

## Overview

AFS FastAPI provides a production-ready framework for managing agricultural robotics systems, including farm tractor fleets, sensor monitoring, CAN bus communication, and equipment safety systems. The platform implements ISO 11783 standards for agricultural equipment communication and provides real-time coordination capabilities for precision farming operations.

## Key Features

- 🚜 **Farm Equipment Management** - Real agricultural equipment implementations
- 📡 **CAN Bus Communication** - ISO 11783 compliant agricultural equipment protocols
- 🗄️ **Database Integration** - Agricultural data schemas with async operations
- 🌐 **REST API** - FastAPI application with real business logic
- 📊 **Sensor Monitoring** - Soil, weather, and equipment telemetry systems
- 🛡️ **Safety Systems** - Cross-layer validation and safety monitoring
- 🤖 **Robotics Integration** - Multi-tractor coordination and fleet management

## Quick Start

### Prerequisites

- Python 3.12+
- SQLite (included) or PostgreSQL for production
- Agricultural equipment with CAN bus interface (optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/afs-fastapi.git
cd afs-fastapi

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m afs_fastapi.database.init_db

# Start the API server
uvicorn afs_fastapi.api.main:app --reload
```

### Basic Usage

```python
from afs_fastapi.equipment.farm_tractors import FarmTractor
from afs_fastapi.database.optimized_db_config import get_async_session

# Create and manage farm equipment
tractor = FarmTractor("John Deere", "8RX", 2023)
print(f"Equipment: {tractor.make} {tractor.model}")

# Database operations
async with get_async_session() as session:
    # Perform agricultural data operations
    pass
```

## Library Verification Status ✅

This library has been **triple-verified** to ensure clean, working implementations:

### Verification Results
- **✅ Code Analysis:** All components contain real business logic
- **✅ Test Coverage:** 690 tests verify actual functionality (84.0% real implementation usage)
- **✅ Integration Testing:** End-to-end functionality confirmed
- **✅ Database Operations:** Real CRUD operations with agricultural schemas
- **✅ API Endpoints:** All serve real data, not stubs
- **✅ Agricultural Domain:** Genuine farming equipment and robotics implementations

### Quality Metrics
- **Implementation Quality:** 84.0% of tests use real implementations
- **Test Suite:** 690 tests across 75 files
- **Async Coverage:** 188 async tests (27.2%)
- **Production Ready:** ✅ Verified for production use

**Verification Date:** November 6, 2025
**Verification Report:** See `docs/verification/library_verification_summary.md`

## Architecture

### Core Components

- **Equipment Layer** (`afs_fastapi/equipment/`)
  - Farm tractor implementations
  - CAN bus communication manager
  - Agricultural equipment coordination

- **Database Layer** (`afs_fastapi/database/`)
  - Agricultural data schemas
  - Async database operations
  - Equipment telemetry storage

- **API Layer** (`afs_fastapi/api/`)
  - FastAPI application and routes
  - Equipment status endpoints
  - Sensor data monitoring APIs

- **Services Layer** (`afs_fastapi/services/`)
  - Fleet coordination services
  - Synchronization primitives
  - Agricultural data processing

- **Safety Systems** (`afs_fastapi/safety/`)
  - Cross-layer validation
  - Safety monitoring
  - ISO 11783 compliance

### Database Schema

The platform uses agricultural-specific data models:
- Equipment telemetry and status
- Sensor data (soil, weather, crops)
- Fleet coordination data
- Safety and compliance records

## API Documentation

Once running, access the interactive API documentation:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=afs_fastapi

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/api/
```

### Test Quality
- **Total Tests:** 690
- **Real Implementation Testing:** 84.0%
- **Async Test Coverage:** 27.2%
- **Integration Testing:** Comprehensive end-to-end tests

## Agricultural Domain Focus

This platform is specifically designed for agricultural robotics applications:

### Supported Equipment
- Agricultural tractors and implements
- Soil moisture sensors
- Weather monitoring stations
- Crop yield monitoring systems
- Fleet management equipment

### Standards Compliance
- **ISO 11783:** Agricultural equipment communication
- **ISO 25119:** Safety systems for agricultural machinery
- **Agricultural robotics best practices**

## Development

### Code Quality Standards
- **Type Hints:** Full type annotation coverage
- **Code Formatting:** Black, isort, Ruff
- **Testing:** Test-driven development (TDD) required
- **Documentation:** Comprehensive docstrings and API docs

### Contributing

1. Follow the test-driven development methodology
2. Ensure all tests pass before submitting
3. Use real implementations over mocks where possible
4. Maintain agricultural domain focus
5. Follow ISO 11783 standards for equipment communication

## Documentation

- **Complete Documentation:** `docs/README.md`
- **Strategic Planning:** `docs/strategic/`
- **Technical Architecture:** `docs/technical/`
- **Implementation Standards:** `docs/implementation/`
- **Verification Reports:** `docs/verification/`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For agricultural robotics implementation support:
- **Documentation:** See `docs/` directory
- **API Reference:** `http://localhost:8000/docs`
- **Issues:** GitHub Issues
- **Verification Status:** See `docs/verification/library_verification_summary.md`

---

**AFS FastAPI** - Production-ready agricultural robotics platform with verified implementations for precision farming operations.