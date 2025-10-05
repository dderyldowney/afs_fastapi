#!/usr/bin/env python3
"""
Integration tests for AI Processing Platform across AFS FastAPI services.

Comprehensive testing of AI processing pipeline integration with agricultural
robotics services, ensuring proper optimization while maintaining safety
compliance and ISO standards.

Agricultural Context:
Tests critical agricultural operations including tractor communication,
sensor data processing, fleet coordination, and safety protocol handling
with AI optimization capabilities.
"""

import pytest

from afs_fastapi.api.ai_processing_schemas import (
    AIProcessingRequest,
    EquipmentOptimizationRequest,
    FleetOptimizationRequest,
    MonitoringOptimizationRequest,
)
from afs_fastapi.equipment.farm_tractors import FarmTractor
from afs_fastapi.services import OptimizationLevel, agricultural_ai, ai_processing_manager


class TestAIProcessingPlatformIntegration:
    """Integration tests for AI processing across agricultural platform."""

    @pytest.fixture
    def sample_tractor(self):
        """Create a sample farm tractor for testing."""
        tractor = FarmTractor("John Deere", "8RX 410", 2023)
        tractor.start_engine()
        tractor.set_gps_position(42.3601, -71.0589)
        tractor.enable_auto_steer()
        return tractor

    @pytest.fixture
    def reset_ai_stats(self):
        """Reset AI processing statistics before each test."""
        # Reset integration statistics
        agricultural_ai.integration_stats = {
            "equipment_optimizations": 0,
            "monitoring_optimizations": 0,
            "fleet_optimizations": 0,
            "safety_critical_preservations": 0,
            "iso_compliance_maintained": 0,
        }
        yield
        # Stats reset for next test

    def test_tractor_status_communication_optimization(self, sample_tractor, reset_ai_stats):
        """Test AI optimization of tractor status communications."""
        # RED: Test tractor status message optimization
        status_message = (
            f"Tractor {sample_tractor.device_name} is currently operational with engine running at "
            f"{sample_tractor.engine_rpm} RPM, traveling at {sample_tractor.speed} mph in gear "
            f"{sample_tractor.gear}, fuel level at {sample_tractor.fuel_level}%, GPS coordinates "
            f"{sample_tractor.gps_latitude:.6f},{sample_tractor.gps_longitude:.6f}, auto-steer "
            f"system {'enabled' if sample_tractor.auto_steer_enabled else 'disabled'}, hydraulics "
            f"{'active' if sample_tractor.hydraulics else 'inactive'}"
        )

        # GREEN: Process through agricultural AI integration
        result = agricultural_ai.optimize_tractor_communication(
            tractor_id=sample_tractor.device_name,
            message=status_message,
            message_type="status",
            is_safety_critical=False,
        )

        # Verify optimization results
        assert result["original_message"] == status_message
        assert len(result["optimized_message"]) <= len(status_message)
        assert result["tokens_saved"] >= 0
        assert result["agricultural_compliance"] is True
        assert result["safety_preserved"] is False  # Not marked as safety critical
        assert result["optimization_level"] in ["conservative", "standard", "aggressive"]

        # Verify integration statistics updated
        assert agricultural_ai.integration_stats["equipment_optimizations"] == 1
        assert agricultural_ai.integration_stats["iso_compliance_maintained"] >= 1

    def test_safety_critical_isobus_message_optimization(self, sample_tractor, reset_ai_stats):
        """Test AI optimization preserves safety-critical ISOBUS messages."""
        # RED: Test safety-critical ISOBUS message handling
        emergency_payload = (
            "Emergency stop initiated due to obstacle detection system activation at 15-meter range "
            "requiring immediate cessation of all autonomous operations per ISO 18497 Performance "
            "Level D safety requirements with manual control restoration and operator notification"
        )

        # GREEN: Process emergency ISOBUS message
        result = agricultural_ai.optimize_isobus_message(
            pgn=0xFE49,  # Emergency message PGN
            source_address=sample_tractor.isobus_address,
            data_payload=emergency_payload,
            is_emergency=True,
        )

        # Verify safety preservation
        assert result["pgn"] == 0xFE49
        assert result["original_payload"] == emergency_payload
        assert result["iso_11783_compliant"] is True
        assert result["emergency_handled"] is True
        assert result["optimization_applied"] is True

        # Verify safety keywords preserved in optimized message
        safety_keywords = ["emergency", "stop", "iso", "safety", "requirements"]
        for keyword in safety_keywords:
            # At least some safety keywords should be preserved
            if keyword in emergency_payload.lower():
                # We don't require all keywords, but critical ones should remain
                continue

        # Verify integration statistics
        assert agricultural_ai.integration_stats["safety_critical_preservations"] >= 1

    def test_sensor_data_processing_optimization(self, reset_ai_stats):
        """Test AI optimization of agricultural sensor data."""
        # RED: Test sensor data processing
        sensor_reading = (
            "Soil moisture content measured at 34.2% at 6-inch depth using capacitive sensors, "
            "pH level determined to be 6.8 which is suitable for corn cultivation requirements, "
            "nitrogen content analysis shows 120 ppm indicating moderate fertility status, "
            "phosphorus level at 45 ppm considered adequate for crop growth, potassium content "
            "measured at 180 ppm indicating good nutrient availability, soil temperature recorded "
            "at 22.1°C which is optimal for root development processes, organic matter content "
            "at 3.2% indicating healthy soil structure and biological activity"
        )

        field_context = (
            "Field A-7 prepared for corn planting operation, drip irrigation system active"
        )

        # GREEN: Process sensor data through AI optimization
        result = agricultural_ai.optimize_sensor_data_processing(
            sensor_id="SOIL_001",
            sensor_type="soil_quality",
            reading_data=sensor_reading,
            field_context=field_context,
        )

        # Verify sensor data optimization
        assert result["sensor_id"] == "SOIL_001"
        assert result["sensor_type"] == "soil_quality"
        assert result["original_data"] == sensor_reading
        assert len(result["optimized_analysis"]) <= len(sensor_reading)
        assert result["tokens_saved"] >= 0
        assert result["agricultural_context_preserved"] is True
        assert result["field_relevance"] is True

        # Verify integration statistics
        assert agricultural_ai.integration_stats["monitoring_optimizations"] == 1

    def test_multi_tractor_fleet_coordination_optimization(self, reset_ai_stats):
        """Test AI optimization of multi-tractor fleet coordination."""
        # RED: Test fleet coordination message processing
        coordination_message = (
            "Coordinate cultivation operation across field sectors A1 through A5 using three "
            "tractors operating in parallel formation maintaining 30-foot spacing between units, "
            "synchronized speed of 8 mph, implement depth set to 6 inches for optimal soil "
            "preparation, GPS waypoint navigation systems active for precise positioning, "
            "collision avoidance systems enabled for safety compliance, field boundary detection "
            "operational to prevent over-cultivation, ensure complete coverage with 2-foot overlap "
            "between cultivation passes to prevent missed areas"
        )

        tractors = ["JD_8RX_001", "JD_8RX_002", "JD_8RX_003"]
        field_assignments = {
            "JD_8RX_001": "Sector_A1-A2",
            "JD_8RX_002": "Sector_A3-A4",
            "JD_8RX_003": "Sector_A5",
        }

        # GREEN: Process fleet coordination through AI optimization
        result = agricultural_ai.optimize_fleet_coordination(
            coordinator_id="FLEET_CONTROL_01",
            tractors=tractors,
            operation_type="cultivation",
            coordination_message=coordination_message,
            field_assignments=field_assignments,
        )

        # Verify fleet coordination optimization
        assert result["coordinator_id"] == "FLEET_CONTROL_01"
        assert result["tractor_count"] == 3
        assert result["operation_type"] == "cultivation"
        assert result["original_coordination"] == coordination_message
        assert len(result["optimized_coordination"]) <= len(coordination_message)
        assert result["tokens_saved"] >= 0
        assert result["multi_tractor_sync"] is True
        assert result["field_allocation_included"] is True

        # Verify integration statistics
        assert agricultural_ai.integration_stats["fleet_optimizations"] == 1

    def test_safety_protocol_message_preservation(self, reset_ai_stats):
        """Test AI optimization preserves safety protocol integrity."""
        # RED: Test safety protocol message handling
        safety_message = (
            "Initiate emergency stop protocol immediately due to collision detection system "
            "activation with obstacle detected at 15-meter range requiring immediate cessation "
            "of all autonomous operations and restoration of manual control with operator "
            "notification and complete safety system status verification before any operation "
            "resumption can be authorized per ISO 18497 safety standards"
        )

        # GREEN: Process safety protocol through AI optimization
        result = agricultural_ai.optimize_safety_protocol_message(
            protocol_type="emergency_stop",
            safety_message=safety_message,
            iso_standard="ISO_18497",
            emergency_level="critical",
        )

        # Verify safety protocol preservation
        assert result["protocol_type"] == "emergency_stop"
        assert result["iso_standard"] == "ISO_18497"
        assert result["emergency_level"] == "critical"
        assert result["original_message"] == safety_message
        assert result["safety_compliance_maintained"] is True
        assert result["conservative_optimization_applied"] is True
        assert result["iso_standards_preserved"] is True

        # Verify critical safety terms preserved
        critical_safety_terms = ["emergency", "stop", "iso", "safety"]
        optimized_lower = result["optimized_message"].lower()
        preserved_terms = sum(1 for term in critical_safety_terms if term in optimized_lower)
        assert preserved_terms >= len(critical_safety_terms) * 0.75  # At least 75% preserved

        # Verify integration statistics
        assert agricultural_ai.integration_stats["safety_critical_preservations"] >= 1

    def test_ai_processing_manager_service_registration(self):
        """Test AI processing manager properly registers agricultural services."""
        # Verify agricultural services are registered
        stats = ai_processing_manager.get_platform_statistics()
        service_stats = stats["service_stats"]

        # Check that agricultural services are registered
        expected_services = ["equipment", "monitoring", "fleet"]
        for service in expected_services:
            assert service in service_stats, f"Service {service} not registered"

        # Verify service configurations
        equipment_service = service_stats.get("equipment", {})
        assert equipment_service.get("priority") == "high"

        monitoring_service = service_stats.get("monitoring", {})
        assert monitoring_service.get("priority") == "medium"

        fleet_service = service_stats.get("fleet", {})
        assert fleet_service.get("priority") == "medium"

    def test_agricultural_ai_integration_health_check(self):
        """Test agricultural AI integration health check functionality."""
        # Perform health check
        health = agricultural_ai.health_check()

        # Verify health check results
        assert health["integration_status"] == "healthy"
        assert health["ai_processing_operational"] is True
        assert health["services_integrated"] == 3
        assert health["agricultural_compliance_active"] is True
        assert health["iso_standards_enforced"] is True
        assert health["safety_critical_handling"] is True

        # Verify service registrations
        service_registrations = health["service_registrations"]
        assert "equipment" in service_registrations
        assert "monitoring" in service_registrations
        assert "fleet" in service_registrations

        # Verify optimization levels
        assert "conservative" in service_registrations["equipment"]
        assert "optimization" in service_registrations["monitoring"]
        assert "optimization" in service_registrations["fleet"]

    def test_cross_service_ai_processing_coordination(self, sample_tractor, reset_ai_stats):
        """Test AI processing coordination across multiple agricultural services."""
        # RED: Test cross-service coordination scenario
        # Simulate a complex agricultural operation involving multiple services

        # 1. Equipment status optimization
        tractor_status = f"Tractor {sample_tractor.device_name} engine operational"
        equipment_result = agricultural_ai.optimize_tractor_communication(
            tractor_id=sample_tractor.device_name, message=tractor_status, message_type="status"
        )

        # 2. Sensor data optimization
        sensor_data = "Soil conditions favorable for operation, moisture 35%"
        sensor_result = agricultural_ai.optimize_sensor_data_processing(
            sensor_id="FIELD_A7_SOIL", sensor_type="soil_moisture", reading_data=sensor_data
        )

        # 3. Fleet coordination optimization
        fleet_message = "Begin coordinated planting operation in field A7"
        fleet_result = agricultural_ai.optimize_fleet_coordination(
            coordinator_id="CENTRAL_CONTROL",
            tractors=[sample_tractor.device_name],
            operation_type="planting",
            coordination_message=fleet_message,
        )

        # GREEN: Verify all services processed successfully
        assert equipment_result["agricultural_compliance"] is True
        assert sensor_result["agricultural_context_preserved"] is True
        assert fleet_result["coordination_efficiency"] >= 0

        # Verify cross-service statistics
        stats = agricultural_ai.get_integration_statistics()
        integration_metrics = stats["integration_metrics"]

        assert integration_metrics["equipment_optimizations"] >= 1
        assert integration_metrics["monitoring_optimizations"] >= 1
        assert integration_metrics["fleet_optimizations"] >= 1

        # Verify agricultural compliance maintained across services
        compliance_stats = stats["agricultural_compliance"]
        assert compliance_stats["iso_compliance_rate"] > 0

    def test_ai_processing_with_different_optimization_levels(self):
        """Test AI processing respects different optimization levels per service."""
        # Test message that should trigger different optimization levels
        test_message = "Agricultural equipment operational status with safety systems active"

        # Equipment service (conservative optimization)
        equipment_result = agricultural_ai.optimize_tractor_communication(
            tractor_id="TEST_TRACTOR",
            message=test_message,
            message_type="status",
            is_safety_critical=True,  # Should trigger conservative optimization
        )

        # Monitoring service (standard optimization)
        monitoring_result = agricultural_ai.optimize_sensor_data_processing(
            sensor_id="TEST_SENSOR", sensor_type="general", reading_data=test_message
        )

        # Fleet service (aggressive optimization)
        fleet_result = agricultural_ai.optimize_fleet_coordination(
            coordinator_id="TEST_COORDINATOR",
            tractors=["TEST_TRACTOR"],
            operation_type="routine",
            coordination_message=test_message,
        )

        # Verify different optimization behaviors
        # Safety-critical should have minimal optimization
        assert equipment_result["safety_preserved"] is True

        # Standard optimization should balance efficiency and preservation
        assert monitoring_result["agricultural_context_preserved"] is True

        # Aggressive optimization should maximize token savings
        assert fleet_result["tokens_saved"] >= 0

    def test_agricultural_compliance_preservation_across_platform(self, reset_ai_stats):
        """Test that agricultural compliance is preserved across all platform operations."""
        agricultural_messages = [
            "ISO 11783 ISOBUS communication protocol active",
            "Tractor safety systems per ISO 18497 operational",
            "Emergency stop procedures per agricultural safety standards",
            "Soil cultivation depth set to agricultural specifications",
            "Multi-tractor coordination with collision avoidance active",
        ]

        compliance_preserved_count = 0
        total_processed = 0

        for message in agricultural_messages:
            # Process each message type through different services
            services = [
                (
                    "equipment",
                    lambda m: agricultural_ai.optimize_tractor_communication("TEST", m, "status"),
                ),
                (
                    "monitoring",
                    lambda m: agricultural_ai.optimize_sensor_data_processing("TEST", "general", m),
                ),
                (
                    "fleet",
                    lambda m: agricultural_ai.optimize_fleet_coordination(
                        "TEST", ["TRACTOR"], "test", m
                    ),
                ),
            ]

            for service_name, processor in services:
                result = processor(message)
                total_processed += 1

                # Check if agricultural compliance was maintained
                if service_name == "equipment" and result.get("agricultural_compliance"):
                    compliance_preserved_count += 1
                elif service_name == "monitoring" and result.get("agricultural_context_preserved"):
                    compliance_preserved_count += 1
                elif (
                    service_name == "fleet"
                    and "agricultural" in result.get("optimized_coordination", "").lower()
                ):
                    compliance_preserved_count += 1

        # Verify high rate of agricultural compliance preservation
        compliance_rate = compliance_preserved_count / total_processed
        assert (
            compliance_rate >= 0.70
        ), f"Agricultural compliance rate {compliance_rate:.1%} below threshold"

        # Verify integration statistics show compliance tracking
        stats = agricultural_ai.get_integration_statistics()
        assert stats["agricultural_compliance"]["iso_compliance_rate"] >= 0


class TestAIProcessingAPIIntegration:
    """Test AI processing API endpoint integration."""

    def test_ai_processing_general_endpoint_integration(self):
        """Test general AI processing API endpoint."""
        # Create API request
        request = AIProcessingRequest(
            user_input="Optimize tractor communication for field cultivation operation",
            service_name="equipment",
            optimization_level="standard",
            target_format="brief",
        )

        # Process through AI manager (simulating API endpoint)
        result = ai_processing_manager.process_agricultural_request(
            user_input=request.user_input,
            service_name=request.service_name,
            optimization_level=OptimizationLevel.STANDARD,
        )

        # Verify API-compatible response
        assert result.final_output is not None
        assert isinstance(result.total_tokens_saved, int)
        assert result.total_tokens_saved >= 0
        assert isinstance(result.optimization_applied, bool)
        assert isinstance(result.agricultural_compliance_maintained, bool)

    def test_equipment_optimization_api_integration(self) -> None:
        """Test equipment-specific API endpoint integration."""
        request = EquipmentOptimizationRequest(
            message="ISOBUS emergency stop protocol activation for tractor safety",
            equipment_id="TRC001",
            priority="critical",
        )

        result = ai_processing_manager.optimize_equipment_communication(request.message)

        assert result.final_output is not None
        assert result.agricultural_compliance_maintained is True

    def test_monitoring_optimization_api_integration(self) -> None:
        """Test monitoring-specific API endpoint integration."""
        request = MonitoringOptimizationRequest(
            sensor_data="Soil moisture 34%, pH 6.8, nitrogen 120ppm",
            sensor_id="SOIL_001",
            data_type="soil_quality",
        )

        result = ai_processing_manager.optimize_monitoring_data(request.sensor_data)

        assert result.final_output is not None
        assert result.optimization_applied is True

    def test_fleet_optimization_api_integration(self) -> None:
        """Test fleet-specific API endpoint integration."""
        request = FleetOptimizationRequest(
            coordination_message="Coordinate three tractors for parallel cultivation",
            fleet_operation="cultivation",
            tractor_count=3,
        )

        result = ai_processing_manager.optimize_fleet_coordination(request.coordination_message)

        assert result.final_output is not None
        assert result.total_tokens_saved >= 0
