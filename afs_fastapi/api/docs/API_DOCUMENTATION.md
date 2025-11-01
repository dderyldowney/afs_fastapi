# AFS FastAPI API Documentation

## Overview

The AFS FastAPI API provides a comprehensive RESTful interface for agricultural robotics, equipment control, and environmental monitoring. The API has been modernized with enhanced error handling, input validation, and ISO 11783/18497 compliance.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, the API operates without authentication for development purposes. In production, implement API key authentication or OAuth2 as needed.

## Error Handling

The API uses standardized error responses with the following structure:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Detailed error description",
    "severity": "medium",
    "category": "validation",
    "equipment_id": "TRC-001",
    "field_id": "FIELD-001",
    "recovery_suggestions": [
      "Suggested action 1",
      "Suggested action 2"
    ]
  },
  "request_id": "uuid-generated-id",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Error Codes

| Code | Category | Description |
|------|----------|-------------|
| VALIDATION_ERROR | Validation | Input validation failed |
| INVALID_INPUT | Validation | Invalid input format |
| RESOURCE_NOT_FOUND | System | Resource not found |
| EQUIPMENT_NOT_AVAILABLE | Agricultural | Equipment not available |
| SAFETY_PROTOCOL_VIOLATION | Agricultural Safety | Safety protocol violated |
| ISOBUS_COMMUNICATION_ERROR | Agricultural | ISOBUS communication issue |
| INTERNAL_SERVER_ERROR | System | Internal server error |

## Endpoints

### Equipment Management

#### Get Equipment Status
```http
GET /equipment/status/{equipment_id}
```

**Description**: Get detailed status information for agricultural equipment.

**Parameters**:
- `equipment_id` (path): Equipment identifier (e.g., "TRC-001")
- `include_diagnostics` (query): Include diagnostic data (default: true)
- `include_location` (query): Include GPS location (default: true)
- `include_safety` (query): Include safety status (default: true)

**Response**:
```json
{
  "success": true,
  "data": {
    "equipment_id": "TRC-001",
    "equipment_type": "tractor",
    "status": "operational",
    "location": {
      "latitude": 40.7128,
      "longitude": -74.0060
    },
    "metrics": {
      "engine_rpm": 1800,
      "fuel_level": 75.5,
      "hydraulic_pressure": 2500.0,
      "ground_speed": 5.2
    },
    "isobus_compliance": true,
    "safety_level": "PLc"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Control Equipment
```http
POST /equipment/control
```

**Description**: Send control commands to agricultural equipment.

**Request Body**:
```json
{
  "equipment_id": "TRC-001",
  "operation": "start_engine",
  "parameters": {
    "priority": "normal"
  },
  "priority": "normal",
  "safety_override": false
}
```

#### List Equipment
```http
GET /equipment/list
```

**Description**: Get list of registered agricultural equipment.

**Parameters**:
- `equipment_type` (query): Filter by equipment type
- `status_filter` (query): Filter by status
- `page` (query): Page number (default: 1)
- `page_size` (query): Items per page (default: 10, max: 50)

### Environmental Monitoring

#### Submit Soil Reading
```http
POST /monitoring/soil/readings
```

**Description**: Submit soil quality measurements from field sensors.

**Request Body**:
```json
{
  "sensor_id": "SOI-001",
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060
  },
  "readings": {
    "moisture_percent": 34.2,
    "ph": 6.8,
    "temperature_celsius": 22.1,
    "nitrogen_ppm": 120,
    "phosphorus_ppm": 45,
    "potassium_ppm": 180
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Get Soil Readings
```http
GET /monitoring/soil/readings
```

**Description**: Retrieve soil sensor readings with filtering.

**Parameters**:
- `sensor_id` (query): Filter by sensor ID
- `field_id` (query): Filter by field ID
- `start_time` (query): Start time filter
- `end_time` (query): End time filter
- `data_quality` (query): Filter by data quality
- `page` (query): Page number
- `page_size` (query): Items per page

### AI Processing

#### Process with AI Optimization
```http
POST /ai/process
```

**Description**: Process agricultural text input with AI optimization.

**Request Body**:
```json
{
  "user_input": "Coordinate tractor fleet for field cultivation with safety protocols",
  "service_name": "platform",
  "optimization_level": "standard",
  "target_format": "standard",
  "token_budget": 2000,
  "context_data": {
    "equipment_id": "TRC-001",
    "field_id": "FIELD-001",
    "operation_type": "cultivation"
  },
  "safety_override": false
}
```

#### Optimize Equipment Communication
```http
POST /ai/equipment/optimize
```

**Description**: Optimize equipment communication messages for ISOBUS and safety protocols.

#### Optimize Fleet Coordination
```http
POST /ai/fleet/optimize
```

**Description**: Optimize fleet coordination messages and multi-tractor commands.

## Data Models

### Equipment Types
- `tractor`: Agricultural tractors
- `combine`: Combine harvesters
- `planter`: Planting equipment
- `sprayer`: Spraying equipment
- `cultivator`: Cultivation equipment
- `harvester`: Harvesting equipment

### Operation Types
- `planting`: Crop planting operations
- `cultivation`: Soil cultivation
- `fertilization`: Fertilizer application
- `irrigation`: Water application
- `pesticide_application`: Pest control
- `harvesting`: Crop harvesting
- `maintenance`: Equipment maintenance
- `transport`: Material transport
- `land_preparation`: Field preparation

### Safety Levels
- `PLc`: Performance Level c (basic safety)
- `PLd`: Performance Level d (enhanced safety)
- `PLe`: Performance Level e (high safety)

### Optimization Levels
- `conservative`: Minimal optimization with maximum safety
- `standard`: Balanced optimization with good safety
- `aggressive`: Significant optimization with reduced safety constraints
- `adaptive`: Dynamic optimization based on context

## ISO Compliance

The API adheres to agricultural industry standards:

### ISO 11783 (ISOBUS)
- Equipment communication protocols
- Standardized data formats
- Message structure and addressing

### ISO 18497 (Safety)
- Safety performance levels
- Risk assessment requirements
- Safety system validation

## Rate Limiting

The API implements rate limiting to ensure fair usage:
- 100 requests per minute per client
- 1000 requests per hour per client
- Burst limit of 20 requests per 10 seconds

## Response Pagination

List responses use standardized pagination:

```json
{
  "success": true,
  "data": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5,
  "has_next": true,
  "has_previous": false,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Examples

### Example 1: Get Tractor Status

```bash
curl -X GET "http://localhost:8000/api/v1/equipment/status/TRC-001" \
  -H "accept: application/json" | jq
```

### Example 2: Submit Soil Reading

```bash
curl -X POST "http://localhost:8000/api/v1/monitoring/soil/readings" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "SOI-001",
    "location": {
      "latitude": 40.7128,
      "longitude": -74.0060
    },
    "readings": {
      "moisture_percent": 34.2,
      "ph": 6.8,
      "temperature_celsius": 22.1
    }
  }' | jq
```

### Example 3: Process Text with AI

```bash
curl -X POST "http://localhost:8000/api/v1/ai/process" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Coordinate tractor fleet for field cultivation",
    "service_name": "platform",
    "optimization_level": "standard"
  }' | jq
```

## Troubleshooting

### Common Issues

1. **400 Bad Request**: Check input validation requirements
2. **404 Not Found**: Verify endpoint path and resource existence
3. **422 Unprocessable Entity**: Fix input data types and formats
4. **500 Internal Server Error**: Check server logs and system status

### Debug Mode

Enable debug logging:

```bash
export AFS_API_LOG_LEVEL=debug
python -m uvicorn afs_fastapi.api.main:app --reload
```

## Version History

### Version 2.0 (Current)
- Modernized API with comprehensive error handling
- Added input validation and response standardization
- Enhanced agricultural compliance features
- Improved error recovery and logging
- Added comprehensive API documentation

### Version 1.x (Legacy)
- Basic API functionality
- Simple error handling
- Limited validation
- Minimal documentation
