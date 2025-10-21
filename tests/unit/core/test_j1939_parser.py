from afs_fastapi.core.j1939_parser import parse_j1939_message


def test_parse_pgn_61444_valid():
    """Tests parsing of a valid PGN 61444 message."""
    # Construct a data payload with known values
    data = [
        0,  # Not used
        int((50 - (-125)) / 1),  # SPN 512: Driver's Demand Engine - Percent Torque (50%)
        int((75 - (-125)) / 1),  # SPN 513: Actual Engine - Percent Torque (75%)
        int(2000 / 0.125) & 0xFF,  # SPN 190: Engine Speed (2000 rpm)
        int(2000 / 0.125) >> 8,
        1,  # SPN 1483: Source Address
        1,  # SPN 1675: Engine Starter Mode (Cranking)
        int((80 - (-125)) / 1),  # SPN 2432: Engine Demand - Percent Torque (80%)
    ]
    parsed_data = parse_j1939_message(61444, data)
    assert parsed_data is not None
    assert parsed_data["Driver's Demand Engine - Percent Torque"] == 50
    assert parsed_data["Actual Engine - Percent Torque"] == 75
    assert parsed_data["Engine Speed"] == 2000
    assert parsed_data["Source Address of Controlling Device for Engine Control"] == 1
    assert parsed_data["Engine Starter Mode"] == 1
    assert parsed_data["Engine Demand - Percent Torque"] == 80


def test_parse_pgn_61444_invalid_range():
    """Tests that an out-of-range value in PGN 61444 returns None."""
    # Construct a data payload with an out-of-range value for Engine Speed
    data = [
        0,  # Not used
        0,  # Not used
        int((50 + 125) / 1),  # SPN 512: Driver's Demand Engine - Percent Torque (50%)
        int((75 + 125) / 1),  # SPN 513: Actual Engine - Percent Torque (75%)
        int(8192 / 0.125) & 0xFF,  # SPN 190: Engine Speed (8192 rpm - out of range)
        int(8192 / 0.125) >> 8,
        1,  # SPN 1483: Source Address
        1,  # SPN 1675: Engine Starter Mode (Cranking)
        int((80 + 125) / 1),  # SPN 2432: Engine Demand - Percent Torque (80%)
    ]
    parsed_data = parse_j1939_message(61444, data)
    assert parsed_data is None


def test_parse_unsupported_pgn():
    """Tests that an unsupported PGN returns None."""
    data = [0] * 8
    parsed_data = parse_j1939_message(99999, data)
    assert parsed_data is None
