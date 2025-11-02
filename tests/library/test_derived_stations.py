import unittest

from afs_fastapi.stations.station_types import (
    DiagnosticsStation,
    DroidDispatchStation,
    RepairStation,
    ServiceDispatchStation,
)


class TestDiagnosticsStation(unittest.TestCase):
    """Unit tests for the DiagnosticsStation class."""

    def setUp(self):
        """Initialize a DiagnosticsStation instance for testing."""
        self.station = DiagnosticsStation(1, "PowerGrid", ["Voltage Tester", "Thermal Scanner"])

    def test_run_diagnostics(self):
        """Test that diagnostics run correctly and return expected output."""
        result = self.station.run_diagnostics()
        self.assertIn("Running diagnostics", result)


class TestDroidDispatchStation(unittest.TestCase):
    """Unit tests for the DroidDispatchStation class."""

    def setUp(self):
        """Initialize a DroidDispatchStation instance for testing."""
        self.station = DroidDispatchStation(2, "Security", 5)

    def test_deploy_droid(self):
        """Test that a droid is deployed correctly and count decreases."""
        initial_count = self.station.droid_count
        result = self.station.deploy_droid()
        self.assertEqual(self.station.droid_count, initial_count - 1)
        self.assertIn("Droid deployed", result)


class TestServiceDispatchStation(unittest.TestCase):
    """Unit tests for the ServiceDispatchStation class."""

    def setUp(self):
        """Initialize a ServiceDispatchStation instance for testing."""
        self.station = ServiceDispatchStation(3, "Logistics", 2)

    def test_assign_task(self):
        """Test that a task is assigned correctly and active tasks increase."""
        initial_tasks = self.station.active_tasks
        result = self.station.assign_task()
        self.assertEqual(self.station.active_tasks, initial_tasks + 1)
        self.assertIn("Task assigned", result)


class TestRepairStation(unittest.TestCase):
    """Unit tests for the RepairStation class."""

    def setUp(self):
        """Initialize a RepairStation instance for testing."""
        self.station = RepairStation(4, "Mechanical", 3)

    def test_perform_repair(self):
        """Test that a repair is performed correctly and capacity decreases."""
        initial_capacity = self.station.repair_capacity
        result = self.station.perform_repair()
        self.assertEqual(self.station.repair_capacity, initial_capacity - 1)
        self.assertIn("Repair performed", result)


if __name__ == "__main__":
    unittest.main()
