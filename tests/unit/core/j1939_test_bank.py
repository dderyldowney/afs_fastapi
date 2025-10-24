from typing import NamedTuple


class TestCase(NamedTuple):
    data: list[int]
    expected_values: dict[str, float | int]


TEST_BANK: dict[int, list[TestCase]] = {
    61444: [
        TestCase(
            data=[
                0,  # Not used
                int((50 - (-125)) / 1),  # SPN 512: Driver's Demand Engine - Percent Torque (50%)
                int((75 - (-125)) / 1),  # SPN 513: Actual Engine - Percent Torque (75%)
                int(2000 / 0.125) & 0xFF,  # SPN 190: Engine Speed (2000 rpm)
                int(2000 / 0.125) >> 8,
                1,  # SPN 1483: Source Address
                1,  # SPN 1675: Engine Starter Mode (Cranking)
                int((80 - (-125)) / 1),  # SPN 2432: Engine Demand - Percent Torque (80%)
            ],
            expected_values={
                "Driver's Demand Engine - Percent Torque": 50,
                "Actual Engine - Percent Torque": 75,
                "Engine Speed": 2000,
                "Source Address of Controlling Device for Engine Control": 1,
                "Engine Starter Mode": 1,
                "Engine Demand - Percent Torque": 80,
            },
        ),
    ],
    65265: [
        TestCase(
            data=[
                0,  # Not used
                int(100 / (1 / 256)) & 0xFF,  # SPN 84: Wheel-Based Vehicle Speed (100 km/h)
                int(100 / (1 / 256)) >> 8,
                0,
                0,
                0,
                0,
                0,  # Not used
            ],
            expected_values={
                "Wheel-Based Vehicle Speed": 100,
            },
        ),
    ],
}
