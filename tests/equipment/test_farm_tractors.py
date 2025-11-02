import pytest

from afs_fastapi.equipment.farm_tractors import FarmTractor


def test_init_with_manual():
    tractor = FarmTractor("John", "Deere", 2020, "http://manual.pdf")
    assert tractor.manual_url == "http://manual.pdf"


def test_init_without_manual():
    tractor = FarmTractor("John", "Deere", 2020)
    assert tractor.manual_url is None


def test_str_representation():
    tractor = FarmTractor("John", "Deere", 2020, "http://manual.pdf")
    str_rep = str(tractor)
    assert "John Deere (2020)" in str_rep
    assert "Engine: Off" in str_rep
    assert "Speed: 0 mph" in str_rep
    assert "Gear: 0" in str_rep
    assert "PTO: Disengaged" in str_rep
    assert "Hydraulics: Deactivated" in str_rep
    assert "Manual URL: http://manual.pdf" in str_rep


def test_str_representation_no_manual():
    tractor = FarmTractor("John", "Deere", 2020)
    str_rep = str(tractor)
    assert "Manual URL: No manual available" in str_rep


def test_acceleration_edge_cases():
    tractor = FarmTractor("John", "Deere", 2020)
    tractor.start_engine()

    # Test max speed limit
    tractor.accelerate(50)  # Should cap at MAX_SPEED (40)
    assert tractor.speed == 40

    with pytest.raises(ValueError, match="Acceleration must be a positive value"):
        tractor.accelerate(-1)


def test_brake_edge_cases():
    tractor = FarmTractor("John", "Deere", 2020)
    tractor.start_engine()
    tractor.accelerate(30)

    # Test minimum speed limit
    tractor.brake(50)  # Should stop at 0
    assert tractor.speed == 0

    with pytest.raises(ValueError, match="Brake reduction must be a positive value"):
        tractor.brake(-1)


def test_gear_edge_cases():
    tractor = FarmTractor("John", "Deere", 2020)
    tractor.start_engine()

    # Test string input
    assert "Gear changed to 5" in tractor.change_gear("5")

    # Test invalid string
    with pytest.raises(ValueError, match="Invalid gear value"):
        tractor.change_gear("invalid")

    # Test out of range values
    with pytest.raises(ValueError, match="Gear must be between 0 and 10"):
        tractor.change_gear(11)
    with pytest.raises(ValueError, match="Gear must be between 0 and 10"):
        tractor.change_gear(-1)


def test_pto_edge_cases():
    tractor = FarmTractor("John", "Deere", 2020)

    # Test PTO with engine off
    with pytest.raises(ValueError, match="Cannot engage PTO while the engine is off"):
        tractor.engage_power_takeoff()

    tractor.start_engine()
    tractor.engage_power_takeoff()

    # Test double engage
    with pytest.raises(ValueError, match="PTO is already engaged"):
        tractor.engage_power_takeoff()

    tractor.disengage_power_takeoff()

    # Test double disengage
    with pytest.raises(ValueError, match="PTO is already disengaged"):
        tractor.disengage_power_takeoff()


def test_hydraulics_edge_cases():
    tractor = FarmTractor("John", "Deere", 2020)

    # Test hydraulics with engine off
    with pytest.raises(ValueError, match="Cannot activate hydraulics while the engine is off"):
        tractor.activate_hydraulics()

    tractor.start_engine()
    tractor.activate_hydraulics()

    # Test double activate
    with pytest.raises(ValueError, match="Hydraulics are already activated"):
        tractor.activate_hydraulics()

    tractor.deactivate_hydraulics()

    # Test double deactivate
    with pytest.raises(ValueError, match="Hydraulics are already deactivated"):
        tractor.deactivate_hydraulics()


def test_stop_engine_resets_state():
    tractor = FarmTractor("John", "Deere", 2020)
    tractor.start_engine()
    tractor.accelerate(20)
    tractor.change_gear(5)
    tractor.engage_power_takeoff()
    tractor.activate_hydraulics()

    tractor.stop_engine()

    assert tractor.speed == 0
    assert tractor.gear == 0
    assert not tractor.power_takeoff
    assert not tractor.hydraulics
