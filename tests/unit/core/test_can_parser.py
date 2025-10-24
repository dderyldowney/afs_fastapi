import pytest

from afs_fastapi.core.can_parser import CanParser


@pytest.fixture
def can_parser():
    return CanParser()


def test_can_parser_valid_pgn(can_parser):
    """Tests that the CanParser correctly parses a valid PGN."""
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
    parsed_data = can_parser.parse_message(61444, data)
    assert parsed_data is not None
    assert parsed_data["pgn"] == 61444
    assert parsed_data["parsed_data"]["Driver's Demand Engine - Percent Torque"] == 50


def test_can_parser_invalid_pgn(can_parser):
    """Tests that the CanParser returns None for an invalid PGN."""
    data = [0] * 8
    parsed_data = can_parser.parse_message(99999, data)
    assert parsed_data is None
