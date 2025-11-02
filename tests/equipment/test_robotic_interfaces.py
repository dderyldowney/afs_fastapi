"""
Tests for robotic interfaces and enhanced FarmTractor functionality.

This module tests the newly added interfaces for ISOBUS communication,
safety systems, motor control, data management, and power management.
"""

import unittest
from datetime import datetime

from afs_fastapi.equipment.farm_tractors import (
    CameraConfig,
    FarmTractor,
    ISOBUSMessage,
    LiDARPoint,
    MotorCommand,
    PowerSource,
    SafetyLevel,
    SafetyZone,
    TaskData,
)


class TestISOBUSInterfaces(unittest.TestCase):
    """Test ISOBUS communication interfaces."""

    def setUp(self):
        self.tractor = FarmTractor("Test", "Tractor", 2024)

    def test_isobus_device_name(self):
        """Test ISOBUS device name generation."""
        device_name = self.tractor.get_device_name()
        self.assertEqual(device_name, "Test_Tractor_2024")

    def test_isobus_message_creation(self):
        """Test ISOBUS message structure."""
        message = ISOBUSMessage(
            pgn=0xFE48,
            source_address=0x80,
            destination_address=0xFF,
            data=b"\x01\x02\x03",
            timestamp=datetime.now(),
        )

        self.assertEqual(message.pgn, 0xFE48)
        self.assertEqual(message.source_address, 0x80)
        self.assertEqual(message.destination_address, 0xFF)
        self.assertEqual(message.data, b"\x01\x02\x03")
        self.assertIsInstance(message.timestamp, datetime)

    def test_send_tractor_status(self):
        """Test ISOBUS tractor status transmission."""
        self.tractor.start_engine()
        self.tractor.change_gear(3)
        self.tractor.accelerate(15)

        result = self.tractor.send_tractor_status()
        self.assertTrue(result)

    def test_message_queue_handling(self):
        """Test ISOBUS message queue management."""
        # Initially empty queue
        message = self.tractor.receive_message()
        self.assertIsNone(message)

        # Add message to queue
        test_message = ISOBUSMessage(
            pgn=0xFE48,
            source_address=0x80,
            destination_address=0xFF,
            data=b"\x01\x02\x03",
            timestamp=datetime.now(),
        )
        self.tractor.message_queue.append(test_message)

        # Receive message
        received = self.tractor.receive_message()
        self.assertEqual(received, test_message)
        self.assertEqual(len(self.tractor.message_queue), 0)


class TestSafetyInterfaces(unittest.TestCase):
    """Test ISO 18497 safety and compliance interfaces."""

    def setUp(self):
        self.tractor = FarmTractor("Test", "Tractor", 2024)
        self.tractor.start_engine()

    def test_emergency_stop(self):
        """Test ISO 18497 emergency stop functionality."""
        # Setup active systems
        self.tractor.set_gps_position(40.0, -73.0)
        self.tractor.enable_auto_steer()
        self.tractor.add_waypoint(40.1, -73.1)  # Add waypoint for autonomous mode
        self.tractor.accelerate(20)
        self.tractor.enable_autonomous_mode()

        # Trigger emergency stop
        result = self.tractor.emergency_stop()

        self.assertTrue(result)
        self.assertTrue(self.tractor.emergency_stop_active)
        self.assertEqual(self.tractor.speed, 0)
        self.assertFalse(self.tractor.autonomous_mode)
        self.assertFalse(self.tractor.auto_steer_enabled)

    def test_safety_zone_creation(self):
        """Test safety zone definition and validation."""
        zone = SafetyZone(
            zone_id="field_01",
            boundary_points=[(40.0, -73.0), (40.1, -73.0), (40.1, -73.1), (40.0, -73.1)],
            safety_level=SafetyLevel.PERFORMANCE_LEVEL_C,
            max_speed=25.0,
            detection_required=True,
        )

        result = self.tractor.add_safety_zone(zone)
        self.assertIn("Safety zone field_01 added", result)
        self.assertEqual(len(self.tractor.safety_zones), 1)

    def test_safety_zone_validation(self):
        """Test position validation within safety zones."""
        # No zones defined - should allow any position
        result = self.tractor.validate_safety_zone((40.0, -73.0))
        self.assertTrue(result)

        # Add a safety zone
        zone = SafetyZone(
            zone_id="test_zone",
            boundary_points=[(40.0, -73.0), (40.1, -73.0), (40.1, -73.1), (40.0, -73.1)],
            safety_level=SafetyLevel.PERFORMANCE_LEVEL_C,
            max_speed=25.0,
            detection_required=True,
        )
        self.tractor.add_safety_zone(zone)

        # Test position validation (simplified implementation always returns True)
        result = self.tractor.validate_safety_zone((40.05, -73.05))
        self.assertTrue(result)

    def test_safety_status_reporting(self):
        """Test comprehensive safety status reporting."""
        self.tractor.set_gps_position(40.0, -73.0)

        status = self.tractor.get_safety_status()

        self.assertIn("emergency_stop_active", status)
        self.assertIn("safety_system_operational", status)
        self.assertIn("position_safe", status)
        self.assertIn("obstacle_detection_active", status)
        self.assertIn("speed_limit_compliant", status)
        self.assertIn("operator_present", status)

        self.assertFalse(status["emergency_stop_active"])
        self.assertTrue(status["safety_system_operational"])
        self.assertTrue(status["obstacle_detection_active"])


class TestMotorControlInterfaces(unittest.TestCase):
    """Test precision motor control interfaces."""

    def setUp(self):
        self.tractor = FarmTractor("Test", "Tractor", 2024)

    def test_motor_command_creation(self):
        """Test motor command structure."""
        command = MotorCommand(
            motor_id="steer_motor",
            command_type="position",
            target_value=45.0,
            max_velocity=10.0,
            max_acceleration=5.0,
        )

        self.assertEqual(command.motor_id, "steer_motor")
        self.assertEqual(command.command_type, "position")
        self.assertEqual(command.target_value, 45.0)
        self.assertEqual(command.max_velocity, 10.0)
        self.assertEqual(command.max_acceleration, 5.0)

    def test_motor_position_control(self):
        """Test motor position control commands."""
        command = MotorCommand(motor_id="steer_motor", command_type="position", target_value=30.0)

        result = self.tractor.send_motor_command(command)
        self.assertTrue(result)

        status = self.tractor.get_motor_status("steer_motor")
        self.assertEqual(status["position"], 30.0)

    def test_motor_velocity_control(self):
        """Test motor velocity control commands."""
        command = MotorCommand(
            motor_id="throttle_motor", command_type="velocity", target_value=15.0
        )

        result = self.tractor.send_motor_command(command)
        self.assertTrue(result)

        status = self.tractor.get_motor_status("throttle_motor")
        self.assertEqual(status["velocity"], 15.0)

    def test_motor_torque_control(self):
        """Test motor torque control commands."""
        command = MotorCommand(motor_id="implement_lift", command_type="torque", target_value=100.0)

        result = self.tractor.send_motor_command(command)
        self.assertTrue(result)

        status = self.tractor.get_motor_status("implement_lift")
        self.assertEqual(status["torque"], 100.0)

    def test_motor_calibration(self):
        """Test motor calibration sequences."""
        # Calibrate existing motor
        result = self.tractor.calibrate_motor("steer_motor")
        self.assertTrue(result)

        status = self.tractor.get_motor_status("steer_motor")
        self.assertEqual(status["position"], 0.0)
        self.assertEqual(status["velocity"], 0.0)
        self.assertEqual(status["torque"], 0.0)

    def test_invalid_motor_operations(self):
        """Test operations on non-existent motors."""
        # Invalid motor command
        command = MotorCommand(
            motor_id="nonexistent_motor", command_type="position", target_value=10.0
        )

        result = self.tractor.send_motor_command(command)
        self.assertFalse(result)

        # Invalid motor status request
        status = self.tractor.get_motor_status("nonexistent_motor")
        self.assertEqual(status["error"], -1.0)

        # Invalid motor calibration
        result = self.tractor.calibrate_motor("nonexistent_motor")
        self.assertFalse(result)


class TestDataManagementInterfaces(unittest.TestCase):
    """Test agricultural data management interfaces."""

    def setUp(self):
        self.tractor = FarmTractor("Test", "Tractor", 2024)

    def test_task_data_creation(self):
        """Test ISO XML task data structure."""
        task = TaskData(
            task_id="TASK_001",
            field_id="FIELD_A",
            operation_type="planting",
            prescription_map={"seed_rate": 32000.0},
            start_time=datetime.now(),
        )

        self.assertEqual(task.task_id, "TASK_001")
        self.assertEqual(task.field_id, "FIELD_A")
        self.assertEqual(task.operation_type, "planting")
        self.assertIsNotNone(task.prescription_map)
        if task.prescription_map is not None:
            self.assertEqual(task.prescription_map["seed_rate"], 32000.0)
        self.assertIsNone(task.end_time)

    def test_iso_xml_export(self):
        """Test ISO 11783-10 XML data export."""
        task = TaskData(
            task_id="TASK_001",
            field_id="FIELD_A",
            operation_type="planting",
            prescription_map=None,
            start_time=datetime.now(),
        )

        xml_output = self.tractor.export_iso_xml(task)

        self.assertIn("<?xml version", xml_output)
        self.assertIn("ISO11783_TaskData", xml_output)
        self.assertIn("TASK_001", xml_output)
        self.assertIn("planting", xml_output)
        self.assertIn("FIELD_A", xml_output)

    def test_prescription_map_import(self):
        """Test variable rate prescription map import."""
        # Simulate map data
        map_data = b"mock_prescription_map_data"

        prescription = self.tractor.import_prescription_map(map_data)

        self.assertIn("seed_rate", prescription)
        self.assertIn("fertilizer_rate", prescription)
        self.assertIn("spray_rate", prescription)
        self.assertEqual(prescription["seed_rate"], 30026.0)

    def test_operation_logging(self):
        """Test operational data logging."""
        # Log initial data point
        data_point = {"depth": 2.5, "spacing": 6.0, "seed_count": 1000.0}

        result = self.tractor.log_operation_data(data_point)
        self.assertTrue(result)
        self.assertEqual(len(self.tractor.operation_log), 1)

        # Check enhanced data
        logged_data = self.tractor.operation_log[0]
        self.assertIn("timestamp", logged_data)
        self.assertIn("speed", logged_data)
        self.assertIn("fuel_level", logged_data)
        # The operation data doesn't include operation type - just core metrics
        self.assertIn("engine_rpm", logged_data)

    def test_task_recording(self):
        """Test field task recording functionality."""
        # Start task recording
        result = self.tractor.start_task_recording("TASK_002", "FIELD_B", "spraying")
        self.assertEqual(result, "Task recording started: TASK_002")
        self.assertIsNotNone(self.tractor.current_task)

        # Stop task recording
        result = self.tractor.stop_task_recording()
        self.assertEqual(result, "Task recording stopped: TASK_002")
        self.assertIsNone(self.tractor.current_task)

        # Try to stop when no task active
        result = self.tractor.stop_task_recording()
        self.assertEqual(result, "No active task to stop")


class TestPowerManagementInterfaces(unittest.TestCase):
    """Test power and energy management interfaces."""

    def setUp(self):
        self.tractor = FarmTractor("Test", "Tractor", 2024)

    def test_power_source_creation(self):
        """Test power source configuration."""
        source = PowerSource(source_type="solar", voltage=24.0, max_current=50.0, efficiency=0.85)

        self.assertEqual(source.source_type, "solar")
        self.assertEqual(source.voltage, 24.0)
        self.assertEqual(source.max_current, 50.0)
        self.assertEqual(source.efficiency, 0.85)

    def test_power_status_reporting(self):
        """Test comprehensive power status reporting."""
        self.tractor.start_engine()

        status = self.tractor.get_power_status()

        self.assertIn("total_available_power", status)
        self.assertIn("total_consumption", status)
        self.assertIn("power_efficiency", status)
        self.assertIn("battery_level", status)
        self.assertIn("regenerative_active", status)
        self.assertIn("diesel_engine_load", status)

        self.assertGreater(status["total_available_power"], 0)
        self.assertFalse(status["regenerative_active"])

    def test_power_priority_management(self):
        """Test power allocation priority setting."""
        priorities = {"engine_control": 1, "steering": 2, "implements": 3, "comfort": 4}

        result = self.tractor.set_power_priority(priorities)
        self.assertTrue(result)

    def test_regenerative_mode(self):
        """Test regenerative energy recovery mode."""
        # Cannot enable without engine
        result = self.tractor.enable_regenerative_mode()
        self.assertFalse(result)

        # Enable with engine running
        self.tractor.start_engine()
        result = self.tractor.enable_regenerative_mode()
        self.assertTrue(result)
        self.assertTrue(self.tractor.regenerative_mode)

        # Disable regenerative mode
        result = self.tractor.disable_regenerative_mode()
        self.assertTrue(result)
        self.assertFalse(self.tractor.regenerative_mode)


class TestVisionSensorInterfaces(unittest.TestCase):
    """Test vision and sensor data structures."""

    def test_camera_config_creation(self):
        """Test camera configuration structure."""
        config = CameraConfig(
            resolution=(1920, 1080),
            frame_rate=30,
            field_of_view=90.0,
            exposure_mode="auto",
            color_space="RGB",
        )

        self.assertEqual(config.resolution, (1920, 1080))
        self.assertEqual(config.frame_rate, 30)
        self.assertEqual(config.field_of_view, 90.0)
        self.assertEqual(config.exposure_mode, "auto")
        self.assertEqual(config.color_space, "RGB")

    def test_lidar_point_creation(self):
        """Test LiDAR point data structure."""
        point = LiDARPoint(x=10.5, y=25.3, z=1.8, intensity=0.85, timestamp=datetime.now())

        self.assertEqual(point.x, 10.5)
        self.assertEqual(point.y, 25.3)
        self.assertEqual(point.z, 1.8)
        self.assertEqual(point.intensity, 0.85)
        self.assertIsInstance(point.timestamp, datetime)


class TestFarmTractorEnhancedInitialization(unittest.TestCase):
    """Test enhanced FarmTractor initialization with new interfaces."""

    def test_isobus_initialization(self):
        """Test ISOBUS interface initialization."""
        tractor = FarmTractor("John Deere", "8R Series", 2024)

        self.assertEqual(tractor.isobus_address, 0x80)
        self.assertEqual(tractor.device_name, "John Deere_8R Series_2024")
        self.assertEqual(len(tractor.message_queue), 0)

    def test_safety_system_initialization(self):
        """Test safety system initialization."""
        tractor = FarmTractor("Case IH", "Magnum", 2024)

        self.assertEqual(len(tractor.safety_zones), 0)
        self.assertEqual(tractor.safety_level, SafetyLevel.PERFORMANCE_LEVEL_C)
        self.assertTrue(tractor.safety_system_active)

    def test_motor_control_initialization(self):
        """Test motor control system initialization."""
        tractor = FarmTractor("New Holland", "T9", 2024)

        self.assertIn("steer_motor", tractor.motors)
        self.assertIn("throttle_motor", tractor.motors)
        self.assertIn("implement_lift", tractor.motors)

        for motor_id, status in tractor.motors.items():
            self.assertEqual(status["position"], 0.0)
            self.assertIsInstance(motor_id, str)
            self.assertEqual(status["velocity"], 0.0)
            self.assertEqual(status["torque"], 0.0)

    def test_data_management_initialization(self):
        """Test data management system initialization."""
        tractor = FarmTractor("Massey Ferguson", "8700", 2024)

        self.assertEqual(len(tractor.operation_log), 0)
        self.assertIsNone(tractor.current_task)

    def test_power_management_initialization(self):
        """Test power management system initialization."""
        tractor = FarmTractor("Kubota", "M7", 2024)

        self.assertEqual(len(tractor.power_sources), 2)
        self.assertEqual(tractor.power_sources[0].source_type, "diesel_engine")
        self.assertEqual(tractor.power_sources[1].source_type, "alternator")
        self.assertEqual(len(tractor.power_consumption), 0)
        self.assertFalse(tractor.regenerative_mode)

    def test_vision_sensor_initialization(self):
        """Test vision sensor system initialization."""
        tractor = FarmTractor("Fendt", "1000", 2024)

        self.assertIsNone(tractor.camera_config)
        self.assertFalse(tractor.lidar_enabled)
        self.assertEqual(len(tractor.obstacle_list), 0)


class TestIntegratedRoboticOperations(unittest.TestCase):
    """Test integrated robotic operations combining multiple interfaces."""

    def setUp(self):
        self.tractor = FarmTractor("Robotic", "TestTractor", 2024)

    def test_complete_autonomous_setup(self):
        """Test complete setup for autonomous operation."""
        # Start engine and basic setup
        self.tractor.start_engine()
        self.tractor.set_gps_position(40.0, -73.0)

        # Add safety zone
        zone = SafetyZone(
            zone_id="work_area",
            boundary_points=[(39.9, -73.1), (40.1, -73.1), (40.1, -72.9), (39.9, -72.9)],
            safety_level=SafetyLevel.PERFORMANCE_LEVEL_D,
            max_speed=20.0,
            detection_required=True,
        )
        self.tractor.add_safety_zone(zone)

        # Setup motors
        steer_command = MotorCommand("steer_motor", "position", 0.0)
        self.tractor.send_motor_command(steer_command)

        # Enable autonomous systems
        self.tractor.enable_auto_steer()
        self.tractor.add_waypoint(40.05, -73.05)
        self.tractor.enable_autonomous_mode()

        # Start task recording
        self.tractor.start_task_recording("AUTO_001", "FIELD_ROBOT", "autonomous_test")

        # Verify integrated state
        self.assertTrue(self.tractor.autonomous_mode)
        self.assertTrue(self.tractor.auto_steer_enabled)
        self.assertEqual(len(self.tractor.safety_zones), 1)
        self.assertIsNotNone(self.tractor.current_task)

    def test_emergency_response_integration(self):
        """Test integrated emergency response across all systems."""
        # Setup active systems
        self.tractor.start_engine()
        self.tractor.set_gps_position(40.0, -73.0)
        self.tractor.enable_auto_steer()
        self.tractor.add_waypoint(40.1, -73.1)
        self.tractor.enable_autonomous_mode()
        self.tractor.accelerate(15)

        # Start power monitoring
        self.tractor.enable_regenerative_mode()

        # Trigger emergency stop
        result = self.tractor.emergency_stop()

        # Verify all systems responded
        self.assertTrue(result)
        self.assertEqual(self.tractor.speed, 0)
        self.assertFalse(self.tractor.autonomous_mode)
        self.assertFalse(self.tractor.auto_steer_enabled)
        self.assertTrue(self.tractor.emergency_stop_active)

        # Verify data logging occurred
        self.assertGreater(len(self.tractor.operation_log), 0)
        last_log = self.tractor.operation_log[-1]
        self.assertEqual(last_log["event_code"], 999.0)  # Emergency stop event code


if __name__ == "__main__":
    unittest.main()
