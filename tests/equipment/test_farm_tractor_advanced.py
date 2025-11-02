import unittest

from afs_fastapi.equipment.farm_tractors import FarmTractor, FieldMode, ImplementPosition


class TestFarmTractorAdvanced(unittest.TestCase):
    def setUp(self):
        """Creates a new FarmTractor instance for each test."""
        self.tractor = FarmTractor("John Deere", "9R Series", 2023)

    def test_gps_controls(self):
        """Test GPS position and auto-steer functionality."""
        # Test GPS position setting
        result = self.tractor.set_gps_position(40.7589, -73.9851)
        self.assertEqual(result, "GPS position set to 40.758900, -73.985100")
        self.assertEqual(self.tractor.gps_latitude, 40.7589)
        self.assertEqual(self.tractor.gps_longitude, -73.9851)

        # Test invalid coordinates
        with self.assertRaises(ValueError):
            self.tractor.set_gps_position(91.0, 0.0)  # Invalid latitude
        with self.assertRaises(ValueError):
            self.tractor.set_gps_position(0.0, 181.0)  # Invalid longitude

        # Test auto-steer (requires engine and GPS)
        with self.assertRaises(ValueError):
            self.tractor.enable_auto_steer()  # Engine off

        self.tractor.start_engine()
        result = self.tractor.enable_auto_steer()
        self.assertEqual(result, "Auto-steer enabled")
        self.assertTrue(self.tractor.auto_steer_enabled)

        # Test disabling auto-steer
        result = self.tractor.disable_auto_steer()
        self.assertEqual(result, "Auto-steer disabled")
        self.assertFalse(self.tractor.auto_steer_enabled)

    def test_waypoint_management(self):
        """Test waypoint addition and management."""
        # Add waypoints
        result = self.tractor.add_waypoint(40.7589, -73.9851)
        self.assertIn("Waypoint added", result)
        self.assertEqual(len(self.tractor.waypoints), 1)

        # Add second waypoint
        self.tractor.add_waypoint(40.7505, -73.9934)
        self.assertEqual(len(self.tractor.waypoints), 2)

        # Clear waypoints
        result = self.tractor.clear_waypoints()
        self.assertEqual(result, "Cleared 2 waypoints")
        self.assertEqual(len(self.tractor.waypoints), 0)

    def test_implement_controls(self):
        """Test implement position controls."""
        self.tractor.start_engine()
        self.tractor.activate_hydraulics()

        # Initially implement should be raised
        self.assertEqual(self.tractor.implement_position, ImplementPosition.RAISED)

        # Test lowering implement
        result = self.tractor.lower_implement(8.0)
        self.assertEqual(result, "Implement lowered to 8.0 inch depth")
        self.assertEqual(self.tractor.implement_position, ImplementPosition.LOWERED)
        self.assertEqual(self.tractor.implement_depth, 8.0)

        # Test transport position
        result = self.tractor.set_transport_position()
        self.assertEqual(result, "Implement set to transport position")
        self.assertEqual(self.tractor.implement_position, ImplementPosition.TRANSPORT)

        # Test setting implement width
        result = self.tractor.set_implement_width(24.0)
        self.assertEqual(result, "Implement width set to 24.0 feet")
        self.assertEqual(self.tractor.implement_width, 24.0)

    def test_field_operations(self):
        """Test field operation modes and work tracking."""
        self.tractor.start_engine()
        self.tractor.activate_hydraulics()

        # Test setting field mode
        result = self.tractor.set_field_mode(FieldMode.PLANTING)
        self.assertEqual(result, "Field mode set to planting")
        self.assertEqual(self.tractor.field_mode, FieldMode.PLANTING)

        # Test starting field work
        self.tractor.lower_implement(6.0)
        self.tractor.set_implement_width(30.0)
        result = self.tractor.start_field_work()
        self.assertEqual(result, "Field work started in planting mode")

        # Test work progress tracking
        result = self.tractor.update_work_progress(1320)  # 1/4 mile
        self.assertIn("Work progress updated", result)
        self.assertGreater(self.tractor.area_covered, 0)

    def test_autonomous_mode(self):
        """Test autonomous operation controls."""
        # Setup for autonomous mode
        self.tractor.start_engine()
        self.tractor.set_gps_position(40.7589, -73.9851)
        self.tractor.enable_auto_steer()
        self.tractor.add_waypoint(40.7505, -73.9934)

        # Test enabling autonomous mode
        result = self.tractor.enable_autonomous_mode()
        self.assertEqual(result, "Autonomous mode enabled")
        self.assertTrue(self.tractor.autonomous_mode)

        # Test disabling autonomous mode
        result = self.tractor.disable_autonomous_mode()
        self.assertEqual(result, "Autonomous mode disabled")
        self.assertFalse(self.tractor.autonomous_mode)

    def test_emergency_stop(self):
        """Test emergency stop functionality."""
        # Setup active systems
        self.tractor.start_engine()
        self.tractor.set_gps_position(40.7589, -73.9851)
        self.tractor.enable_auto_steer()
        self.tractor.add_waypoint(40.7505, -73.9934)
        self.tractor.enable_autonomous_mode()
        self.tractor.accelerate(15)

        # Trigger emergency stop
        result = self.tractor.emergency_stop()  # type: ignore[assignment]
        self.assertTrue(result)  # ISO 18497 interface returns boolean
        self.assertTrue(self.tractor.emergency_stop_active)
        self.assertEqual(self.tractor.speed, 0)
        self.assertFalse(self.tractor.autonomous_mode)
        self.assertFalse(self.tractor.auto_steer_enabled)

        # Reset emergency stop
        result = self.tractor.reset_emergency_stop()
        self.assertEqual(result, "Emergency stop reset - Manual control restored")
        self.assertFalse(self.tractor.emergency_stop_active)

    def test_sensor_diagnostics(self):
        """Test sensor reading methods."""
        self.tractor.start_engine()
        self.tractor.activate_hydraulics()
        self.tractor.accelerate(10)

        # Test engine diagnostics
        engine_data = self.tractor.get_engine_diagnostics()
        self.assertIn("rpm", engine_data)
        self.assertIn("temperature", engine_data)
        self.assertIn("fuel_level", engine_data)
        self.assertGreater(engine_data["rpm"], 0)

        # Test hydraulic status
        hydraulic_data = self.tractor.get_hydraulic_status()
        self.assertIn("pressure", hydraulic_data)
        self.assertIn("flow_rate", hydraulic_data)
        self.assertGreater(hydraulic_data["pressure"], 0)

        # Test ground conditions
        ground_data = self.tractor.get_ground_conditions()
        self.assertIn("wheel_slip", ground_data)
        self.assertIn("ground_speed", ground_data)
        self.assertIn("draft_load", ground_data)

    def test_initialization_with_new_fields(self):
        """Test that new fields are properly initialized."""
        tractor = FarmTractor("Case IH", "Magnum", 2024)

        # Check GPS initialization
        self.assertIsNone(tractor.gps_latitude)
        self.assertIsNone(tractor.gps_longitude)
        self.assertFalse(tractor.auto_steer_enabled)
        self.assertEqual(len(tractor.waypoints), 0)

        # Check implement initialization
        self.assertEqual(tractor.implement_position, ImplementPosition.RAISED)
        self.assertEqual(tractor.implement_depth, 0.0)
        self.assertEqual(tractor.implement_width, 0.0)

        # Check field operation initialization
        self.assertEqual(tractor.field_mode, FieldMode.TRANSPORT)
        self.assertEqual(tractor.work_rate, 0.0)
        self.assertEqual(tractor.area_covered, 0.0)

        # Check autonomous features initialization
        self.assertFalse(tractor.autonomous_mode)
        self.assertTrue(tractor.obstacle_detection)
        self.assertFalse(tractor.emergency_stop_active)


if __name__ == "__main__":
    unittest.main()
