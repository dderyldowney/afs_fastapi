import pytest

from afs_fastapi.stations.station_types import MasterStation, StationType, get_station_type


def test_station_type_enum():
    assert StationType.MASTER.value == "master"
    assert StationType.DIAGNOSTIC.value == "diagnostic"
    assert StationType.SERVICE_DISPATCH.value == "service_dispatch"


def test_get_station_type_valid():
    assert get_station_type("master") == StationType.MASTER
    assert get_station_type("diagnostic") == StationType.DIAGNOSTIC
    assert get_station_type("service_dispatch") == StationType.SERVICE_DISPATCH


def test_get_station_type_invalid():
    with pytest.raises(ValueError) as exc_info:
        get_station_type("invalid")
    assert "Invalid station type" in str(exc_info.value)


def test_get_station_type_case_insensitive():
    assert get_station_type("Master") == StationType.MASTER
    assert get_station_type("Diagnostic") == StationType.DIAGNOSTIC


def test_command_station_initialization():
    station = MasterStation(1, "Irrigation")
    assert station.station_id == 1
    assert station.system == "Irrigation"


def test_command_station_activate():
    station = MasterStation(1, "Irrigation")
    result = station.activate()
    assert result == "Master station 1 for Irrigation system is activated."


def test_command_station_deactivate():
    station = MasterStation(1, "Irrigation")
    result = station.deactivate()
    assert result == "Master station 1 for Irrigation system is deactivated."
