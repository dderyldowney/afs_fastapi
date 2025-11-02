from datetime import datetime

from afs_fastapi.monitoring.soil_monitor import SoilMonitor


def test_soil_monitor_initialization():
    sensor_id = "SOIL_001"
    monitor = SoilMonitor(sensor_id)
    assert monitor.sensor_id == sensor_id
    assert monitor.last_reading == {}


def test_soil_composition_reading():
    monitor = SoilMonitor("SOIL_001")
    readings = monitor.get_soil_composition()

    # Check that all expected measurements are present
    assert isinstance(readings, dict)
    assert all(key in readings for key in ["nitrogen", "phosphorus", "potassium", "ph", "moisture"])

    # Check value ranges
    assert 0 <= readings["ph"] <= 14  # pH scale
    assert all(0 <= readings[nutrient] for nutrient in ["nitrogen", "phosphorus", "potassium"])
    assert 0 <= readings["moisture"] <= 100  # percentage


def test_soil_monitor_log_reading():
    monitor = SoilMonitor("SOIL_001")
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
    assert all(key in readings for key in ["nitrogen", "phosphorus", "potassium", "ph", "moisture"])
