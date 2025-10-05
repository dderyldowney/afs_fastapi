# AI Processing Integration Guide

## AFS FastAPI Platform AI Processing Pipeline

The AFS FastAPI agricultural robotics platform includes sophisticated AI processing capabilities designed to optimize communication efficiency while maintaining strict compliance with agricultural safety standards and ISO requirements.

## Overview

The AI Processing Pipeline provides intelligent token optimization across all platform services:

- **Equipment Communication**: Conservative optimization for safety-critical tractor and implement messaging
- **Monitoring Data**: Standard optimization for sensor readings and environmental data
- **Fleet Coordination**: Aggressive optimization for routine multi-tractor coordination
- **Safety Protocols**: Ultra-conservative optimization preserving all critical safety information

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│  AI Processing Endpoints  │  Agricultural Services          │
│  /ai/process              │  Equipment | Monitoring | Fleet │
│  /ai/equipment/optimize   │                                 │
│  /ai/monitoring/optimize  │                                 │
│  /ai/fleet/optimize       │                                 │
├─────────────────────────────────────────────────────────────┤
│              Agricultural AI Integration Layer               │
├─────────────────────────────────────────────────────────────┤
│                 AI Processing Manager                       │
├─────────────────────────────────────────────────────────────┤
│              AI Processing Pipeline (4-Stage)               │
│  Pre-fill → Prompt Processing → Generation → Decoding      │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. API Usage

#### General AI Processing
```python
import requests

# Process agricultural text with AI optimization
response = requests.post("/ai/process", json={
    "user_input": "Coordinate tractor fleet for field cultivation with safety protocols",
    "service_name": "fleet",
    "optimization_level": "standard"
})

result = response.json()
print(f"Optimized: {result['final_output']}")
print(f"Tokens Saved: {result['total_tokens_saved']}")
```

#### Equipment Communication
```python
# Optimize equipment communication messages
response = requests.post("/ai/equipment/optimize", json={
    "message": "ISOBUS emergency stop initiated for tractor TRC001",
    "equipment_id": "TRC001",
    "priority": "critical"
})
```

#### Monitoring Data
```python
# Optimize sensor data processing
response = requests.post("/ai/monitoring/optimize", json={
    "sensor_data": "Soil moisture 34.2%, pH 6.8, nitrogen 120ppm",
    "sensor_id": "SOIL_001",
    "data_type": "soil_quality"
})
```

#### Fleet Coordination
```python
# Optimize fleet coordination messages
response = requests.post("/ai/fleet/optimize", json={
    "coordination_message": "Coordinate three tractors for parallel cultivation",
    "fleet_operation": "cultivation",
    "tractor_count": 3
})
```

### 2. Service Integration

#### Direct Service Usage
```python
from afs_fastapi.services import agricultural_ai

# Optimize tractor communication
result = agricultural_ai.optimize_tractor_communication(
    tractor_id="JD_8RX_001",
    message="Tractor operational status update",
    is_safety_critical=False
)

# Optimize ISOBUS messages
result = agricultural_ai.optimize_isobus_message(
    pgn=0xFE48,
    source_address=0x80,
    data_payload="Status update data",
    is_emergency=False
)

# Optimize sensor data
result = agricultural_ai.optimize_sensor_data_processing(
    sensor_id="SOIL_001",
    sensor_type="soil_quality",
    reading_data="Comprehensive soil analysis results"
)
```

### 3. CLI Management

#### Status and Health Checks
```bash
# Check AI processing status
./bin/ai-processing status

# Perform health check
./bin/ai-processing health

# View configuration
./bin/ai-processing config list
```

#### Testing and Optimization
```bash
# Test AI processing with sample text
./bin/ai-processing test "Coordinate tractor fleet for cultivation"

# Optimize equipment messages
./bin/ai-processing equipment "ISOBUS emergency stop for TRC001"

# Optimize monitoring data
./bin/ai-processing monitoring "Soil moisture 34%, pH 6.8"

# Optimize fleet coordination
./bin/ai-processing fleet "Coordinate three tractors for parallel planting"
```

## Configuration

### Platform Configuration File
Location: `.claude/ai_processing_config.json`

```json
{
  "agricultural_safety_mode": true,
  "default_optimization_level": "standard",
  "token_budget": 4000,
  "services": {
    "equipment": {
      "optimization_level": "conservative",
      "priority": "high",
      "description": "Equipment communication (ISOBUS, safety protocols)"
    },
    "monitoring": {
      "optimization_level": "standard",
      "priority": "medium",
      "description": "Sensor data and monitoring systems"
    },
    "fleet": {
      "optimization_level": "aggressive",
      "priority": "medium",
      "description": "Multi-tractor fleet coordination"
    }
  },
  "safety_compliance": {
    "iso_11783_compliance": true,
    "iso_18497_compliance": true,
    "protected_keywords": [
      "emergency", "stop", "safety", "critical", "iso", "isobus",
      "tractor", "equipment", "agricultural", "coordination", "fleet"
    ]
  }
}
```

### Optimization Levels

#### Conservative (Equipment/Safety)
- **Target Reduction**: 15%
- **Safety Keywords**: All preserved
- **Format Optimization**: Disabled
- **Use Cases**: Emergency messages, safety protocols, ISOBUS communication

#### Standard (Monitoring/General)
- **Target Reduction**: 30%
- **Agricultural Keywords**: Preserved
- **Format Optimization**: Enabled
- **Use Cases**: Sensor data, status updates, general communication

#### Aggressive (Fleet/Coordination)
- **Target Reduction**: 50%
- **Essential Keywords**: Preserved
- **Format Optimization**: Enabled
- **Use Cases**: Routine coordination, batch operations, logging

#### Adaptive (Dynamic)
- **Target Reduction**: Variable (30% baseline)
- **Auto-Detection**: Safety-critical content
- **Dynamic Adjustment**: Based on content analysis
- **Use Cases**: Mixed content requiring intelligent optimization

## Safety and Compliance

### ISO Standards Compliance

The AI processing system maintains strict compliance with agricultural robotics standards:

- **ISO 11783**: ISOBUS communication protocol preservation
- **ISO 18497**: Agricultural machinery safety system compliance
- **Emergency Protocols**: Ultra-conservative processing for safety-critical messages
- **Keyword Protection**: Automatic preservation of safety and agricultural terminology

### Safety Features

- **Emergency Message Handling**: Highest priority processing with minimal optimization
- **Safety Keyword Protection**: Automatic detection and preservation of critical terms
- **Compliance Monitoring**: Real-time tracking of agricultural compliance rates
- **Fallback Systems**: Graceful degradation to original messages when optimization fails

## Integration Examples

### Equipment Integration Example
```python
from afs_fastapi.equipment.farm_tractors import FarmTractor
from afs_fastapi.services import agricultural_ai

# Create tractor instance
tractor = FarmTractor("John Deere", "8RX 410", 2023)
tractor.start_engine()

# Generate status message
status = f"Tractor {tractor.device_name} operational: RPM {tractor.engine_rpm}, Speed {tractor.speed} mph"

# Optimize with AI processing
optimized = agricultural_ai.optimize_tractor_communication(
    tractor_id=tractor.device_name,
    message=status,
    message_type="status"
)

print(f"Original: {optimized['original_message']}")
print(f"Optimized: {optimized['optimized_message']}")
print(f"Tokens Saved: {optimized['tokens_saved']}")
```

### Fleet Coordination Example
```python
from afs_fastapi.services import agricultural_ai

# Multi-tractor coordination
coordination_msg = """
Coordinate cultivation operation across field sectors A1-A5
with three tractors in parallel formation, maintaining 30-foot spacing,
synchronized at 8 mph with 6-inch implement depth, GPS waypoint
navigation active, collision avoidance enabled, complete coverage
with 2-foot overlap between passes.
"""

result = agricultural_ai.optimize_fleet_coordination(
    coordinator_id="FLEET_CONTROL_01",
    tractors=["JD_8RX_001", "JD_8RX_002", "JD_8RX_003"],
    operation_type="cultivation",
    coordination_message=coordination_msg,
    field_assignments={
        "JD_8RX_001": "Sector_A1-A2",
        "JD_8RX_002": "Sector_A3-A4",
        "JD_8RX_003": "Sector_A5"
    }
)

print(f"Optimized Coordination: {result['optimized_coordination']}")
print(f"Efficiency Gain: {result['coordination_efficiency']:.1%}")
```

## Monitoring and Statistics

### Platform Statistics
```bash
# Get comprehensive statistics
./bin/ai-processing status

# Health check
./bin/ai-processing health
```

### API Statistics Endpoint
```python
response = requests.get("/ai/statistics")
stats = response.json()

print(f"Total Requests: {stats['global_stats']['total_requests']}")
print(f"Tokens Saved: {stats['global_stats']['tokens_saved']}")
print(f"Agricultural Compliance Rate: {stats['pipeline_health']['agricultural_request_ratio']:.1%}")
```

### Integration Statistics
```python
from afs_fastapi.services import agricultural_ai

stats = agricultural_ai.get_integration_statistics()

# Integration metrics
metrics = stats["integration_metrics"]
print(f"Equipment Optimizations: {metrics['equipment_optimizations']}")
print(f"Safety Preservations: {metrics['safety_critical_preservations']}")

# Agricultural compliance
compliance = stats["agricultural_compliance"]
print(f"ISO Compliance Rate: {compliance['iso_compliance_rate']:.1%}")
```

## Best Practices

### 1. Service-Appropriate Optimization
- **Equipment Messages**: Use conservative optimization for safety-critical communication
- **Monitoring Data**: Use standard optimization for sensor readings and analysis
- **Fleet Coordination**: Use aggressive optimization for routine coordination messages
- **Safety Protocols**: Always use conservative optimization with keyword preservation

### 2. Agricultural Context Preservation
- Include equipment IDs, field references, and operation types in messages
- Preserve agricultural terminology and technical specifications
- Maintain ISO standard references and compliance indicators
- Include safety-critical information explicitly

### 3. Error Handling and Fallbacks
- Monitor optimization success rates and agricultural compliance
- Use fallback to original messages when optimization fails
- Implement retry mechanisms for critical communications
- Maintain audit logs for safety-critical message processing

### 4. Performance Optimization
- Use appropriate optimization levels based on message criticality
- Monitor token savings and processing efficiency
- Configure service priorities based on operational requirements
- Leverage caching for frequently processed message patterns

## Testing

### Unit Tests
```bash
# Test AI processing pipeline components
PYTHONPATH=. pytest tests/unit/services/test_ai_processing_pipeline.py -v
```

### Integration Tests
```bash
# Test platform integration
PYTHONPATH=. pytest tests/integration/test_ai_processing_platform_integration.py -v
```

### Manual Testing
```bash
# Test CLI functionality
./bin/ai-processing test "Sample agricultural message"

# Test different service optimizations
./bin/ai-processing equipment "ISOBUS message"
./bin/ai-processing monitoring "Sensor data"
./bin/ai-processing fleet "Coordination message"
```

## Troubleshooting

### Common Issues

1. **Low Optimization Rates**
   - Check if messages contain too many protected keywords
   - Verify optimization level configuration
   - Review service-specific settings

2. **Safety Compliance Warnings**
   - Ensure safety-critical messages use conservative optimization
   - Check protected keyword configuration
   - Verify ISO standard preservation settings

3. **Performance Issues**
   - Monitor processing time metrics
   - Check token budget configuration
   - Review service priority settings

### Debugging Commands
```bash
# Check configuration
./bin/ai-processing config list

# Verify service health
./bin/ai-processing health

# Test processing with debug output
./bin/ai-processing test "Debug message" --verbose
```

## API Reference

### Endpoints

- `POST /ai/process` - General AI processing
- `POST /ai/equipment/optimize` - Equipment communication optimization
- `POST /ai/monitoring/optimize` - Monitoring data optimization
- `POST /ai/fleet/optimize` - Fleet coordination optimization
- `GET /ai/statistics` - Platform statistics
- `GET /ai/health` - Health check

### Response Format
```json
{
  "final_output": "Optimized message text",
  "total_tokens_saved": 45,
  "agricultural_compliance_maintained": true,
  "optimization_level": "standard",
  "optimization_applied": true,
  "processing_time_ms": 23.4
}
```

## Support

For additional support:
- Review integration examples in `examples/ai_integration_example.py`
- Check test cases for usage patterns
- Use CLI commands for debugging and validation
- Monitor platform statistics for optimization effectiveness

The AI Processing Pipeline is designed to seamlessly integrate with existing agricultural robotics workflows while providing significant efficiency improvements through intelligent token optimization.