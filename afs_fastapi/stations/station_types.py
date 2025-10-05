# afs_fastapi/stations/station_types.py
from enum import Enum


class StationType(Enum):
    MASTER = "master"
    DIAGNOSTIC = "diagnostic"
    SERVICE_DISPATCH = "service_dispatch"
    MONITORING = "monitoring"
    DROID_DISPATCH = "droid_dispatch"
    REPAIR_SERVICE = "repair_service"


def get_station_type(station_type_str: str) -> StationType:
    try:
        return StationType(station_type_str.lower())
    except ValueError as e:
        raise ValueError(f"Invalid station type: {station_type_str}") from e


class MasterStation:
    def __init__(self, station_id: int, system: str):
        self.station_id = station_id
        self.system = system

    def activate(self) -> str:
        return f"Master station {self.station_id} for {self.system} system is activated."

    def deactivate(self) -> str:
        return f"Master station {self.station_id} for {self.system} system is deactivated."


class DiagnosticsStation(MasterStation):
    """
    A diagnostics station responsible for system diagnostics and reporting.
    """

    def __init__(self, station_id: int, system: str, diagnostic_tools: list[str]):
        super().__init__(station_id, system)
        self.station_type = StationType.DIAGNOSTIC
        self.diagnostic_tools: list[str] = diagnostic_tools

    def run_diagnostics(self) -> str:
        """Run diagnostics using available tools."""
        return f"Running diagnostics at station {self.station_id} using {', '.join(self.diagnostic_tools)}."


class DroidDispatchStation(MasterStation):
    """
    A droid dispatch station responsible for managing and deploying droids.
    """

    def __init__(self, station_id: int, system: str, droid_count: int):
        super().__init__(station_id, system)
        self.station_type = StationType.DROID_DISPATCH
        self.droid_count: int = droid_count

    def deploy_droid(self) -> str:
        """Deploy a droid if available."""
        if self.droid_count > 0:
            self.droid_count -= 1
            return f"Droid deployed from station {self.station_id}. Remaining: {self.droid_count}"
        return "No droids available for dispatch."


class ServiceDispatchStation(MasterStation):
    """
    A service dispatch station handling service task assignments.
    """

    def __init__(self, station_id: int, system: str, active_tasks: int):
        super().__init__(station_id, system)
        self.station_type = StationType.SERVICE_DISPATCH
        self.active_tasks: int = active_tasks

    def assign_task(self) -> str:
        """Assign a new task."""
        self.active_tasks += 1
        return f"Task assigned at station {self.station_id}. Active tasks: {self.active_tasks}"


class RepairStation(MasterStation):
    """
    A repair station responsible for repairing damaged systems or units.
    """

    def __init__(self, station_id: int, system: str, repair_capacity: int):
        super().__init__(station_id, system)
        self.station_type = StationType.REPAIR_SERVICE
        self.repair_capacity: int = repair_capacity

    def perform_repair(self) -> str:
        """Perform a repair if capacity allows."""
        if self.repair_capacity > 0:
            self.repair_capacity -= 1
            return f"Repair performed at station {self.station_id}. Remaining capacity: {self.repair_capacity}"
        return "Repair station at full capacity, cannot perform repairs."
