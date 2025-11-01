"""
Test suite for the modernized AFS FastAPI API with comprehensive error handling.

This test suite validates the new API endpoints, error handling, validation,
and compliance features for agricultural robotics operations.
"""

from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from afs_fastapi.api.core.error_handling import ErrorCode
from afs_fastapi.api.main import app

client = TestClient(app)


class TestErrorHandling:
    """Test comprehensive error handling for all API endpoints."""

    def test_validation_error_response_format(self):
        """Test that validation errors return proper error response format."""
        # Test equipment control with invalid equipment ID
        response = client.post(
            "/api/v1/equipment/control",
            json={"equipment_id": "INVALID", "operation": "start_engine"},  # Invalid format
        )

        assert response.status_code == 422
        error_data = response.json()
        assert error_data["success"] is False
        assert "error" in error_data
        assert error_data["error"]["code"] == ErrorCode.VALIDATION_ERROR
        assert "recovery_suggestions" in error_data["error"]
        assert "request_id" in error_data
        assert "timestamp" in error_data

    def test_not_found_error_format(self):
        """Test that 404 errors return proper error response format."""
        response = client.get("/api/v1/equipment/status/INVALID-001")

        assert response.status_code == 404
        error_data = response.json()
        assert error_data["success"] is False
        assert "error" in error_data
        assert error_data["error"]["code"] == ErrorCode.RESOURCE_NOT_FOUND

    def test_internal_server_error_format(self):
        """Test that 500 errors return proper error response format."""
        # Mock a failure in AI processing
        with patch("afs_fastapi.api.endpoints.ai_processing.ai_processing_manager") as mock_manager:
            mock_manager.process_agricultural_request.side_effect = Exception("Service unavailable")

            response = client.post(
                "/api/v1/ai/process", json={"user_input": "test input", "service_name": "test"}
            )

            assert response.status_code == 500
            error_data = response.json()
            assert error_data["success"] is False
            assert "error" in error_data
            assert error_data["error"]["code"] == ErrorCode.INTERNAL_SERVER_ERROR


class TestEquipmentAPI:
    """Test modernized equipment API endpoints."""

    def test_get_equipment_status_success(self):
        """Test successful equipment status retrieval."""
        response = client.get("/api/v1/equipment/status/TRC-001")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["equipment_id"] == "TRC-001"
        assert data["data"]["equipment_type"] == "tractor"
        assert "metrics" in data["data"]
        assert "timestamp" in data

    def test_equipment_control_success(self):
        """Test successful equipment control command."""
        response = client.post(
            "/api/v1/equipment/control",
            json={
                "equipment_id": "TRC-001",
                "operation": "start_engine",
                "parameters": {},
                "priority": "normal",
                "safety_override": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["operation"] == "start_engine"
        assert data["data"]["equipment_id"] == "TRC-001"

    def test_equipment_control_invalid_operation(self):
        """Test equipment control with invalid operation."""
        response = client.post(
            "/api/v1/equipment/control",
            json={"equipment_id": "TRC-001", "operation": "invalid_operation"},
        )

        assert response.status_code == 422
        error_data = response.json()
        assert error_data["success"] is False

    def test_equipment_list_pagination(self):
        """Test equipment list with pagination."""
        response = client.get("/api/v1/equipment/list?page=1&page_size=5")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "pagination" in data
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 5

    def test_equipment_types_endpoint(self):
        """Test equipment types endpoint."""
        response = client.get("/api/v1/equipment/types")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "tractor" in data["data"]
        assert "capabilities" in data["data"]["tractor"]


class TestMonitoringAPI:
    """Test modernized monitoring API endpoints."""

    def test_submit_soil_reading_success(self):
        """Test successful soil reading submission."""
        soil_data = {
            "sensor_id": "SOI-001",
            "location": {"latitude": 40.7128, "longitude": -74.0060},
            "readings": {"moisture_percent": 34.2, "ph": 6.8, "temperature_celsius": 22.1},
            "timestamp": "2024-01-01T12:00:00Z",
        }

        response = client.post("/api/v1/monitoring/soil/readings", json=soil_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["sensor_id"] == "SOI-001"
        assert "agricultural_metrics" in data["data"]
        assert "irrigation_recommendation" in data["data"]["agricultural_metrics"]

    def test_soil_reading_validation_errors(self):
        """Test soil reading validation."""
        # Invalid moisture percentage
        invalid_data = {
            "sensor_id": "SOI-001",
            "location": {"latitude": 40.7128, "longitude": -74.0060},
            "readings": {
                "moisture_percent": 150,  # Invalid: >100%
                "ph": 6.8,
                "temperature_celsius": 22.1,
            },
        }

        response = client.post("/api/v1/monitoring/soil/readings", json=invalid_data)

        assert response.status_code == 422
        error_data = response.json()
        assert error_data["success"] is False

    def test_get_soil_readings_filtering(self):
        """Test soil readings with filtering."""
        response = client.get(
            "/api/v1/monitoring/soil/readings?sensor_id=SOI-001&page=1&page_size=10"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "pagination" in data

    def test_submit_water_reading_success(self):
        """Test successful water quality reading submission."""
        water_data = {
            "sensor_id": "WAT-001",
            "location": {"latitude": 40.7128, "longitude": -74.0060},
            "readings": {
                "ph": 7.2,
                "turbidity_ntu": 12.5,
                "temperature_celsius": 18.7,
                "dissolved_oxygen_ppm": 8.4,
            },
        }

        response = client.post("/api/v1/monitoring/water/readings", json=water_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["sensor_id"] == "WAT-001"

    def test_sensor_status_endpoint(self):
        """Test sensor network status endpoint."""
        response = client.get("/api/v1/monitoring/sensor-status")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "sensor_network" in data["data"]
        assert "summary" in data["data"]


class TestAIProcessingAPI:
    """Test modernized AI processing API endpoints."""

    def test_process_with_ai_optimization_success(self):
        """Test successful AI processing."""
        request_data = {
            "user_input": "Coordinate tractor fleet for field cultivation with safety protocols",
            "service_name": "platform",
            "optimization_level": "standard",
            "target_format": "standard",
            "context_data": {
                "equipment_id": "TRC-001",
                "field_id": "FIELD-001",
                "operation_type": "cultivation",
            },
        }

        response = client.post("/api/v1/ai/process", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "input_text" in data
        assert "processed_output" in data
        assert "optimization_applied" in data
        assert "agricultural_compliance" in data

    def test_equipment_communication_optimization(self):
        """Test equipment communication optimization."""
        request_data = {
            "user_input": "ISOBUS: Emergency stop initiated for tractor TRC001",
            "equipment_id": "TRC001",
            "priority": "critical",
        }

        response = client.post("/api/v1/ai/equipment/optimize", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "optimization_level" in data
        assert data["optimization_level"] == "conservative"

    def test_fleet_coordination_optimization(self):
        """Test fleet coordination optimization."""
        request_data = {
            "fleet_id": "FLT-001",
            "operation_type": "planting",
            "tractor_ids": ["TRC-001", "TRC-002", "TRC-003"],
            "coordination_parameters": {"speed": 6.0, "spacing": 30.0},
        }

        response = client.post("/api/v1/ai/fleet/optimize", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "optimization_level" in data

    def test_ai_statistics_endpoint(self):
        """Test AI processing statistics endpoint."""
        response = client.get("/api/v1/ai/statistics")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "global_stats" in data["data"]
        assert "service_stats" in data["data"]

    def test_ai_health_check_endpoint(self):
        """Test AI processing health check endpoint."""
        response = client.get("/api/v1/ai/health")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "status" in data["data"]
        assert "pipeline_operational" in data["data"]

    def test_optimization_levels_endpoint(self):
        """Test available optimization levels endpoint."""
        response = client.get("/api/v1/ai/optimization-levels")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "conservative" in data["data"]
        assert "standard" in data["data"]
        assert "aggressive" in data["data"]
        assert "adaptive" in data["data"]


class TestAPIStandards:
    """Test API compliance and standards."""

    def test_error_response_consistency(self):
        """Test that all error responses follow the same format."""
        from unittest.mock import patch

        endpoints_to_test = [
            ("/api/v1/equipment/status/INVALID", 404),
            ("/api/v1/equipment/control", 422, {"invalid_data": "test"}),
            ("/api/v1/monitoring/soil/readings", 422, {"invalid_data": "test"}),
        ]

        # Test regular error responses
        for endpoint in endpoints_to_test:
            if len(endpoint) == 2:
                path, expected_status = endpoint
                response = client.get(path)
            elif len(endpoint) == 3:
                path, expected_status, test_data = endpoint
                response = client.post(path, json=test_data)

            assert response.status_code == expected_status
            data = response.json()

            # All error responses should have these fields
            assert "success" in data
            assert "error" in data
            assert "request_id" in data
            assert "timestamp" in data

        # Test 500 error separately with mock
        with patch("afs_fastapi.api.endpoints.ai_processing.ai_processing_manager") as mock_manager:
            mock_manager.process_agricultural_request.side_effect = Exception("Service unavailable")

            response = client.post(
                "/api/v1/ai/process", json={"user_input": "test input", "service_name": "test"}
            )

            assert response.status_code == 500
            data = response.json()
            assert "success" in data
            assert "error" in data
            assert "request_id" in data
            assert "timestamp" in data


class TestAgriculturalValidation:
    """Test agricultural-specific validation features."""

    def test_equipment_id_format_validation(self):
        """Test equipment ID format validation."""
        invalid_ids = ["INVALID", "TRC1", "ABC123", "T1", "TOOLONGID-12345", "AB-12", "TOO-1234"]

        for invalid_id in invalid_ids:
            response = client.post(
                "/api/v1/equipment/control",
                json={"equipment_id": invalid_id, "operation": "start_engine"},
            )
            assert response.status_code == 422

    def test_gps_coordinates_validation(self):
        """Test GPS coordinates validation for agricultural locations."""
        invalid_locations = [
            {"latitude": 91, "longitude": -74},  # Invalid latitude
            {"latitude": -91, "longitude": -74},  # Invalid latitude
            {"latitude": 40, "longitude": 181},  # Invalid longitude
            {"latitude": 40, "longitude": -181},  # Invalid longitude
        ]

        for location in invalid_locations:
            response = client.post(
                "/api/v1/monitoring/soil/readings",
                json={
                    "sensor_id": "SOI-001",
                    "location": location,
                    "readings": {"moisture_percent": 34.2},
                },
            )
            assert response.status_code == 422

    def test_agricultural_context_validation(self):
        """Test agricultural context data validation."""
        # Test with invalid operation type
        invalid_context = {
            "user_input": "test",
            "context_data": {"operation_type": "invalid_operation"},
        }

        response = client.post("/api/v1/ai/process", json=invalid_context)
        assert response.status_code == 422

    def test_safety_override_validation(self):
        """Test safety override validation."""
        # Test safety override with non-emergency operation
        request_data = {"user_input": "test", "safety_override": True}

        response = client.post("/api/v1/ai/process", json=request_data)
        assert response.status_code == 422

    def test_iso_compliance_error_codes(self):
        """Test that ISO compliance violations have appropriate error codes."""
        # Test with soil data that would violate agricultural standards
        violation_data = {
            "sensor_id": "SOI-001",
            "location": {"latitude": 40.7128, "longitude": -74.0060},
            "readings": {
                "moisture_percent": 5.0,  # Very low moisture
                "ph": 9.5,  # High pH (alkaline)
                "temperature_celsius": -10.0,  # Below freezing
            },
        }

        response = client.post("/api/v1/monitoring/soil/readings", json=violation_data)

        # Should reject data with proper agricultural compliance error
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == ErrorCode.VALIDATION_ERROR
        assert (
            "agricultural" in data["error"]["message"].lower()
            or "soil" in data["error"]["message"].lower()
        )


class TestAPIPerformance:
    """Test API performance and response times."""

    def test_response_time_standards(self):
        """Test that API responses meet performance standards."""
        endpoints = [
            "/api/v1/equipment/status/TRC-001",
            "/api/v1/monitoring/soil/readings",
            "/api/v1/ai/process",
            "/api/v1/ai/statistics",
        ]

        for endpoint in endpoints:
            start_time = datetime.now()
            response = client.post(endpoint) if "ai/process" in endpoint else client.get(endpoint)
            end_time = datetime.now()

            response_time = (
                end_time - start_time
            ).total_seconds() * 1000  # Convert to milliseconds

            assert response.status_code in [200, 422]  # Allow validation errors
            assert response_time < 1000  # Response should be under 1 second


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
