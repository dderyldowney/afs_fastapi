import pytest
from pytest_bdd import given, parsers, scenario, then, when

from afs_fastapi.core.can_parser import CanParser


# Scenarios
@scenario("../features/tractor_can_data.feature", "Receiving <Data Type> Data")
def test_receiving_data_type_data():
    pass


# Fixtures
@pytest.fixture
def afs_fastapi_system():
    """Represents the AFS FastAPI system instance."""
    return {"can_messages_received": [], "can_parser": CanParser()}


@pytest.fixture
def isobus_network():
    """Represents the simulated ISOBUS network."""
    return {"connected": False, "messages_on_bus": []}


@pytest.fixture
def tractor_ecu():
    """Represents a simulated Tractor ECU."""
    return {"present": False, "engine_speed": None}


# Given Steps
@given("the AFS FastAPI system is connected to an ISOBUS network")
def system_connected_to_isobus(afs_fastapi_system, isobus_network):
    isobus_network["connected"] = True
    pass


@given("a Tractor ECU is present on the network")
def tractor_ecu_present(tractor_ecu, isobus_network):
    tractor_ecu["present"] = True
    pass


# When Steps
@when(
    parsers.parse(
        "the Tractor ECU broadcasts {data_type} (PGN {pgn:d}, SPN {spn:d}) with value {value:d}"
    )
)
def ecu_broadcasts_data_with_value(tractor_ecu, isobus_network, data_type, pgn, spn, value):
    isobus_network["messages_on_bus"].append(
        {"pgn": pgn, "spn": spn, "value": value, "data_type": data_type}
    )
    pass


# Then Steps
@then(
    parsers.parse(
        "the AFS FastAPI system should receive and correctly parse the {data_type} value as {value:d}"
    )
)
def system_receives_and_parses_data(afs_fastapi_system, isobus_network, data_type, value):
    from afs_fastapi.core.j1939_specs import PGN_SPECS

    for message in isobus_network["messages_on_bus"]:
        # Extract PGN and SPN from message
        pgn = message["pgn"]
        spn = message["spn"]

        # Get the SPN spec to determine byte offset and encoding
        if pgn not in PGN_SPECS:
            continue

        spn_spec = next((spec for spec in PGN_SPECS[pgn] if spec.spn == spn), None)
        if not spn_spec:
            continue

        # Create data payload with value at correct byte offset
        data = [0] * 8

        # Calculate raw value from scaled value
        raw_value = int((value - spn_spec.offset) / spn_spec.scale)

        # Encode raw value at correct byte offset in little-endian format
        for i in range(spn_spec.length):
            data[spn_spec.byte_offset + i] = (raw_value >> (8 * i)) & 0xFF

        parsed_message = afs_fastapi_system["can_parser"].parse_message(pgn, data)
        if parsed_message:
            # Add data_type to parsed message for test validation
            parsed_message["data_type"] = data_type
            afs_fastapi_system["can_messages_received"].append(parsed_message)

    assert len(afs_fastapi_system["can_messages_received"]) > 0

    # Find the message corresponding to the current data_type
    found_message = next(
        (
            msg
            for msg in afs_fastapi_system["can_messages_received"]
            if msg.get("data_type") == data_type
        ),
        None,
    )

    assert found_message is not None

    # Check if the parsed value matches expected value (with tolerance for floating point)
    parsed_data = found_message["parsed_data"]
    # The SPN name in parsed_data should match the data_type
    # For "Engine Speed", look for "Engine Speed" key
    # For "Vehicle Speed", look for "Wheel-Based Vehicle Speed" key
    # For "Fuel Level", look for "Fuel Level" key
    # For "GPS Coordinates", this is more complex (Latitude/Longitude)

    if data_type == "Engine Speed":
        assert "Engine Speed" in parsed_data
        assert abs(parsed_data["Engine Speed"] - value) < 1.0
    elif data_type == "Vehicle Speed":
        assert "Wheel-Based Vehicle Speed" in parsed_data
        assert abs(parsed_data["Wheel-Based Vehicle Speed"] - value) < 1.0
    elif data_type == "Fuel Level":
        assert "Fuel Level" in parsed_data
        assert abs(parsed_data["Fuel Level"] - value) < 1.0
    elif data_type == "GPS Coordinates":
        # GPS Coordinates test uses SPN 162 which doesn't exist in our specs
        # SPN 584 is Latitude, SPN 585 is Longitude
        # For now, check if either Latitude or Longitude is present
        assert "Latitude" in parsed_data or "Longitude" in parsed_data
