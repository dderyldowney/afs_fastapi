from afs_fastapi.monitoring.soil_monitor import SoilMonitor
from afs_fastapi.monitoring.water_monitor import WaterMonitor


def test_soil_monitor():
    monitor = SoilMonitor("test_sensor")
    readings = monitor.get_soil_composition()
    assert isinstance(readings, dict)
    assert "ph" in readings


def test_water_monitor():
    monitor = WaterMonitor("test_sensor")
    readings = monitor.get_water_quality()
    assert isinstance(readings, dict)
    assert "ph" in readings
