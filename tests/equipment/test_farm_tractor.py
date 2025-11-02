import unittest

from afs_fastapi.equipment.farm_tractors import FarmTractor


class TestFarmTractor(unittest.TestCase):
    def setUp(self):
        """
        Creates a new FarmTractor instance for each test.
        """
        self.tractor = FarmTractor("John Deere", "Model X", 2023, "https://manual.johndeere.com")

    def test_initialization(self):
        """
        Test proper initialization of a FarmTractor instance.
        """
        self.assertEqual(self.tractor.make, "John Deere")
        self.assertEqual(self.tractor.model, "Model X")
        self.assertEqual(self.tractor.year, 2023)
        self.assertEqual(self.tractor.manual_url, "https://manual.johndeere.com")
        self.assertFalse(self.tractor.engine_on)
        self.assertEqual(self.tractor.speed, 0)
        self.assertEqual(self.tractor.gear, 0)
        self.assertFalse(self.tractor.power_takeoff)
        self.assertFalse(self.tractor.hydraulics)

    def test_start_engine(self):
        """
        Test starting the engine.
        """
        self.assertEqual(self.tractor.start_engine(), "Engine started.")
        self.assertTrue(self.tractor.engine_on)

        with self.assertRaises(ValueError) as context:
            self.tractor.start_engine()
        self.assertEqual(str(context.exception), "Engine is already running.")

    def test_stop_engine(self):
        """
        Test stopping the engine and resetting state.
        """
        self.tractor.start_engine()
        self.tractor.change_gear(3)
        self.tractor.accelerate(20)
        self.tractor.engage_power_takeoff()
        self.tractor.activate_hydraulics()

        self.assertEqual(self.tractor.stop_engine(), "Engine stopped. Tractor is now reset.")
        self.assertFalse(self.tractor.engine_on)
        self.assertEqual(self.tractor.speed, 0)
        self.assertEqual(self.tractor.gear, 0)
        self.assertFalse(self.tractor.power_takeoff)
        self.assertFalse(self.tractor.hydraulics)

        with self.assertRaises(ValueError) as context:
            self.tractor.stop_engine()
        self.assertEqual(str(context.exception), "Engine is already off.")

    def test_change_gear(self):
        """
        Test valid and invalid gear changes.
        """
        self.tractor.start_engine()

        self.assertEqual(self.tractor.change_gear(5), "Gear changed to 5.")
        self.assertEqual(self.tractor.gear, 5)

        with self.assertRaises(ValueError) as context:
            self.tractor.change_gear(11)
        self.assertEqual(str(context.exception), "Gear must be between 0 and 10.")

        with self.assertRaises(ValueError) as context:
            self.tractor.change_gear(-1)
        self.assertEqual(str(context.exception), "Gear must be between 0 and 10.")

        self.tractor.stop_engine()

        with self.assertRaises(ValueError) as context:
            self.tractor.change_gear(2)
        self.assertEqual(
            str(context.exception),
            "Cannot change gears while the engine is off.",
        )

    def test_accelerate(self):
        """
        Test acceleration functionality.
        """
        self.tractor.start_engine()

        self.assertEqual(self.tractor.accelerate(10), "Speed increased to 10 mph.")
        self.assertEqual(self.tractor.speed, 10)

        self.assertEqual(self.tractor.accelerate(35), "Speed increased to 40 mph.")
        self.assertEqual(self.tractor.speed, self.tractor.MAX_SPEED)

        with self.assertRaises(ValueError) as context:
            self.tractor.accelerate(-5)
        self.assertEqual(str(context.exception), "Acceleration must be a positive value.")

        self.tractor.stop_engine()

        with self.assertRaises(ValueError) as context:
            self.tractor.accelerate(10)
        self.assertEqual(
            str(context.exception),
            "Cannot accelerate while the engine is off.",
        )

    def test_brake(self):
        """
        Test braking functionality.
        """
        self.tractor.start_engine()
        self.tractor.accelerate(30)

        self.assertEqual(self.tractor.brake(10), "Speed decreased to 20 mph.")
        self.assertEqual(self.tractor.speed, 20)

        self.assertEqual(self.tractor.brake(25), "Speed decreased to 0 mph.")
        self.assertEqual(self.tractor.speed, 0)

        with self.assertRaises(ValueError) as context:
            self.tractor.brake(-5)
        self.assertEqual(str(context.exception), "Brake reduction must be a positive value.")

        self.tractor.stop_engine()

        with self.assertRaises(ValueError) as context:
            self.tractor.brake(10)
        self.assertEqual(str(context.exception), "Cannot brake while the engine is off.")

    def test_engage_power_takeoff(self):
        """
        Test engaging the PTO.
        """
        self.tractor.start_engine()

        self.assertEqual(
            self.tractor.engage_power_takeoff(),
            "Power Take-Off (PTO) engaged.",
        )
        self.assertTrue(self.tractor.power_takeoff)

        with self.assertRaises(ValueError) as context:
            self.tractor.engage_power_takeoff()
        self.assertEqual(str(context.exception), "PTO is already engaged.")

        self.tractor.stop_engine()

        with self.assertRaises(ValueError) as context:
            self.tractor.engage_power_takeoff()
        self.assertEqual(
            str(context.exception),
            "Cannot engage PTO while the engine is off.",
        )

    def test_disengage_power_takeoff(self):
        """
        Test disengaging the PTO.
        """
        self.tractor.start_engine()
        self.tractor.engage_power_takeoff()

        self.assertEqual(
            self.tractor.disengage_power_takeoff(),
            "Power Take-Off (PTO) disengaged.",
        )
        self.assertFalse(self.tractor.power_takeoff)

        with self.assertRaises(ValueError) as context:
            self.tractor.disengage_power_takeoff()
        self.assertEqual(str(context.exception), "PTO is already disengaged.")

    def test_activate_hydraulics(self):
        """
        Test activating hydraulics.
        """
        self.tractor.start_engine()

        self.assertEqual(self.tractor.activate_hydraulics(), "Hydraulics activated.")
        self.assertTrue(self.tractor.hydraulics)

        with self.assertRaises(ValueError) as context:
            self.tractor.activate_hydraulics()
        self.assertEqual(str(context.exception), "Hydraulics are already activated.")

        self.tractor.stop_engine()

        with self.assertRaises(ValueError) as context:
            self.tractor.activate_hydraulics()
        self.assertEqual(
            str(context.exception),
            "Cannot activate hydraulics while the engine is off.",
        )

    def test_deactivate_hydraulics(self):
        """
        Test deactivating hydraulics.
        """
        self.tractor.start_engine()
        self.tractor.activate_hydraulics()

        self.assertEqual(self.tractor.deactivate_hydraulics(), "Hydraulics deactivated.")
        self.assertFalse(self.tractor.hydraulics)

        with self.assertRaises(ValueError) as context:
            self.tractor.deactivate_hydraulics()
        self.assertEqual(str(context.exception), "Hydraulics are already deactivated.")

    def test_str_representation(self):
        """
        Test the string representation of the tractor.
        """
        expected_str = (
            "Tractor John Deere Model X (2023)\n"
            "Engine: Off\n"
            "Speed: 0 mph\n"
            "Gear: 0\n"
            "PTO: Disengaged\n"
            "Hydraulics: Deactivated\n"
            "GPS: Not Set\n"
            "Auto-Steer: Disabled\n"
            "Field Mode: transport\n"
            "Implement: raised\n"
            "Autonomous: Inactive\n"
            "Manual URL: https://manual.johndeere.com"
        )
        self.assertEqual(str(self.tractor), expected_str)

        self.tractor.start_engine()
        self.tractor.change_gear(3)
        self.tractor.accelerate(15)
        self.tractor.engage_power_takeoff()
        self.tractor.activate_hydraulics()

        expected_str = (
            "Tractor John Deere Model X (2023)\n"
            "Engine: On\n"
            "Speed: 15 mph\n"
            "Gear: 3\n"
            "PTO: Engaged\n"
            "Hydraulics: Activated\n"
            "GPS: Not Set\n"
            "Auto-Steer: Disabled\n"
            "Field Mode: transport\n"
            "Implement: raised\n"
            "Autonomous: Inactive\n"
            "Manual URL: https://manual.johndeere.com"
        )
        self.assertEqual(str(self.tractor), expected_str)


if __name__ == "__main__":
    unittest.main()
