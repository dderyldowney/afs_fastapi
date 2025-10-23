from typing import NamedTuple


class SPNSpec(NamedTuple):
    spn: int
    name: str
    byte_offset: int
    length: int
    scale: float
    offset: float
    min_value: float
    max_value: float


PGN_61444_SPNS: list[SPNSpec] = [
    SPNSpec(
        spn=512,
        name="Driver's Demand Engine - Percent Torque",
        byte_offset=1,
        length=1,
        scale=1,
        offset=-125,
        min_value=-125,
        max_value=125,
    ),
    SPNSpec(
        spn=513,
        name="Actual Engine - Percent Torque",
        byte_offset=2,
        length=1,
        scale=1,
        offset=-125,
        min_value=0,
        max_value=125,
    ),
    SPNSpec(
        spn=190,
        name="Engine Speed",
        byte_offset=3,
        length=2,
        scale=0.125,
        offset=0,
        min_value=0,
        max_value=8031.875,
    ),
    # Note: The following SPNs are not officially part of PGN 61444 in all J1939 standards.
    # The byte offsets are assumed.
    SPNSpec(
        spn=1483,
        name="Source Address of Controlling Device for Engine Control",
        byte_offset=5,
        length=1,
        scale=1,
        offset=0,
        min_value=0,
        max_value=254,
    ),
    SPNSpec(
        spn=1675,
        name="Engine Starter Mode",
        byte_offset=6,
        length=1,
        scale=1,
        offset=0,
        min_value=0,
        max_value=2,  # Assuming states: 0: Off, 1: Cranking, 2: Start inhibited
    ),
    SPNSpec(
        spn=2432,
        name="Engine Demand - Percent Torque",
        byte_offset=7,
        length=1,
        scale=1,
        offset=-125,
        min_value=0,
        max_value=100,
    ),
]

PGN_SPECS: dict[int, list[SPNSpec]] = {
    61444: PGN_61444_SPNS,
    65265: [
        SPNSpec(
            spn=84,
            name="Wheel-Based Vehicle Speed",
            byte_offset=1,
            length=2,
            scale=1 / 256,
            offset=0,
            min_value=0,
            max_value=250.996,
        ),
    ],
    65267: [
        SPNSpec(
            spn=584,
            name="Latitude",
            byte_offset=0,
            length=4,
            scale=1e-7,
            offset=0,
            min_value=-180,
            max_value=180,
        ),
        SPNSpec(
            spn=585,
            name="Longitude",
            byte_offset=4,
            length=4,
            scale=1e-7,
            offset=0,
            min_value=-180,
            max_value=180,
        ),
    ],
    65276: [
        SPNSpec(
            spn=96,
            name="Fuel Level",
            byte_offset=1,
            length=1,
            scale=0.4,
            offset=0,
            min_value=0,
            max_value=100,
        ),
    ],
}
