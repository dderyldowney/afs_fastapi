# AFS-FastAPI Project Context

> **Navigation**: [📚 DOCS Index](../README.md) | [🏠 Project Root](../../) | [📋 Strategic Documents](../strategic/) | [⚙️ Implementation](../implementation/) | [🔧 Technical](../technical/)
>
> **Reading Order**: [Project Strategy](PROJECT_STRATEGY.md) → [State of Affairs](STATE_OF_AFFAIRS.md) → [Where We Are](WHERE_WE_ARE.md) → **Current Document** → [Next Steps](NEXT_STEPS.md)

---

This file contains project analysis for Claude Code to reference across sessions.

## Repository Purpose

The Automated Farming System API (AFS-FastAPI) is a FastAPI-based system designed to automate essential farming processes through Machine Learning and robotics integration. It provides API interfaces for:

1. **Farm Equipment Control** - Operating tractors and other agricultural machinery
2. **Environmental Monitoring** - Tracking soil composition, pH, nutrients, and water quality
3. **Automation Support** - Serving both AI agents and human operators

## Key Components

- **Core API** (`afs_fastapi/api/main.py:43`): FastAPI app with equipment and monitoring endpoints
- **Equipment Module** (`afs_fastapi/equipment/`): `FarmTractor` class with comprehensive tractor simulation including GPS navigation, implement controls, autonomous features
- **Monitoring Module** (`afs_fastapi/monitoring/`): Soil and water quality monitoring with pluggable sensor backends
- **Configuration** (`pyproject.toml`): Python 3.12 project with FastAPI, Pydantic v2, strict typing

## Project Structure

```text
afs_fastapi/
├── api/           # FastAPI application and routes
├── equipment/     # Farm equipment classes (tractors, etc.)
├── monitoring/    # Environmental monitoring (soil, water)
├── services/      # Business logic services
├── stations/      # Station management
├── config.py      # Configuration management
├── version.py     # Version information
└── __main__.py    # Application entry point
```

## Execution Methods

1. **Development**: `python -m afs_fastapi` (defaults to 127.0.0.1:8000)
2. **Console Script**: `afs-api` (after pip install)
3. **Environment Configuration**:
   - `AFS_API_HOST`, `AFS_API_PORT`, `AFS_API_RELOAD`, `AFS_API_LOG_LEVEL`, `AFS_CORS_ORIGINS`

## API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /version` - API version
- `GET /equipment/tractor/{tractor_id}` - Get tractor status
- `GET /monitoring/soil/{sensor_id}` - Get soil readings
- `GET /monitoring/water/{sensor_id}` - Get water quality data

## Version Management and Tagging Strategy

### Critical Implementation Requirement

This tagging strategy must be enforced in all future sessions

### Current Version State

- **Latest Release**: `v0.1.3` (main branch)
- **Development**: `develop` branch prepared for next development cycle
- **Branch Strategy**: Git Flow with `main` (stable) and `develop` (active development)

### Tagging Rules - MUST FOLLOW

#### 1. Release Tags (Production)

- **Format**: `v{major}.{minor}.{patch}` (e.g., `v0.1.1`)
- **Branch**: Only tag on `main` branch
- **When**: After merging `develop` → `main` for stable releases
- **Examples**: `v0.1.1`, `v0.1.2`, `v0.2.0`

#### 2. Alpha Tags (Development)

- **Format**: `v{major}.{minor}.{patch}a{n}` (e.g., `v0.1.2a0`)
- **Branch**: Only tag on `develop` branch
- **When**: After significant development milestones
- **Sequence**: `v0.1.2a0` → `v0.1.2a1` → `v0.1.2a2` → `v0.1.2`
- **First Alpha**: Created when starting work on next version

#### 3. Version Progression Rules

```text
Current: v0.1.1 (stable on main)
Next:    v0.1.2a0 → v0.1.2a1 → ... → v0.1.2 (patch)
Or:      v0.2.0a0 → v0.2.0a1 → ... → v0.2.0 (minor)
Or:      v1.0.0a0 → v1.0.0a1 → ... → v1.0.0 (major)
```

#### 4. Branching Workflow - MANDATORY

```text
main branch (stable):
├── v0.1.0 → v0.1.1 → v0.1.2 (release tags only)

develop branch (development):
├── v0.1.2a0 → v0.1.2a1 → v0.1.2a2 (alpha tags)
└── merge to main → v0.1.2 release tag
```

#### 5. Version File Synchronization

When creating tags, ensure these files match:

- `afs_fastapi/version.py` - Contains `__version__`
- `pyproject.toml` - Contains `version`
- Both must match tag version (without 'v' prefix)

#### 6. Tag Creation Commands

```bash
# For alpha releases (on develop branch):
git checkout develop
git tag -a v0.1.2a1 -m "Alpha release v0.1.2a1 - [description]"
git push origin v0.1.2a1

# For stable releases (on main branch):
git checkout main
git tag -a v0.1.2 -m "Release v0.1.2 - [changes]"
git push origin v0.1.2
```

#### 7. Enforcement Rules

- **NEVER** tag the same commit with both release and alpha tags
- **NEVER** create release tags on develop branch
- **NEVER** create alpha tags on main branch
- **ALWAYS** verify version file consistency before tagging
- **ALWAYS** use annotated tags (`-a`) with descriptive messages

#### 8. Claude Code Monitoring Requirements

In every session, Claude Code must:

1. Check current tag status before creating new tags
2. Verify branch alignment with tagging rules
3. Ensure version files match intended tag version
4. Follow proper alpha sequence (no gaps: a0→a1→a2, not a0→a3)
5. Validate branch context before any tag operations

### Example Tag History (Correct)

```text
v0.1.1     (main branch - stable release)
v0.1.2a0   (develop branch - start development)
v0.1.2a1   (develop branch - development milestone)
v0.1.2     (main branch - next stable release)
v0.1.3a0   (develop branch - start next development)
```

## Architecture

### 3-Layer Enterprise Architecture

```text
┌─────────────────────────────────────────────────────┐
│                  API Layer                          │
│  FastAPI endpoints, Pydantic models, HTTP interface │
└─────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│              Coordination Layer                     │
│  Multi-tractor synchronization, conflict resolution │
│  Vector clocks, distributed state management        │
└─────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│               Equipment Layer                       │
│  Individual tractor control, ISOBUS compliance     │
│  Safety systems, sensor integration                │
└─────────────────────────────────────────────────────┘
```

## Development Tools

- **Testing**: pytest with asyncio support (see `WORKFLOW.md` for complete test architecture)
- **Type Checking**: mypy (strict mode) and pyright
- **Code Formatting**: black and ruff
- **Dependencies**: FastAPI, Pydantic v2, Uvicorn
- **Python Version**: 3.12 (strict requirement)

## Testing Documentation

**Complete Reference**: `WORKFLOW.md` - Comprehensive test suite workflow analysis covering:

- **Test Architecture**: 191 tests (100% passing in ~3-6 seconds) across 3 layers (Feature, Unit, Root-level)
- **Agricultural Domain Coverage**: Equipment, Monitoring, API, Infrastructure testing
- **Professional Standards**: ISOBUS (ISO 11783) and Safety (ISO 18497) compliance
- **Flow Patterns**: End-to-end workflow explanations and execution commands
- **Quality Metrics**: Performance characteristics and domain expertise validation

This document serves as the authoritative guide to understanding the sophisticated testing strategy employed in the AFS FastAPI agricultural robotics platform.

## Key Features

### FarmTractor Class

- Engine and gear controls
- GPS navigation with waypoints
- Implement position management
- Autonomous operation modes
- Hydraulic system controls
- Field operation tracking
- Emergency stop functionality
- Comprehensive diagnostics

### Monitoring System

- Pluggable sensor backends
- Soil composition tracking (pH, moisture, nutrients)
- Water quality monitoring (pH, turbidity, dissolved oxygen)
- Real-time data collection support

## Use Cases

The system is designed as a foundation for ML-driven precision agriculture, supporting:

- Autonomous tractor operations
- Real-time soil and water quality management
- Integration with AI agents for farm automation
- Human oversight of automated systems
- Data collection for machine learning models

---

*Last updated: October 06, 2025*
*Generated by Gemini CLI*
