# Database Schema Reference
## Actual Table Names (Verified Through Execution Testing)

This document provides the **actual database table names** as verified through execution testing in a clean environment.

### ⚠️ IMPORTANT: Documentation vs Reality

**Common misconceptions vs actual implementation:**

| Model Class | ❌ Incorrect Table Name | ✅ **Actual Table Name** |
|-------------|------------------------|--------------------------|
| `ISOBUSMessageRecord` | `isobus_message_record` | `isobus_messages` |
| `AgriculturalSensorRecord` | `agricultural_sensor_record` | `agricultural_sensor_data` |
| `Field` | `field` | `fields` |
| `Equipment` | `equipment` | `equipment` ✅ (matches) |

### 📋 **Verified Table Structure**

#### Core Tables
```sql
-- Equipment Registry
equipment (equipment_id PK, isobus_address, equipment_type, manufacturer, model, ...)

-- Field Management
fields (field_id PK, field_name, crop_type, field_area_hectares, boundary_coordinates, ...)

-- ISOBUS Communication
isobus_messages (id PK, timestamp, equipment_id FK, pgn, source_address, destination_address, data_payload, ...)

-- Agricultural Sensor Data
agricultural_sensor_data (id PK, timestamp, equipment_id FK, field_id FK, sensor_type, sensor_value, unit, ...)

-- Additional Tables
tractor_telemetry (id PK, timestamp, equipment_id FK, ...)
yield_monitor_data (id PK, timestamp, equipment_id FK, ...)
operational_sessions (id PK, equipment_id FK, field_id FK, ...)
token_usage (id PK, timestamp, agent_id, task_id, tokens_used, ...)
```

### 🔍 **Usage Examples**

#### ✅ **Correct Database Queries**
```python
# Correct table names for direct SQL queries
cursor.execute("SELECT COUNT(*) FROM isobus_messages")
cursor.execute("SELECT * FROM agricultural_sensor_data WHERE sensor_type = 'soil_moisture'")
cursor.execute("SELECT * FROM fields WHERE crop_type = 'corn'")
```

#### ✅ **Correct SQLAlchemy Usage**
```python
# These work because they use the model classes, not table names directly
from afs_fastapi.database.agricultural_schemas_async import ISOBUSMessageRecord, AgriculturalSensorRecord, Field

# SQLAlchemy automatically maps to correct table names
messages = session.query(ISOBUSMessageRecord).all()
sensor_data = session.query(AgriculturalSensorRecord).filter_by(sensor_type='soil_moisture').all()
fields = session.query(Field).filter_by(crop_type='corn').all()
```

#### ❌ **Incorrect Direct SQL (Common Mistake)**
```python
# These will fail because table names don't match the pattern
cursor.execute("SELECT COUNT(*) FROM isobus_message_record")  # ❌ FAILS
cursor.execute("SELECT * FROM agricultural_sensor_record")    # ❌ FAILS
cursor.execute("SELECT * FROM field")                         # ❌ FAILS
```

### 🎯 **Key Insight**

The **model class names** follow singular patterns (`ISOBUSMessageRecord`, `AgriculturalSensorRecord`) but the **actual database table names** follow different patterns:

- `ISOBUSMessageRecord` → `isobus_messages` (plural, no "_record" suffix)
- `AgriculturalSensorRecord` → `agricultural_sensor_data` (descriptive suffix instead of "_record")
- `Field` → `fields` (standard pluralization)
- `Equipment` → `equipment` (mass noun, no plural)

**Always use the model classes in Python code** - SQLAlchemy handles the mapping correctly. **Only reference table names directly for raw SQL queries**.

### 📝 **Verification Method**

These table names were verified through:
1. **Database creation testing** in clean environment
2. **Direct SQLite inspection** of created tables
3. **Functional testing** of CRUD operations
4. **Cross-validation** with model definitions

*Last verified: 2025-11-05 through execution testing*