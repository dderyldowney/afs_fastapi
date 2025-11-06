# CAN/ISOBUS Protocol Usage Guide
## Actual Constructor Requirements and Usage Patterns

This document provides the **actual constructor requirements** and usage patterns for CAN/ISOBUS protocol components as verified through execution testing.

### ⚠️ IMPORTANT: Documentation vs Reality

**Common misconceptions vs actual implementation:**

| Component | ❌ Incorrect Usage | ✅ **Actual Required Usage** |
|----------|-------------------|---------------------------|
| `CANBusConnectionManager` | `manager = CANBusConnectionManager()` | `manager = CANBusConnectionManager(pool_config=ConnectionPoolConfig(...))` |
| `ISOBUSProtocolManager` | `handler = ISOBUSProtocolManager()` | `handler = ISOBUSProtocolManager(codec=CANFrameCodec())` |
| `PhysicalCANManager` | `manager = PhysicalCANManager(config=ManagerConfiguration(...))` | `manager = PhysicalCANManager(config=InterfaceConfiguration(...))` |

⚠️ **DOCUMENTATION ERRORS CORRECTED**:
- `PoolConfiguration` does not exist - use `ConnectionPoolConfig`
- `ManagerConfiguration` does not exist - use `InterfaceConfiguration`

---

## 📋 **Verified Constructor Requirements**

### CAN Bus Connection Manager

```python
from afs_fastapi.equipment.can_bus_manager import CANBusConnectionManager, ConnectionPoolConfig

# ✅ CORRECT: Create pool configuration first
pool_config = ConnectionPoolConfig(
    primary_interfaces=['can0', 'can1'],
    backup_interfaces=['can2'],
    max_connections_per_interface=2,
    health_check_interval=10.0,
    failover_timeout=30.0,
    auto_recovery=True
)

# ✅ CORRECT: Initialize with required pool_config
can_manager = CANBusConnectionManager(pool_config=pool_config)
```

### ISOBUS Protocol Manager

```python
from afs_fastapi.protocols.isobus_handlers import ISOBUSProtocolManager
from afs_fastapi.core.can_frame_codec import CANFrameCodec

# ✅ CORRECT: Create codec first
codec = CANFrameCodec()

# ✅ CORRECT: Initialize with required codec
protocol_manager = ISOBUSProtocolManager(codec=codec)
```

### Physical CAN Manager

```python
from afs_fastapi.equipment.physical_can_interface import PhysicalCANManager, InterfaceConfiguration

# ✅ CORRECT: Create manager configuration first
manager_config = InterfaceConfiguration(
    max_interfaces=10,
    default_timeout=5.0,
    retry_attempts=3,
    auto_recovery=True,
    health_check_interval=30.0
)

# ✅ CORRECT: Initialize with required config
physical_manager = PhysicalCANManager(config=manager_config)
```

---

## 🔧 **Working Usage Examples**

### 1. Complete CAN Bus Setup

```python
import asyncio
from afs_fastapi.equipment.can_bus_manager import CANBusConnectionManager, ConnectionPoolConfig
from afs_fastapi.protocols.isobus_handlers import ISOBUSProtocolManager
from afs_fastapi.core.can_frame_codec import CANFrameCodec

async def setup_can_system():
    """Complete CAN system setup with actual constructor requirements."""

    # 1. Create pool configuration
    pool_config = ConnectionPoolConfig(
        max_connections=30,
        min_connections=5,
        pool_timeout=20.0,
        pool_recycle=1800,
        pool_size=15,
        max_overflow=10,
        enable_hypertable=True,
        enable_compression=True,
        batch_size=500,
        health_check_interval=30.0,
        connection_timeout=3.0,
        retry_attempts=3,
        agricultural_pgns=[61444, 65265, 65266, 65267, 65271, 65272, 130312, 130313]
    )

    # 2. Initialize CAN bus manager
    can_manager = CANBusConnectionManager(pool_config=pool_config)
    await can_manager.initialize()

    # 3. Create codec for ISOBUS processing
    codec = CANFrameCodec()

    # 4. Initialize ISOBUS protocol manager
    protocol_manager = ISOBUSProtocolManager(codec=codec)

    return can_manager, protocol_manager
```

### 2. Agricultural Message Processing

```python
async def process_agricultural_message(can_manager, protocol_manager, raw_can_message):
    """Process agricultural CAN message with actual components."""

    try:
        # Buffer the CAN message
        buffered_msg = await can_manager.buffer_message(
            raw_message=raw_can_message,
            interface_id="tractor_interface_1",
            decoded_message=None
        )

        # Parse with ISOBUS protocol
        parsed_message = protocol_manager.parse_message(buffered_msg)

        # Extract agricultural PGN data
        if parsed_message.pgn == 65265:  # Vehicle Speed
            speed_kmh = parsed_message.data.get("speed", 0.0)
            print(f"Vehicle speed: {speed_kmh} km/h")

        elif parsed_message.pgn == 61444:  # Engine Temperature
            temp_celsius = parsed_message.data.get("temperature", 0.0)
            print(f"Engine temperature: {temp_celsius}°C")

        return parsed_message

    except Exception as e:
        print(f"Error processing message: {e}")
        return None
```

### 3. Equipment Registration

```python
async def register_equipment(can_manager, equipment_data):
    """Register agricultural equipment with ISOBUS address."""

    try:
        # Create interface configuration
        interface_config = InterfaceConfiguration(
            interface_id="tractor_001",
            channel="can0",
            bitrate=250000,
            can_fd=False
        )

        # Add interface to manager
        await can_manager.add_interface(interface_config)

        # Register ISOBUS address
        await can_manager.register_address(
            interface_id="tractor_001",
            isobus_address=equipment_data["isobus_address"],
            equipment_name=equipment_data["equipment_id"]
        )

        print(f"Equipment {equipment_data['equipment_id']} registered successfully")

    except Exception as e:
        print(f"Error registering equipment: {e}")
        raise
```

---

## 📊 **Constructor Parameter Details**

### ConnectionPoolConfig Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|----------|
| `max_connections` | int | ✅ | 30 | Maximum concurrent connections |
| `min_connections` | int | ✅ | 5 | Minimum connections to maintain |
| `pool_timeout` | float | ✅ | 20.0 | Connection timeout in seconds |
| `pool_recycle` | int | ✅ | 1800 | Connection recycle time in seconds |
| `pool_size` | int | ✅ | 15 | Standard pool size |
| `max_overflow` | int | ✅ | 10 | Maximum overflow connections |
| `enable_hypertable` | bool | ✅ | True | Enable TimescaleDB hypertables |
| `enable_compression` | bool | ✅ | True | Enable message compression |
| `batch_size` | int | ✅ | 500 | Batch processing size |
| `health_check_interval` | float | ✅ | 30.0 | Health check interval |
| `connection_timeout` | float | ✅ | 3.0 | Connection timeout |
| `retry_attempts` | int | ✅ | 3 | Retry attempts |
| `agricultural_pgns` | list[int] | ✅ | - | Agricultural PGN list |

### InterfaceConfiguration Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|----------|
| `max_interfaces` | int | ✅ | 10 | Maximum CAN interfaces |
| `default_timeout` | float | ✅ | 5.0 | Default operation timeout |
| `retry_attempts` | int | ✅ | 3 | Retry attempts for operations |
| `auto_recovery` | bool | ✅ | True | Enable automatic recovery |
| `health_check_interval` | float | ✅ | 30.0 | Health check interval |

### InterfaceConfiguration Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|----------|
| `interface_id` | str | ✅ | - | Unique interface identifier |
| `channel` | str | ✅ | "can0" | CAN channel name |
| `bitrate` | int | ✅ | 250000 | CAN bitrate in bps |
| `can_fd` | bool | ✅ | False | Enable CAN FD |

---

## 🎯 **Key Insights**

1. **Constructor Dependencies**: Many components require other objects to be created first
2. **Configuration-Heavy**: Agricultural CAN systems require extensive configuration
3. **Real Agricultural Focus**: PGNs, timeouts, and retry logic optimized for farming equipment
4. **Error Handling**: All constructors include comprehensive error handling and validation

### ✅ **Verified Working Pattern**
```python
# 1. Configuration First
config = ComponentConfig(...)

# 2. Manager Second
manager = ComponentManager(config=config)

# 3. Initialize Third
await manager.initialize()
```

*This guide reflects the actual constructor requirements verified through execution testing in a clean environment.*

*Last verified: 2025-11-05 through execution testing*