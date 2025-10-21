import pytest
from afs_fastapi.core.can_parser import CanParser


@pytest.fixture
def can_parser():
    return CanParser()


def test_parse_engine_speed_valid(can_parser):
    """Tests parsing of a valid Engine Speed message (PGN 61444, SPN 190)."""
    message = {"pgn": 61444, "spn": 190, "value": 2000, "data_type": "rpm"}
    parsed_data = can_parser.parse_message(message)
    assert parsed_data is not None
    assert parsed_data["parsed_data"]["engine_speed"] == 2000


def test_parse_engine_speed_lower_bound(can_parser):
    """Tests parsing of Engine Speed at the lower bound of the valid range."""
    message = {"pgn": 61444, "spn": 190, "value": 0, "data_type": "rpm"}
    parsed_data = can_parser.parse_message(message)
    assert parsed_data is not None
    assert parsed_data["parsed_data"]["engine_speed"] == 0


def test_parse_engine_speed_upper_bound(can_parser):
    """Tests parsing of Engine Speed at the upper bound of the valid range."""
    message = {"pgn": 61444, "spn": 190, "value": 8191.875, "data_type": "rpm"}
    parsed_data = can_parser.parse_message(message)
    assert parsed_data is not None
    assert parsed_data["parsed_data"]["engine_speed"] == 8191.875


def test_parse_engine_speed_out_of_range(can_parser):
    """Tests that an out-of-range Engine Speed value returns None."""
    message = {"pgn": 61444, "spn": 190, "value": 8192, "data_type": "rpm"}
    parsed_data = can_parser.parse_message(message)
    assert parsed_data is None


def test_parse_engine_speed_negative(can_parser):
    """Tests that a negative Engine Speed value returns None."""
    message = {"pgn": 61444, "spn": 190, "value": -1, "data_type": "rpm"}
    parsed_data = can_parser.parse_message(message)
    assert parsed_data is None
