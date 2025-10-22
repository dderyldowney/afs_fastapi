from datetime import datetime
from typing import Any

from .interfaces import DummyWaterSensorBackend, WaterSensorBackend


class WaterMonitor:
    def __init__(self, sensor_id: str, backend: WaterSensorBackend | None = None) -> None:
        self.sensor_id = sensor_id
        self.backend: WaterSensorBackend = backend or DummyWaterSensorBackend()
        self.last_reading: dict[str, Any] = {}

    def get_water_quality(self) -> dict[str, float]:
        """Get water quality readings via the configured backend."""
        return self.backend.read(self.sensor_id)

    def log_reading(self) -> None:
        """Log current water quality readings with timestamp."""
        self.last_reading = {
            "timestamp": datetime.now(),
            "readings": self.get_water_quality(),
        }
