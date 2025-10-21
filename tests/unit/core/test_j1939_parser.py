import pytest

from afs_fastapi.core.j1939_parser import parse_j1939_message
from tests.unit.core.j1939_test_bank import TEST_BANK


@pytest.mark.parametrize(
    "pgn, data, expected_values",
    [
        (pgn, test_case.data, test_case.expected_values)
        for pgn, test_cases in TEST_BANK.items()
        for test_case in test_cases
    ],
)
def test_j1939_parser(pgn, data, expected_values):
    """Tests the J1939 parser with a test bank of PGNs and data."""
    parsed_data = parse_j1939_message(pgn, data)
    assert parsed_data is not None
    for key, value in expected_values.items():
        assert key in parsed_data
        assert parsed_data[key] == value
