"""
ISO 25119 Functional Safety Compliance Tests for Agricultural Machinery

RED PHASE: Comprehensive test suite for ISO 25119 functional safety implementation.
Agricultural Context: ISO 25119 provides functional safety requirements specifically
for agricultural machinery, complementing existing safety standards.

Safety Requirements: ISO 25119 compliance ensures agricultural machinery meets
Safety Integrity Levels (SIL) for autonomous and semi-autonomous operations.
"""

import unittest


class TestISO25119SafetyIntegrityLevels(unittest.TestCase):
    """
    RED PHASE: Test ISO 25119 Safety Integrity Level (SIL) implementation.

    Agricultural Context: Agricultural machinery requires different SIL levels
    based on operational risk and potential consequences of failure.
    Safety-critical functions require higher SIL levels.
    """

    def test_sil_level_classification_for_agricultural_equipment(self) -> None:
        """
        RED PHASE: Test SIL level classification for agricultural machinery.

        Agricultural Context: Different agricultural systems require different
        safety integrity levels based on risk assessment and potential harm.
        """
        from afs_fastapi.safety.iso25119 import ISO25119SafetyClassifier

        classifier = ISO25119SafetyClassifier()

        # Test autonomous tractor navigation (high risk)
        autonomous_nav_sil = classifier.determine_sil_level(
            system_type="autonomous_navigation",
            operation_mode="field_operations",
            risk_factors=["collision_risk", "operator_safety", "equipment_damage"],
        )

        assert autonomous_nav_sil.sil_level == "SIL 2"
        assert autonomous_nav_sil.justification == "High risk autonomous operation requires SIL 2"
        assert autonomous_nav_sil.verification_requirements is not None

        # Test implement hydraulics (medium risk)
        hydraulic_sil = classifier.determine_sil_level(
            system_type="hydraulic_control",
            operation_mode="implement_operation",
            risk_factors=["equipment_damage", "operational_efficiency"],
        )

        assert hydraulic_sil.sil_level == "SIL 1"
        assert hydraulic_sil.agricultural_specific is True

        # Test emergency stop system (critical)
        emergency_sil = classifier.determine_sil_level(
            system_type="emergency_stop",
            operation_mode="all_operations",
            risk_factors=[
                "operator_safety",
                "collision_risk",
                "equipment_damage",
                "bystander_safety",
            ],
        )

        assert emergency_sil.sil_level == "SIL 3"
        assert emergency_sil.mandatory_functions is not None
        assert emergency_sil.mandatory_functions.include_fail_safe is True

    def test_agricultural_hazard_analysis_and_risk_assessment(self) -> None:
        """
        RED PHASE: Test ISO 25119 HARA (Hazard Analysis and Risk Assessment).

        Agricultural Context: Agricultural operations present unique hazards
        requiring specialized risk assessment including field conditions,
        weather factors, and multi-equipment coordination risks.
        """
        from afs_fastapi.safety.iso25119 import ISO25119HazardAnalyzer

        hazard_analyzer = ISO25119HazardAnalyzer()

        # Test multi-tractor collision risk analysis
        collision_hazard = hazard_analyzer.analyze_hazard(
            hazard_id="MT_COLLISION_001",
            description="Two autonomous tractors operating in same field section",
            agricultural_context={
                "field_type": "open_field",
                "visibility_conditions": "good",
                "equipment_types": ["tractor", "tractor"],
                "operation_speed": "high",
            },
        )

        assert collision_hazard.severity_level == "S3"  # Life-threatening injuries
        assert collision_hazard.exposure_probability == "E4"  # Very high exposure
        assert collision_hazard.controllability == "C2"  # Normally controllable
        assert collision_hazard.agricultural_safety_level == "ASL_B"  # Agricultural Safety Level B

        # Test implement detachment hazard
        detachment_hazard = hazard_analyzer.analyze_hazard(
            hazard_id="IMP_DETACH_001",
            description="Implement unexpectedly detaches during field operation",
            agricultural_context={
                "field_type": "sloped_field",
                "implement_weight": "heavy",
                "operation_speed": "medium",
                "bystander_presence": "possible",
            },
        )

        assert detachment_hazard.severity_level == "S2"  # Severe injuries possible
        assert detachment_hazard.mitigation_required is True
        assert "hydraulic_lock" in detachment_hazard.recommended_safety_functions

    def test_iso25119_safety_lifecycle_implementation(self) -> None:
        """
        RED PHASE: Test ISO 25119 safety lifecycle for agricultural equipment.

        Agricultural Context: Agricultural equipment development must follow
        structured safety lifecycle from concept through decommissioning,
        with agricultural-specific considerations at each phase.
        """
        from afs_fastapi.safety.iso25119 import ISO25119SafetyLifecycle

        lifecycle = ISO25119SafetyLifecycle()

        # Test safety lifecycle phase validation
        concept_phase = lifecycle.execute_phase(
            phase="concept_development",
            agricultural_requirements={
                "equipment_type": "autonomous_tractor",
                "intended_use": "field_cultivation",
                "operating_environment": "agricultural_fields",
                "safety_goals": [
                    "prevent_collision",
                    "ensure_operator_safety",
                    "protect_equipment",
                ],
            },
        )

        assert concept_phase.phase_complete is True
        assert concept_phase.safety_goals_defined is True
        assert len(concept_phase.agricultural_safety_requirements) >= 3
        assert concept_phase.iso25119_compliance_verified is True

        # Test hazard analysis and risk assessment phase
        hara_phase = lifecycle.execute_phase(
            phase="hazard_analysis_risk_assessment",
            inputs=concept_phase.outputs,
            agricultural_scenarios=[
                "field_operation_normal",
                "field_operation_adverse_weather",
                "multi_equipment_coordination",
                "emergency_situations",
            ],
        )

        assert hara_phase.hazards_identified is True
        assert hara_phase.risk_assessment_complete is True
        assert hara_phase.safety_integrity_requirements_defined is True


class TestISO25119SafetyFunctions(unittest.TestCase):
    """
    RED PHASE: Test ISO 25119 safety function implementation for agricultural equipment.

    Agricultural Context: Safety functions must be specifically designed for
    agricultural operations including autonomous navigation, implement control,
    and emergency response systems.
    """

    def test_autonomous_tractor_safety_functions(self) -> None:
        """
        RED PHASE: Test safety functions for autonomous agricultural tractors.

        Agricultural Context: Autonomous tractors require comprehensive safety
        functions including path planning validation, obstacle detection,
        and emergency stop capabilities compliant with ISO 25119.
        """
        from afs_fastapi.safety.iso25119 import AutonomousTractorSafetyFunctions

        safety_functions = AutonomousTractorSafetyFunctions()

        # Test safe state transition
        safe_state_result = safety_functions.transition_to_safe_state(
            trigger="obstacle_detected",
            current_state="autonomous_operation",
            environmental_conditions={
                "field_slope": 5.2,  # degrees
                "soil_moisture": "high",
                "visibility": "good",
                "other_equipment_present": True,
            },
        )

        assert safe_state_result.safe_state_achieved is True
        assert safe_state_result.stopping_distance <= 10.0  # meters (ISO 25119 requirement)
        assert safe_state_result.emergency_systems_activated is True
        assert safe_state_result.operator_notification_sent is True

        # Test path validation safety function
        path_validation = safety_functions.validate_planned_path(
            planned_path=[
                {"x": 0, "y": 0, "heading": 0},
                {"x": 100, "y": 0, "heading": 0},
                {"x": 100, "y": 50, "heading": 90},
            ],
            field_boundaries={"min_x": -10, "max_x": 110, "min_y": -10, "max_y": 60},
            obstacle_map={"obstacles": [{"x": 50, "y": 25, "radius": 5}]},
        )

        assert path_validation.path_safe is True
        assert path_validation.collision_risk_acceptable is True
        assert path_validation.field_boundary_respected is True
        assert path_validation.iso25119_compliant is True

    def test_implement_safety_monitoring(self) -> None:
        """
        RED PHASE: Test safety monitoring for agricultural implements.

        Agricultural Context: Agricultural implements require continuous
        safety monitoring including hydraulic pressure, attachment status,
        and operational parameters to prevent equipment damage and injury.
        """
        from afs_fastapi.safety.iso25119 import ImplementSafetyMonitor

        safety_monitor = ImplementSafetyMonitor()

        # Test hydraulic safety monitoring
        hydraulic_status = safety_monitor.monitor_hydraulic_system(
            pressure_reading=175.0,  # bar (87.5% of max, ensuring >10% safety margin)
            temperature_reading=65.3,  # Celsius
            flow_rate=45.2,  # L/min
            system_limits={"max_pressure": 200.0, "max_temperature": 80.0, "min_flow_rate": 40.0},
        )

        assert hydraulic_status.system_safe is True
        assert hydraulic_status.pressure_within_limits is True
        assert hydraulic_status.temperature_acceptable is True
        assert hydraulic_status.safety_margin_adequate is True

        # Test implement attachment safety
        attachment_status = safety_monitor.verify_implement_attachment(
            attachment_sensors={
                "top_link_engaged": True,
                "lower_links_engaged": True,
                "hydraulic_connected": True,
                "electrical_connected": True,
                "pto_connected": False,  # Not required for this implement
            },
            implement_type="cultivator",
            operation_mode="transport",
        )

        assert attachment_status.attachment_secure is True
        assert attachment_status.all_required_connections_verified is True
        assert attachment_status.safe_for_operation is True

    def test_emergency_response_system_iso25119(self) -> None:
        """
        RED PHASE: Test ISO 25119 compliant emergency response system.

        Agricultural Context: Emergency response must handle agricultural-specific
        scenarios including multi-equipment coordination, field evacuation,
        and implement securing procedures.
        """
        from afs_fastapi.safety.iso25119 import ISO25119EmergencyResponse

        emergency_system = ISO25119EmergencyResponse()

        # Test multi-equipment emergency stop
        emergency_response = emergency_system.execute_emergency_stop(
            trigger_source="operator_command",
            affected_equipment=["tractor_01", "tractor_02", "implement_cultivator"],
            emergency_type="immediate_stop",
            field_conditions={
                "slope": 3.5,  # degrees
                "surface_condition": "firm",
                "weather": "clear",
            },
        )

        assert emergency_response.all_equipment_stopped is True
        assert emergency_response.response_time <= 1.0  # seconds (ISO 25119 requirement)
        assert emergency_response.implements_secured is True
        assert emergency_response.operator_notifications_sent is True
        assert emergency_response.iso25119_compliant is True

        # Test emergency communication protocol
        communication_test = emergency_system.test_emergency_communication(
            communication_channels=["radio", "cellular", "satellite"],
            test_scenarios=["normal_conditions", "interference", "partial_failure"],
        )

        assert communication_test.primary_channel_functional is True
        assert communication_test.backup_channels_available is True
        assert communication_test.message_delivery_confirmed is True


class TestISO25119VerificationValidation(unittest.TestCase):
    """
    RED PHASE: Test ISO 25119 verification and validation requirements.

    Agricultural Context: Agricultural equipment must undergo rigorous
    verification and validation testing including field testing under
    various agricultural conditions and scenarios.
    """

    def test_agricultural_equipment_verification_procedures(self) -> None:
        """
        RED PHASE: Test verification procedures for agricultural equipment.

        Agricultural Context: Equipment verification must include testing
        under various agricultural conditions including different soil types,
        weather conditions, and operational scenarios.
        """
        from afs_fastapi.safety.iso25119 import ISO25119VerificationSuite

        verification_suite = ISO25119VerificationSuite()

        # Test safety function verification
        verification_results = verification_suite.verify_safety_functions(
            equipment_type="autonomous_tractor",
            safety_functions=[
                "emergency_stop",
                "obstacle_avoidance",
                "path_following",
                "implement_control",
            ],
            test_conditions={
                "field_types": ["flat", "sloped", "terraced"],
                "weather_conditions": ["clear", "rain", "fog"],
                "soil_conditions": ["dry", "wet", "muddy"],
                "crop_types": ["corn", "wheat", "soybeans"],
            },
        )

        assert verification_results.all_functions_verified is True
        assert verification_results.test_coverage >= 95.0  # Percentage
        assert verification_results.agricultural_scenarios_covered is True
        assert verification_results.iso25119_compliance_verified is True

        # Test failure mode verification
        failure_mode_tests = verification_suite.test_failure_modes(
            failure_scenarios=[
                "sensor_failure_gps",
                "communication_loss",
                "hydraulic_pressure_drop",
                "engine_overheat",
                "implement_detachment",
            ],
            safety_requirements={
                "safe_state_transition_time": 2.0,  # seconds
                "operator_notification_time": 0.5,  # seconds
                "system_recovery_capability": True,
            },
        )

        assert failure_mode_tests.all_scenarios_tested is True
        assert failure_mode_tests.safe_state_achieved_for_all is True
        assert failure_mode_tests.response_times_acceptable is True

    def test_field_validation_testing(self) -> None:
        """
        RED PHASE: Test field validation testing for agricultural equipment.

        Agricultural Context: Field validation must demonstrate safe operation
        under real-world agricultural conditions with actual crops, varying
        terrain, and operational stresses.
        """
        from afs_fastapi.safety.iso25119 import ISO25119FieldValidation

        field_validator = ISO25119FieldValidation()

        # Test comprehensive field validation
        field_test_results = field_validator.execute_field_validation(
            test_duration_hours=100,  # Minimum test duration
            field_conditions={
                "total_fields": 5,
                "field_sizes_hectares": [10, 25, 50, 75, 100],
                "crop_types": ["corn", "soybeans", "wheat"],
                "terrain_variations": ["flat", "rolling", "steep"],
                "weather_exposure": ["sunny", "rainy", "windy", "foggy"],
            },
            operational_scenarios=[
                "normal_cultivation",
                "precision_planting",
                "harvest_operations",
                "transport_mode",
                "emergency_scenarios",
            ],
        )

        assert field_test_results.validation_successful is True
        assert field_test_results.safety_incidents == 0
        assert field_test_results.operational_effectiveness >= 90.0  # Percentage
        assert field_test_results.farmer_acceptance_rating >= 8.0  # Out of 10
        assert field_test_results.iso25119_field_requirements_met is True

        # Test performance under stress conditions
        stress_test_results = field_validator.validate_under_stress_conditions(
            stress_scenarios=[
                "continuous_operation_12_hours",
                "high_dust_environment",
                "temperature_extremes",
                "multiple_equipment_coordination",
                "communication_interference",
            ]
        )

        assert stress_test_results.performance_maintained is True
        assert stress_test_results.safety_functions_reliable is True
        assert stress_test_results.degradation_acceptable is True


class TestISO25119Documentation(unittest.TestCase):
    """
    RED PHASE: Test ISO 25119 documentation and traceability requirements.

    Agricultural Context: Agricultural equipment safety documentation must
    provide complete traceability from safety requirements through
    implementation to validation results.
    """

    def test_safety_case_documentation(self) -> None:
        """
        RED PHASE: Test safety case documentation for agricultural equipment.

        Agricultural Context: Safety case must demonstrate that agricultural
        equipment meets safety requirements through systematic argumentation
        supported by evidence from testing and analysis.
        """
        from afs_fastapi.safety.iso25119 import ISO25119SafetyCase

        safety_case = ISO25119SafetyCase()

        # Test safety case generation
        case_document = safety_case.generate_safety_case(
            equipment_specification={
                "type": "autonomous_tractor",
                "intended_use": "field_cultivation",
                "operational_domain": "agricultural_fields",
                "automation_level": "SAE_Level_4",
            },
            safety_requirements_trace={
                "requirements_count": 127,
                "sil_levels_addressed": ["SIL 1", "SIL 2", "SIL 3"],
                "verification_methods": ["testing", "analysis", "review"],
                "validation_evidence": ["field_tests", "simulation", "expert_review"],
            },
        )

        assert case_document.safety_argument_complete is True
        assert case_document.evidence_sufficient is True
        assert case_document.traceability_established is True
        assert case_document.agricultural_considerations_addressed is True
        assert case_document.iso25119_compliant is True

        # Test documentation traceability
        traceability_matrix = safety_case.generate_traceability_matrix(
            safety_goals=["prevent_collision", "ensure_safe_stop", "maintain_control"],
            safety_requirements=["REQ_001", "REQ_002", "REQ_003", "REQ_004"],
            implementation_elements=[
                "emergency_stop_module",
                "collision_detection",
                "path_controller",
            ],
            verification_activities=["unit_tests", "integration_tests", "field_tests"],
        )

        assert traceability_matrix.complete_coverage is True
        assert traceability_matrix.bidirectional_traceability is True
        assert traceability_matrix.gap_analysis_performed is True
