from fastapi.testclient import TestClient

from afs_fastapi.api.main import app
from tests.utilities.api_testing import MonitoringSystem

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


def test_get_soil_status():
    """Test soil monitoring endpoint with real data instead of mocks."""
    # Use real monitoring system data instead of mocking
    sensor_id = "SOIL001"
    mock_monitoring = MonitoringSystem()
    expected_data = mock_monitoring.get_soil_composition(sensor_id)

    response = client.get(f"/monitoring/soil/{sensor_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["sensor_id"] == sensor_id
    assert "readings" in data

    # Verify the data structure matches expected agricultural monitoring format
    assert "ph" in data["readings"]
    assert "moisture" in data["readings"]
    assert "nitrogen" in data["readings"]

    # Verify values are in realistic agricultural ranges
    assert 5.0 <= data["readings"]["ph"] <= 9.0  # Soil pH range
    assert 0.0 <= data["readings"]["moisture"] <= 100.0  # Percentage
    assert 0.0 <= data["readings"]["nitrogen"] <= 5.0  # Typical agricultural range


def test_get_water_status():
    """Test water monitoring endpoint with real data instead of mocks."""
    # Use real monitoring system data instead of mocking
    sensor_id = "WTR001"
    mock_monitoring = MonitoringSystem()
    expected_data = mock_monitoring.get_water_quality(sensor_id)

    response = client.get(f"/monitoring/water/{sensor_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["sensor_id"] == sensor_id
    assert "readings" in data

    # Verify the data structure matches expected agricultural monitoring format
    assert "ph" in data["readings"]
    assert "turbidity" in data["readings"]
    assert "dissolved_oxygen" in data["readings"]
    assert "temperature" in data["readings"]

    # Verify values are in realistic agricultural water ranges
    assert 6.0 <= data["readings"]["ph"] <= 8.5  # Water pH range
    assert 0.0 <= data["readings"]["turbidity"] <= 10.0  # NTU range
    assert 5.0 <= data["readings"]["dissolved_oxygen"] <= 15.0  # mg/L range
    assert 0.0 <= data["readings"]["temperature"] <= 35.0  # Celsius range
