"""Tests for CollisionAvoidanceSystem - TDD RED Phase Implementation.

This module implements comprehensive unit tests for the CollisionAvoidanceSystem,
which provides real-time collision prevention between autonomous agricultural
tractors using dynamic safety zones and predictive path analysis.

Agricultural Context
--------------------
Autonomous agricultural tractors operating in the same field must maintain
safe separation distances while maximizing operational efficiency. The system must:
- Calculate dynamic safety zones based on speed, terrain, and equipment
- Predict potential collision paths using trajectory analysis
- Execute graduated collision avoidance responses
- Integrate with fleet coordination for conflict resolution
- Handle emergency collision scenarios with immediate response

The system implements ISO 18497 collision avoidance requirements for autonomous
agricultural equipment, ensuring safe multi-tractor field operations.

Test Strategy
-------------
Tests follow TDD methodology with realistic agricultural collision scenarios:
1. RED Phase: Failing tests defining expected collision avoidance behavior
2. GREEN Phase: Minimal implementation meeting safety requirements
3. REFACTOR Phase: Enhanced implementation with performance optimizations

These tests validate actual collision detection and avoidance logic.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from afs_fastapi.services.collision_avoidance_system import (
    CollisionAvoidanceAction,
    CollisionAvoidanceSystem,
    CollisionRisk,
    CollisionThreat,
    DynamicSafetyZone,
    PositionVector,
    TrajectoryPrediction,
    VelocityVector,
)


class TestDynamicSafetyZoneCalculation:
    """Test dynamic safety zone calculation for agricultural equipment.

    Tests the fundamental capability to calculate appropriate safety zones
    based on tractor operational parameters and field conditions.
    """

    def test_initialization_with_safety_parameters(self) -> None:
        """Test CollisionAvoidanceSystem initialization with safety parameters.

        Agricultural Context:
        Each tractor must maintain appropriate safety zones based on equipment
        dimensions, operational speed, and field conditions. Parameters must
        comply with ISO 18497 safety requirements for autonomous equipment.
        """
        # Arrange - Agricultural safety parameters
        base_safety_radius = 8.0  # meters - minimum safe distance
        speed_factor = 2.0  # safety zone expansion per m/s
        equipment_width = 12.0  # meters - cultivator implement width
        reaction_time = 1.5  # seconds - system reaction time

        # Act
        collision_system = CollisionAvoidanceSystem(
            base_safety_radius=base_safety_radius,
            speed_factor=speed_factor,
            equipment_width=equipment_width,
            reaction_time=reaction_time,
        )

        # Assert
        assert collision_system.base_safety_radius == base_safety_radius
        assert collision_system.speed_factor == speed_factor
        assert collision_system.equipment_width == equipment_width
        assert collision_system.reaction_time == reaction_time
        assert collision_system.collision_detection_enabled is True

    def test_dynamic_safety_zone_calculation_for_working_tractor(self) -> None:
        """Test calculation of dynamic safety zone for working tractor.

        Agricultural Context:
        A tractor performing cultivation at operational speed needs a larger
        safety zone than an idle tractor. Zone must account for implement
        width, stopping distance, and system reaction time.
        """
        # Arrange
        position = PositionVector(lat=40.7128, lon=-74.0060, heading=45.0)
        velocity = VelocityVector(speed=6.0, direction=45.0)  # 6 m/s cultivation speed

        collision_system = CollisionAvoidanceSystem(
            base_safety_radius=8.0, speed_factor=2.0, equipment_width=12.0, reaction_time=1.5
        )

        # Act
        safety_zone = collision_system.calculate_dynamic_safety_zone(
            position=position, velocity=velocity, operational_status="WORKING"
        )

        # Assert
        assert isinstance(safety_zone, DynamicSafetyZone)
        assert safety_zone.radius > 8.0  # Expanded beyond base radius
        assert safety_zone.forward_extension > safety_zone.lateral_extension  # Longer forward
        assert safety_zone.equipment_clearance >= 12.0  # At least implement width
        assert safety_zone.stopping_distance > 0.0  # Calculated stopping distance
        assert abs(safety_zone.center_position.lat - position.lat) < 0.001
        assert abs(safety_zone.center_position.lon - position.lon) < 0.001

    def test_safety_zone_adaptation_for_different_speeds(self) -> None:
        """Test safety zone adaptation based on tractor operational speed.

        Agricultural Context:
        Higher operational speeds require proportionally larger safety zones
        due to increased stopping distances and reduced reaction time.
        Zones must scale appropriately for different agricultural operations.
        """
        # Arrange
        position = PositionVector(lat=40.0, lon=-75.0, heading=90.0)
        collision_system = CollisionAvoidanceSystem(base_safety_radius=8.0, speed_factor=2.0)

        # Test different operational speeds
        test_speeds = [
            (2.0, "PLANTING"),  # Slow precision operation
            (6.0, "CULTIVATION"),  # Normal field operation
            (10.0, "TRANSPORT"),  # High speed transport
        ]

        safety_zones = []
        for speed, operation in test_speeds:
            velocity = VelocityVector(speed=speed, direction=90.0)
            zone = collision_system.calculate_dynamic_safety_zone(
                position=position, velocity=velocity, operational_status=operation
            )
            safety_zones.append((speed, zone))

        # Assert - Safety zones increase with speed
        assert safety_zones[0][1].radius < safety_zones[1][1].radius  # Planting < Cultivation
        assert safety_zones[1][1].radius < safety_zones[2][1].radius  # Cultivation < Transport
        assert safety_zones[2][1].stopping_distance > safety_zones[0][1].stopping_distance

    def test_safety_zone_adjustment_for_equipment_dimensions(self) -> None:
        """Test safety zone adjustment based on implement dimensions.

        Agricultural Context:
        Different agricultural implements (plows, cultivators, planters)
        have varying widths and require appropriate safety clearances
        to prevent equipment damage during multi-tractor operations.
        """
        # Arrange
        position = PositionVector(lat=41.0, lon=-76.0, heading=0.0)
        velocity = VelocityVector(speed=5.0, direction=0.0)

        # Test different implement widths
        implement_configurations = [
            (8.0, "NARROW_CULTIVATOR"),
            (12.0, "STANDARD_PLOW"),
            (18.0, "WIDE_PLANTER"),
        ]

        for width, _implement_type in implement_configurations:
            collision_system = CollisionAvoidanceSystem(
                base_safety_radius=8.0, equipment_width=width
            )

            # Act
            safety_zone = collision_system.calculate_dynamic_safety_zone(
                position=position, velocity=velocity, operational_status="WORKING"
            )

            # Assert
            assert safety_zone.equipment_clearance >= width
            assert safety_zone.lateral_extension >= width / 2.0  # Half-width clearance


class TestTrajectoryPredictionAndCollisionDetection:
    """Test trajectory prediction and collision threat detection.

    Tests the system's ability to predict tractor movement paths and
    identify potential collision scenarios in agricultural operations.
    """

    def test_trajectory_prediction_for_straight_line_movement(self) -> None:
        """Test trajectory prediction for straight-line tractor movement.

        Agricultural Context:
        Most agricultural operations involve straight-line movement across
        fields. System must accurately predict future positions to enable
        proactive collision avoidance during coordinated field operations.
        """
        # Arrange
        current_position = PositionVector(lat=40.5, lon=-75.5, heading=90.0)
        velocity = VelocityVector(speed=8.0, direction=90.0)  # 8 m/s eastward

        collision_system = CollisionAvoidanceSystem()
        prediction_horizon = 10.0  # seconds

        # Act
        trajectory = collision_system.predict_trajectory(
            position=current_position, velocity=velocity, prediction_horizon=prediction_horizon
        )

        # Assert
        assert isinstance(trajectory, TrajectoryPrediction)
        assert len(trajectory.future_positions) > 0
        assert trajectory.prediction_horizon == prediction_horizon
        assert trajectory.confidence_level > 0.8  # High confidence for straight line

        # Check trajectory extends eastward (90 degrees)
        final_position = trajectory.future_positions[-1]
        assert final_position.lon > current_position.lon  # Moved east
        assert abs(final_position.lat - current_position.lat) < 0.001  # Minimal north/south drift

    def test_collision_threat_detection_between_converging_tractors(self) -> None:
        """Test collision threat detection between converging tractors.

        Agricultural Context:
        When tractors are working converging field patterns, system must
        detect potential collision points and calculate threat levels
        based on closest approach distance and time to collision.
        """
        # Arrange
        collision_system = CollisionAvoidanceSystem(base_safety_radius=10.0)

        # Tractor 1 - Moving east
        tractor1_position = PositionVector(lat=40.0, lon=-75.0, heading=90.0)
        tractor1_velocity = VelocityVector(speed=6.0, direction=90.0)

        # Tractor 2 - Moving south (converging path)
        tractor2_position = PositionVector(
            lat=40.001, lon=-74.998, heading=180.0
        )  # ~100m north, 20m east
        tractor2_velocity = VelocityVector(speed=5.0, direction=180.0)

        # Act
        threat = collision_system.detect_collision_threat(
            own_position=tractor1_position,
            own_velocity=tractor1_velocity,
            other_position=tractor2_position,
            other_velocity=tractor2_velocity,
            prediction_horizon=15.0,
        )

        # Assert
        assert isinstance(threat, CollisionThreat)
        assert threat.collision_detected is True
        assert threat.time_to_collision > 0.0
        assert threat.closest_approach_distance < 20.0  # Will pass close
        assert threat.risk_level in [CollisionRisk.HIGH, CollisionRisk.CRITICAL]
        assert threat.collision_point.lat is not None
        assert threat.collision_point.lon is not None

    def test_no_collision_threat_for_parallel_tractors(self) -> None:
        """Test no collision threat detected for parallel tractor movements.

        Agricultural Context:
        Tractors working parallel field strips should not trigger collision
        warnings when maintaining safe separation distances during
        coordinated agricultural operations.
        """
        # Arrange
        collision_system = CollisionAvoidanceSystem(base_safety_radius=8.0)

        # Tractor 1 - Moving east in south strip
        tractor1_position = PositionVector(lat=40.0, lon=-75.0, heading=90.0)
        tractor1_velocity = VelocityVector(speed=6.0, direction=90.0)

        # Tractor 2 - Moving east in north strip (safe distance)
        tractor2_position = PositionVector(lat=40.0005, lon=-75.0, heading=90.0)  # ~55m north
        tractor2_velocity = VelocityVector(speed=6.0, direction=90.0)

        # Act
        threat = collision_system.detect_collision_threat(
            own_position=tractor1_position,
            own_velocity=tractor1_velocity,
            other_position=tractor2_position,
            other_velocity=tractor2_velocity,
            prediction_horizon=30.0,
        )

        # Assert
        assert threat.collision_detected is False
        assert threat.risk_level == CollisionRisk.NONE
        assert threat.closest_approach_distance > 50.0  # Maintain safe distance

    def test_collision_detection_with_stationary_obstacle(self) -> None:
        """Test collision detection with stationary agricultural obstacle.

        Agricultural Context:
        Fields may contain stationary obstacles (equipment, buildings, trees).
        Moving tractors must detect potential collisions with stationary
        objects and plan appropriate avoidance maneuvers.
        """
        # Arrange
        collision_system = CollisionAvoidanceSystem(base_safety_radius=8.0)

        # Moving tractor
        tractor_position = PositionVector(lat=40.0, lon=-75.0, heading=90.0)
        tractor_velocity = VelocityVector(speed=5.0, direction=90.0)

        # Stationary obstacle directly ahead
        obstacle_position = PositionVector(lat=40.0, lon=-74.995, heading=0.0)  # ~40m east
        obstacle_velocity = VelocityVector(speed=0.0, direction=0.0)  # Stationary

        # Act
        threat = collision_system.detect_collision_threat(
            own_position=tractor_position,
            own_velocity=tractor_velocity,
            other_position=obstacle_position,
            other_velocity=obstacle_velocity,
            prediction_horizon=10.0,
        )

        # Assert
        assert threat.collision_detected is True
        assert threat.time_to_collision < 10.0  # Will reach obstacle soon
        assert threat.closest_approach_distance < 8.0  # Within safety radius
        assert threat.risk_level in [CollisionRisk.HIGH, CollisionRisk.CRITICAL]


class TestCollisionAvoidanceActions:
    """Test collision avoidance action generation and execution.

    Tests the system's ability to generate appropriate avoidance actions
    when collision threats are detected in agricultural operations.
    """

    @pytest.mark.asyncio
    async def test_collision_avoidance_action_for_head_on_approach(self) -> None:
        """Test avoidance action generation for head-on collision threat.

        Agricultural Context:
        When tractors approach each other head-on (end of field turns,
        transport operations), system must generate immediate avoidance
        actions with priority given to the tractor with right-of-way.
        """
        # Arrange
        collision_system = CollisionAvoidanceSystem(base_safety_radius=12.0)

        # High-risk head-on collision scenario
        threat = CollisionThreat(
            collision_detected=True,
            time_to_collision=3.0,  # 3 seconds - immediate threat
            closest_approach_distance=2.0,  # Very close approach
            risk_level=CollisionRisk.CRITICAL,
            collision_point=PositionVector(lat=40.001, lon=-74.999, heading=0.0),
            relative_bearing=0.0,  # Head-on
        )

        # Act
        action = await collision_system.generate_avoidance_action(
            threat=threat, own_tractor_id="TRACTOR_ALPHA", other_tractor_id="TRACTOR_BETA"
        )

        # Assert
        assert isinstance(action, CollisionAvoidanceAction)
        assert action.action_type in ["EMERGENCY_STOP", "IMMEDIATE_MANEUVER"]
        assert action.priority == "CRITICAL"
        assert action.speed_adjustment <= 0.0  # Reduce or stop speed
        assert abs(action.heading_adjustment) > 0.0  # Course change required
        assert action.emergency_stop is True
        assert "immediate collision threat" in action.safety_message.lower()

    @pytest.mark.asyncio
    async def test_gradual_avoidance_for_moderate_collision_risk(self) -> None:
        """Test gradual avoidance action for moderate collision risk.

        Agricultural Context:
        For moderate collision risks with sufficient time to react,
        system should generate gradual course corrections that maintain
        agricultural productivity while ensuring safe separation.
        """
        # Arrange
        collision_system = CollisionAvoidanceSystem(base_safety_radius=10.0)

        # Moderate risk collision scenario
        threat = CollisionThreat(
            collision_detected=True,
            time_to_collision=12.0,  # 12 seconds - time to react
            closest_approach_distance=6.0,  # Close but not critical
            risk_level=CollisionRisk.MODERATE,
            collision_point=PositionVector(lat=40.002, lon=-74.998, heading=0.0),
            relative_bearing=30.0,  # Crossing path
        )

        # Act
        action = await collision_system.generate_avoidance_action(
            threat=threat, own_tractor_id="TRACTOR_001", other_tractor_id="TRACTOR_002"
        )

        # Assert
        assert action.action_type == "GRADUAL_MANEUVER"
        assert action.priority == "MODERATE"
        assert -0.3 <= action.speed_adjustment <= 0.0  # Slight speed reduction
        assert abs(action.heading_adjustment) <= 15.0  # Minor course correction
        assert action.emergency_stop is False
        assert action.maintain_agricultural_pattern is True

    @pytest.mark.asyncio
    async def test_fleet_coordination_for_collision_resolution(self) -> None:
        """Test fleet coordination integration for collision resolution.

        Agricultural Context:
        When collision threats involve multiple tractors, system must
        coordinate with fleet management to determine optimal resolution
        strategy considering work priorities and field patterns.
        """
        # Arrange
        mock_fleet_coordination = AsyncMock()
        mock_fleet_coordination.resolve_collision_conflict.return_value = {
            "primary_avoider": "TRACTOR_GAMMA",
            "maneuver_type": "YIELD_RIGHT_OF_WAY",
            "secondary_action": "MAINTAIN_COURSE",
        }

        collision_system = CollisionAvoidanceSystem(base_safety_radius=10.0)

        threat = CollisionThreat(
            collision_detected=True,
            time_to_collision=8.0,
            closest_approach_distance=4.0,
            risk_level=CollisionRisk.HIGH,
            collision_point=PositionVector(lat=40.003, lon=-74.997, heading=0.0),
            relative_bearing=45.0,
        )

        # Act
        action = await collision_system.coordinate_avoidance_with_fleet(
            threat=threat,
            own_tractor_id="TRACTOR_GAMMA",
            other_tractor_id="TRACTOR_DELTA",
            fleet_coordination=mock_fleet_coordination,
        )

        # Assert
        assert isinstance(action, CollisionAvoidanceAction)
        mock_fleet_coordination.resolve_collision_conflict.assert_called_once()
        assert action.fleet_coordination_required is True
        assert action.coordinated_maneuver is True

    @pytest.mark.asyncio
    async def test_emergency_collision_response(self) -> None:
        """Test emergency collision response for imminent threats.

        Agricultural Context:
        For imminent collision threats (< 2 seconds), system must execute
        immediate emergency stop regardless of agricultural operations
        to prevent equipment damage and safety hazards.
        """
        # Arrange
        collision_system = CollisionAvoidanceSystem(base_safety_radius=8.0)

        # Critical imminent threat
        threat = CollisionThreat(
            collision_detected=True,
            time_to_collision=1.2,  # < 2 seconds - imminent
            closest_approach_distance=0.5,  # Extremely close
            risk_level=CollisionRisk.CRITICAL,
            collision_point=PositionVector(lat=40.0001, lon=-74.9999, heading=0.0),
            relative_bearing=5.0,  # Nearly head-on
        )

        # Act
        action = await collision_system.generate_avoidance_action(
            threat=threat, own_tractor_id="TRACTOR_EMERGENCY", other_tractor_id="TRACTOR_OBSTACLE"
        )

        # Assert
        assert action.action_type == "EMERGENCY_STOP"
        assert action.priority == "CRITICAL"
        assert action.emergency_stop is True
        assert action.speed_adjustment == -1.0  # Full stop
        assert action.time_to_execute <= 1.0  # Execute immediately
        assert "emergency" in action.safety_message.lower()


class TestDynamicSafetyZoneAdaptation:
    """Test dynamic safety zone adaptation to operational conditions.

    Tests the system's ability to adapt safety zones based on communication
    health, weather conditions, and operational parameters.
    """

    def test_safety_zone_expansion_for_degraded_communication(self) -> None:
        """Test safety zone expansion when communication is degraded.

        Agricultural Context:
        When fleet communication is unreliable, tractors must expand
        safety zones to account for potential coordination failures
        and delayed emergency response capabilities.
        """
        # Arrange
        position = PositionVector(lat=40.0, lon=-75.0, heading=45.0)
        velocity = VelocityVector(speed=5.0, direction=45.0)

        collision_system = CollisionAvoidanceSystem(base_safety_radius=8.0)

        # Simulate degraded communication health
        communication_health = {
            "overall_health_score": 0.3,  # Poor communication
            "lost_tractors": {"TRACTOR_002", "TRACTOR_003"},
            "message_success_rate": 0.4,
        }

        # Act
        safety_zone = collision_system.calculate_adaptive_safety_zone(
            position=position,
            velocity=velocity,
            operational_status="WORKING",
            communication_health=communication_health,
        )

        # Assert
        assert isinstance(safety_zone, DynamicSafetyZone)
        assert safety_zone.radius > 12.0  # Expanded beyond normal due to poor comms
        assert safety_zone.communication_penalty_applied is True
        assert safety_zone.expansion_factor > 1.5  # Significant expansion

    def test_safety_zone_adjustment_for_field_conditions(self) -> None:
        """Test safety zone adjustment based on field conditions.

        Agricultural Context:
        Field conditions (wet soil, slopes, obstacles) affect tractor
        stopping distances and maneuverability, requiring dynamic
        safety zone adjustments for safe multi-tractor operations.
        """
        # Arrange
        position = PositionVector(lat=40.0, lon=-75.0, heading=0.0)
        velocity = VelocityVector(speed=6.0, direction=0.0)

        collision_system = CollisionAvoidanceSystem(base_safety_radius=8.0)

        # Test different field conditions
        field_conditions = [
            {"terrain": "FLAT_DRY", "grip_coefficient": 0.9, "expected_multiplier": 1.0},
            {"terrain": "WET_SOIL", "grip_coefficient": 0.6, "expected_multiplier": 1.4},
            {"terrain": "STEEP_SLOPE", "grip_coefficient": 0.8, "expected_multiplier": 1.6},
        ]

        for condition in field_conditions:
            # Act
            safety_zone = collision_system.calculate_adaptive_safety_zone(
                position=position,
                velocity=velocity,
                operational_status="WORKING",
                field_conditions=condition,
            )

            # Assert
            from typing import cast

            multiplier = cast(float, condition.get("expected_multiplier", 1.0))
            expected_min_radius = 8.0 * multiplier
            assert safety_zone.radius >= expected_min_radius
            assert safety_zone.stopping_distance_adjustment >= 1.0

    def test_multi_tractor_safety_zone_coordination(self) -> None:
        """Test safety zone coordination between multiple tractors.

        Agricultural Context:
        When multiple tractors operate in proximity, their safety zones
        may overlap. System must coordinate zone boundaries to prevent
        conflicts while maintaining operational efficiency.
        """
        # Arrange
        collision_system = CollisionAvoidanceSystem(base_safety_radius=8.0)

        # Three tractors in proximity
        tractor_states = [
            {
                "id": "TRACTOR_A",
                "position": PositionVector(lat=40.0, lon=-75.0, heading=90.0),
                "velocity": VelocityVector(speed=5.0, direction=90.0),
                "status": "WORKING",
            },
            {
                "id": "TRACTOR_B",
                "position": PositionVector(lat=40.0002, lon=-75.0, heading=90.0),  # ~22m north
                "velocity": VelocityVector(speed=5.0, direction=90.0),
                "status": "WORKING",
            },
            {
                "id": "TRACTOR_C",
                "position": PositionVector(
                    lat=40.0001, lon=-75.001, heading=270.0
                ),  # Between, opposite direction
                "velocity": VelocityVector(speed=4.0, direction=270.0),
                "status": "WORKING",
            },
        ]

        # Act
        coordinated_zones = collision_system.coordinate_multi_tractor_safety_zones(
            tractor_states=tractor_states
        )

        # Assert
        assert len(coordinated_zones) == 3
        for _tractor_id, zone in coordinated_zones.items():
            assert isinstance(zone, DynamicSafetyZone)
            assert zone.multi_tractor_coordination is True

        # Check for zone overlap resolution
        zone_a = coordinated_zones["TRACTOR_A"]
        zone_b = coordinated_zones["TRACTOR_B"]
        # Zones should be adjusted to prevent excessive overlap
        assert zone_a.coordination_adjustment_applied is True
        assert zone_b.coordination_adjustment_applied is True
