"""
Real API testing utilities without mocks.

This module provides utilities for testing FastAPI endpoints using real
HTTP clients and real monitoring systems, eliminating the need for mocks in API testing.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import contextmanager
from typing import Any

from fastapi.testclient import TestClient

from afs_fastapi.api.main import app

logger = logging.getLogger(__name__)


class MonitoringSystem:
    """Test monitoring system providing realistic agricultural sensor data.

    This provides realistic sensor data for testing agricultural monitoring
    endpoints without mocking the entire system.
    """

    @staticmethod
    def get_soil_composition(sensor_id: str) -> dict[str, Any]:
        """Get realistic soil composition data.

        Parameters
        ----------
        sensor_id : str
            Soil sensor identifier

        Returns
        -------
        Dict[str, Any]
            Realistic soil composition data
        """
        # Simulate realistic agricultural soil data based on sensor ID
        sensor_data = {
            "SOIL001": {"ph": 6.5, "moisture": 75.0, "nitrogen": 1.2, "organic_matter": 3.5},
            "SOIL002": {"ph": 6.8, "moisture": 72.0, "nitrogen": 1.4, "organic_matter": 3.8},
            "SOIL003": {"ph": 6.2, "moisture": 78.0, "nitrogen": 1.1, "organic_matter": 3.2},
        }

        # Return default if sensor not found
        return sensor_data.get(
            sensor_id, {"ph": 6.5, "moisture": 75.0, "nitrogen": 1.2, "organic_matter": 3.5}
        )

    @staticmethod
    def get_water_quality(sensor_id: str) -> dict[str, Any]:
        """Get realistic water quality data.

        Parameters
        ----------
        sensor_id : str
            Water sensor identifier

        Returns
        -------
        Dict[str, Any]
            Realistic water quality data
        """
        # Simulate realistic agricultural water data
        sensor_data = {
            "WTR001": {"ph": 7.0, "turbidity": 0.5, "dissolved_oxygen": 8.0, "temperature": 18.5},
            "WTR002": {"ph": 7.2, "turbidity": 0.3, "dissolved_oxygen": 8.5, "temperature": 19.0},
            "WTR003": {"ph": 6.8, "turbidity": 0.7, "dissolved_oxygen": 7.5, "temperature": 18.0},
        }

        return sensor_data.get(
            sensor_id, {"ph": 7.0, "turbidity": 0.5, "dissolved_oxygen": 8.0, "temperature": 18.5}
        )

    @staticmethod
    def get_weather_data(location: str) -> dict[str, Any]:
        """Get realistic weather data.

        Parameters
        ----------
        location : str
            Location identifier

        Returns
        -------
        Dict[str, Any]
            Realistic weather data
        """
        # Simulate realistic agricultural weather data
        weather_data = {
            "FIELD_01": {
                "temperature": 22.5,
                "humidity": 65.0,
                "wind_speed": 12.3,
                "rainfall": 0.0,
                "pressure": 1013.2,
                "uv_index": 6.0,
            },
            "FIELD_02": {
                "temperature": 21.8,
                "humidity": 68.0,
                "wind_speed": 8.7,
                "rainfall": 0.0,
                "pressure": 1015.1,
                "uv_index": 4.0,
            },
        }

        return weather_data.get(
            location,
            {
                "temperature": 22.5,
                "humidity": 65.0,
                "wind_speed": 12.3,
                "rainfall": 0.0,
                "pressure": 1013.2,
                "uv_index": 6.0,
            },
        )


class APITester:
    """API tester using FastAPI TestClient.

    This provides comprehensive API testing capabilities for HTTP communication
    and data validation.
    """

    def __init__(self, app_instance: Any = None) -> None:
        """Initialize API tester.

        Parameters
        ----------
        app_instance : Any, optional
            FastAPI app instance. If None, uses default app.
        """
        self.app = app_instance or app
        self.client = TestClient(self.app)
        self.monitoring = MonitoringSystem()

    @contextmanager
    def client_context(self):
        """Context manager for API client operations."""
        yield self.client

    def test_endpoint(
        self,
        method: str,
        path: str,
        data: Any = None,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        expected_status: int = 200,
        expected_keys: list[str] | None = None,
    ) -> dict[str, Any]:
        """Test an API endpoint with real HTTP calls.

        parameters
        ----------
        method : str
            HTTP method (GET, POST, PUT, DELETE, etc.)
        path : str
            API endpoint path
        data : Any, optional
            Request data (for form data)
        json_data : Dict[str, Any], optional
            JSON request data
        params : Dict[str, Any], optional
            Query parameters
        headers : Dict[str, str], optional
            Request headers
        expected_status : int, default 200
            Expected HTTP status code
        expected_keys : List[str], optional
            Expected JSON keys in response

        Returns
        -------
        Dict[str, Any]
            Response data
        """
        try:
            # Make the HTTP request
            if method.upper() == "GET":
                response = self.client.get(path, params=params, headers=headers)
            elif method.upper() == "POST":
                response = self.client.post(
                    path, data=data, json=json_data, params=params, headers=headers
                )
            elif method.upper() == "PUT":
                response = self.client.put(
                    path, data=data, json=json_data, params=params, headers=headers
                )
            elif method.upper() == "DELETE":
                response = self.client.delete(path, params=params, headers=headers)
            else:
                response = self.client.request(
                    method, path, data=data, json=json_data, params=params, headers=headers
                )

            # Check status code
            if response.status_code != expected_status:
                raise AssertionError(
                    f"Expected status {expected_status}, got {response.status_code}"
                )

            # Get response data
            if response.headers.get("content-type", "").startswith("application/json"):
                response_data = response.json()
            else:
                response_data = {"content": response.text}

            # Check expected keys
            if expected_keys:
                for key in expected_keys:
                    if key not in response_data:
                        raise AssertionError(f"Expected key '{key}' not found in response")

            return response_data

        except Exception as e:
            raise RuntimeError(f"API test failed for {method} {path}: {e}") from e

    def test_health_endpoint(self) -> dict[str, Any]:
        """Test health check endpoint."""
        return self.test_endpoint(
            "GET", "/health", expected_keys=["status", "timestamp", "systems", "version"]
        )

    def test_root_endpoint(self) -> dict[str, Any]:
        """Test root API endpoint."""
        return self.test_endpoint(
            "GET", "/", expected_keys=["name", "version", "description", "endpoints"]
        )

    def test_error_handling(
        self,
        method: str,
        path: str,
        data: Any = None,
        json_data: dict[str, Any] | None = None,
        expected_status: int = 422,
        error_code: str | None = None,
    ) -> dict[str, Any]:
        """Test API error handling.

        Parameters
        ----------
        method : str
            HTTP method
        path : str
            API endpoint path
        data : Any, optional
            Request data
        json_data : Dict[str, Any], optional
            JSON request data
        expected_status : int, default 422
            Expected HTTP status code
        error_code : str, optional
            Expected error code

        Returns
        -------
        Dict[str, Any]
            Error response data
        """
        try:
            if method.upper() == "POST":
                response = self.client.post(path, data=data, json=json_data)
            elif method.upper() == "GET":
                response = self.client.get(path)
            else:
                response = self.client.request(method, path, data=data, json=json_data)

            if response.status_code != expected_status:
                raise AssertionError(
                    f"Expected status {expected_status}, got {response.status_code}"
                )

            error_data = response.json()

            if error_code and "error" in error_data:
                if error_data["error"].get("code") != error_code:
                    raise AssertionError(
                        f"Expected error code {error_code}, got {error_data['error'].get('code')}"
                    )

            return error_data

        except Exception as e:
            raise RuntimeError(f"Error handling test failed: {e}") from e

    def test_monitoring_endpoints(self) -> dict[str, bool]:
        """Test all monitoring endpoints."""
        results = {}

        try:
            # Test soil monitoring
            sensor_id = "SOIL001"
            soil_data = self.test_endpoint(
                "GET", f"/monitoring/soil/{sensor_id}", expected_keys=["sensor_id", "readings"]
            )
            results["soil_monitoring"] = True

            # Test water monitoring
            sensor_id = "WTR001"
            water_data = self.test_endpoint(
                "GET", f"/monitoring/water/{sensor_id}", expected_keys=["sensor_id", "readings"]
            )
            results["water_monitoring"] = True

            # Validate data consistency
            if soil_data["readings"]["ph"] < 5.0 or soil_data["readings"]["ph"] > 9.0:
                logger.warning(f"Unusual soil pH reading: {soil_data['readings']['ph']}")

            if water_data["readings"]["dissolved_oxygen"] < 5.0:
                logger.warning(
                    f"Low dissolved oxygen: {water_data['readings']['dissolved_oxygen']} mg/L"
                )

        except Exception as e:
            logger.error(f"Monitoring endpoint test failed: {e}")
            results["monitoring"] = False

        return results


# Convenience functions for common API testing patterns
def test_api_endpoint(endpoint: str, method: str = "GET", data: Any = None, **kwargs: Any) -> bool:
    """Test an API endpoint with basic validation.

    Parameters
    ----------
    endpoint : str
        API endpoint path
    method : str, default "GET"
        HTTP method
    data : Any, optional
        Request data
    **kwargs : Any
        Additional arguments

    Returns
    -------
    bool
        True if test passes
    """
    try:
        tester = APITester()
        result = tester.test_endpoint(method, endpoint, data=data, **kwargs)
        return True
    except Exception:
        return False


def run_api_test_suite(test_cases: list[dict[str, Any]]) -> dict[str, bool]:
    """Run a suite of API tests.

    Parameters
    ----------
    test_cases : List[Dict[str, Any]]
        List of test case dictionaries

    Returns
    -------
    Dict[str, bool]
        Results of test cases
    """
    results = {}
    tester = APITester()

    for i, test_case in enumerate(test_cases):
        test_name = test_case.get("name", f"test_{i+1}")
        try:
            result = tester.test_endpoint(**test_case)
            results[test_name] = True
        except Exception as e:
            logger.error(f"API test '{test_name}' failed: {e}")
            results[test_name] = False

    return results


async def test_concurrent_api_requests() -> dict[str, Any]:
    """Test concurrent API requests."""
    try:
        tester = APITester()

        async def make_request(endpoint: str, delay: float = 0.1):
            if delay > 0:
                await asyncio.sleep(delay)
            return tester.test_endpoint("GET", endpoint)

        # Create concurrent requests
        endpoints = ["/health", "/", "/health"]
        tasks = [make_request(ep, 0.1 * i) for i, ep in enumerate(endpoints)]

        results = await asyncio.gather(*tasks)

        return {
            "concurrent_requests": len(results),
            "all_successful": all(r["status"] == 200 for r in results),
            "total_requests": len(tasks),
        }

    except Exception as e:
        return {
            "concurrent_requests": 0,
            "all_successful": False,
            "total_requests": 0,
            "error": str(e),
        }


def create_test_equipment_data() -> dict[str, Any]:
    """Create realistic test equipment data."""
    return {
        "equipment_id": "TRACTOR_001",
        "operation": "start_engine",
        "parameters": {"rpm": 1500, "temperature": 85.0, "hydraulics": True},
    }


def create_test_fleet_data() -> dict[str, Any]:
    """Create realistic test fleet data."""
    return {
        "fleet_id": "FLEET_001",
        "operation": "coordinate_field_operation",
        "parameters": {"field_id": "FIELD_A", "formation_type": "line", "spacing": 30.0},
    }
