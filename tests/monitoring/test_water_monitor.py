from datetime import datetime

from afs_fastapi.monitoring.water_monitor import WaterMonitor


def test_water_monitor_initialization():
    sensor_id = "WATER_001"
    monitor = WaterMonitor(sensor_id)
    assert monitor.sensor_id == sensor_id
    assert monitor.last_reading == {}


def test_water_quality_reading():
    monitor = WaterMonitor("WATER_001")
    readings = monitor.get_water_quality()

    # Check that all expected measurements are present
    assert isinstance(readings, dict)
    assert all(
        key in readings
        for key in ["ph", "dissolved_oxygen", "temperature", "conductivity", "turbidity"]
    )

    # Check value ranges
    assert 0 <= readings["ph"] <= 14  # pH scale
    assert readings["dissolved_oxygen"] >= 0  # mg/L
    assert readings["temperature"] >= -10  # Celsius
    assert readings["conductivity"] >= 0  # μS/cm
    assert readings["turbidity"] >= 0  # NTU


def test_water_monitor_log_reading():
    monitor = WaterMonitor("WATER_001")
    assert monitor.last_reading == {}

    monitor.log_reading()

    # Verify the log structure
    assert "timestamp" in monitor.last_reading
    assert "readings" in monitor.last_reading
    assert isinstance(monitor.last_reading["timestamp"], datetime)
    assert isinstance(monitor.last_reading["readings"], dict)

    # Verify readings content
    from typing import cast

    readings = cast(dict[str, object], monitor.last_reading["readings"])
    assert all(
        key in readings
        for key in ["ph", "dissolved_oxygen", "temperature", "conductivity", "turbidity"]
    )
