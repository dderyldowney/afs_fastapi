from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from afs_fastapi.api.main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["name"] == "Automated Farming System API"
    assert "version" in data
    assert "description" in data
    assert "endpoints" in data
    assert "health_check" in data


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "systems" in data
    assert "version" in data
    assert "compliance" in data


def test_api_version():
    response = client.get("/version")
    assert response.status_code == 200
    assert "version" in response.json()


def test_get_tractor_status():
    tractor_id = "TR123"
    response = client.get(f"/equipment/tractor/{tractor_id}")
    assert response.status_code == 200
    data = response.json()
    assert "tractor_id" in data
    assert data["tractor_id"] == tractor_id
    assert "status" in data
    assert "John Deere" in data["status"]


@patch("afs_fastapi.monitoring.soil_monitor.SoilMonitor.get_soil_composition")
def test_get_soil_status(mock_soil_composition: Mock):
    # return numeric readings matching API expectations
    mock_soil_composition.return_value = {"ph": 6.5, "moisture": 75.0, "nitrogen": 1.2}
    sensor_id = "SOIL001"
    response = client.get(f"/monitoring/soil/{sensor_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["sensor_id"] == sensor_id
    assert "readings" in data
    assert data["readings"]["ph"] == 6.5


@patch("afs_fastapi.monitoring.water_monitor.WaterMonitor.get_water_quality")
def test_get_water_status(mock_water_quality: Mock):
    mock_water_quality.return_value = {"ph": 7.0, "turbidity": 0.5, "dissolved_oxygen": 8.0}
    sensor_id = "WTR001"
    response = client.get(f"/monitoring/water/{sensor_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["sensor_id"] == sensor_id
    assert "readings" in data
    assert data["readings"]["ph"] == 7.0
