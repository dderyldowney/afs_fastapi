from afs_fastapi.equipment.farm_tractors import FarmTractor


def test_farm_tractor_to_response_defaults():
    tractor = FarmTractor("John Deere", "9RX", 2023)
    resp = tractor.to_response(tractor_id="TR123")
    assert resp.tractor_id == "TR123"
    assert resp.make == "John Deere"
    assert resp.model == "9RX"
    assert resp.year == 2023
    assert resp.manual_url is None
    assert resp.engine_on is False
    assert resp.speed == 0
    assert resp.gear == 0
    assert resp.power_takeoff is False
    assert resp.hydraulics is False
    assert "Tractor John Deere 9RX (2023)" in resp.status


def test_farm_tractor_to_response_after_state_changes():
    tractor = FarmTractor("John Deere", "9RX", 2023, manual_url="https://example.com/manual")
    tractor.start_engine()
    tractor.change_gear(3)
    tractor.accelerate(15)
    tractor.engage_power_takeoff()
    tractor.activate_hydraulics()

    resp = tractor.to_response(tractor_id="TR999")
    assert resp.tractor_id == "TR999"
    assert resp.engine_on is True
    assert resp.speed == 15
    assert resp.gear == 3
    assert resp.power_takeoff is True
    assert resp.hydraulics is True
    assert resp.manual_url == "https://example.com/manual"
    assert "Engine: On" in resp.status
