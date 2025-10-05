# AI Processing Quick Reference

## Fast Track Guide to AFS FastAPI AI Processing Integration

### 1. Immediate Usage

#### CLI Commands
```bash
# Quick status check
./bin/ai-processing status

# Test optimization
./bin/ai-processing test "Your message here"

# Service-specific optimization
./bin/ai-processing equipment "ISOBUS message"
./bin/ai-processing monitoring "Sensor data"
./bin/ai-processing fleet "Coordination message"
```

#### API Calls
```bash
# General processing
curl -X POST "/ai/process" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Optimize tractor communication", "service_name": "equipment"}'

# Equipment optimization
curl -X POST "/ai/equipment/optimize" \
  -H "Content-Type: application/json" \
  -d '{"message": "Emergency stop for TRC001", "priority": "critical"}'
```

### 2. Service Integration

#### Python Integration
```python
from afs_fastapi.services import agricultural_ai

# Optimize tractor message
result = agricultural_ai.optimize_tractor_communication(
    tractor_id="TRC001",
    message="Your tractor message",
    is_safety_critical=False  # Use True for emergency/safety
)

# Optimize sensor data
result = agricultural_ai.optimize_sensor_data_processing(
    sensor_id="SOIL001",
    sensor_type="soil_quality",
    reading_data="Your sensor readings"
)

# Optimize fleet coordination
result = agricultural_ai.optimize_fleet_coordination(
    coordinator_id="FLEET01",
    tractors=["TRC001", "TRC002"],
    operation_type="cultivation",
    coordination_message="Your coordination message"
)
```

### 3. Configuration Quick Setup

#### Default Configuration Location
- File: `.claude/ai_processing_config.json`
- Auto-created with sensible agricultural defaults
- Modify optimization levels per service as needed

#### Key Settings
```json
{
  "agricultural_safety_mode": true,
  "default_optimization_level": "standard",
  "services": {
    "equipment": {"optimization_level": "conservative"},
    "monitoring": {"optimization_level": "standard"},
    "fleet": {"optimization_level": "aggressive"}
  }
}
```

### 4. Optimization Levels Summary

| Level | Use Case | Token Reduction | Safety |
|-------|----------|----------------|---------|
| **Conservative** | Equipment, Emergency | ~15% | Maximum preservation |
| **Standard** | Monitoring, General | ~30% | Agricultural keywords preserved |
| **Aggressive** | Fleet, Routine | ~50% | Essential keywords preserved |
| **Adaptive** | Mixed content | Variable | Auto-detection |

### 5. Safety Compliance Features

- **ISO 11783 Compliance**: ISOBUS protocol preservation
- **ISO 18497 Compliance**: Agricultural safety standards
- **Protected Keywords**: Emergency, safety, ISO, agricultural terms
- **Safety-Critical Detection**: Automatic conservative optimization
- **Compliance Monitoring**: Real-time tracking and reporting

### 6. Common Use Cases

#### Equipment Communication
```python
# Status updates
optimize_tractor_communication(tractor_id, "status update", is_safety_critical=False)

# Emergency messages
optimize_tractor_communication(tractor_id, "emergency stop", is_safety_critical=True)

# ISOBUS messages
optimize_isobus_message(pgn, source_addr, payload, is_emergency=False)
```

#### Monitoring Systems
```python
# Soil sensors
optimize_sensor_data_processing("SOIL001", "soil_quality", "readings...")

# Water quality
optimize_sensor_data_processing("WATER001", "water_quality", "analysis...")

# Weather data
optimize_sensor_data_processing("WEATHER001", "environmental", "conditions...")
```

#### Fleet Coordination
```python
# Multi-tractor operations
optimize_fleet_coordination("FLEET01", ["TRC001", "TRC002"], "planting", "message...")

# Field assignments
optimize_fleet_coordination("FLEET01", tractors, "cultivation", message, field_assignments)
```

### 7. Health Monitoring

#### Quick Health Check
```bash
./bin/ai-processing health
```

#### Statistics Overview
```bash
./bin/ai-processing status
```

#### API Health Check
```python
response = requests.get("/ai/health")
health = response.json()
print(f"Status: {health['status']}")
```

### 8. Integration Testing

#### Test AI Processing
```bash
# Basic functionality test
PYTHONPATH=. pytest tests/integration/test_ai_processing_platform_integration.py -v

# Specific service test
PYTHONPATH=. pytest tests/integration/test_ai_processing_platform_integration.py::TestAIProcessingPlatformIntegration::test_tractor_status_communication_optimization -v
```

### 9. Response Format

All AI processing operations return:
```json
{
  "original_message": "Input text",
  "optimized_message": "Processed output",
  "tokens_saved": 42,
  "agricultural_compliance": true,
  "safety_preserved": true,
  "optimization_level": "standard",
  "processing_time_ms": 25.3
}
```

### 10. Troubleshooting

#### Common Issues
- **Low token savings**: Check message complexity and optimization level
- **Safety warnings**: Use conservative optimization for critical messages
- **Performance issues**: Monitor processing time and adjust token budget

#### Debug Commands
```bash
# Check configuration
./bin/ai-processing config list

# Test with verbose output
./bin/ai-processing test "message" --verbose

# Reset configuration
./bin/ai-processing reset
```

### 11. Best Practices Summary

1. **Use appropriate optimization levels** for different message types
2. **Include agricultural context** in messages (equipment IDs, field references)
3. **Mark safety-critical messages** explicitly
4. **Monitor compliance rates** and optimization effectiveness
5. **Test integration** thoroughly before production deployment

### 12. Quick Reference Links

- **Full Documentation**: `docs/AI_PROCESSING_INTEGRATION.md`
- **Integration Examples**: `examples/ai_integration_example.py`
- **Test Cases**: `tests/integration/test_ai_processing_platform_integration.py`
- **Configuration**: `.claude/ai_processing_config.json`
- **CLI Commands**: `./bin/ai-processing --help`

---

**Ready to use!** The AI Processing Pipeline is fully integrated and operational across the AFS FastAPI agricultural robotics platform.