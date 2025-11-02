"""Tests for advanced message prioritization framework with QoS levels for agricultural operations.

This module tests the sophisticated message prioritization system that handles
CAN bus traffic optimization for multi-tractor fleet coordination with
safety-critical and operational message classification.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import Mock

# Import will be created
from afs_fastapi.equipment.advanced_message_prioritization import (
    AdvancedMessagePrioritizer,
    AgriculturalOperationContext,
    MessageClassification,
    PrioritizedMessage,
    QoSLevel,
    TrafficThrottlingDecision,
)


class TestQoSLevelDefinitions:
    """Test Quality of Service level definitions for agricultural operations."""

    def test_qos_level_priority_ordering(self) -> None:
        """Test that QoS levels are correctly ordered by priority."""
        # RED: QoS levels must have correct priority hierarchy
        assert QoSLevel.EMERGENCY.priority > QoSLevel.CRITICAL.priority
        assert QoSLevel.CRITICAL.priority > QoSLevel.OPERATIONAL.priority
        assert QoSLevel.OPERATIONAL.priority > QoSLevel.INFORMATIONAL.priority

    def test_qos_level_timeout_definitions(self) -> None:
        """Test that QoS levels have appropriate timeout values for agricultural operations."""
        # RED: Emergency messages must have minimal timeouts
        assert QoSLevel.EMERGENCY.max_delay_ms <= 50  # 50ms max for emergency
        assert QoSLevel.CRITICAL.max_delay_ms <= 200  # 200ms max for critical safety
        assert QoSLevel.OPERATIONAL.max_delay_ms <= 1000  # 1s for operational
        assert QoSLevel.INFORMATIONAL.max_delay_ms <= 5000  # 5s for informational

    def test_agricultural_context_classification(self) -> None:
        """Test agricultural operation context classification."""
        # RED: Different agricultural contexts should affect message prioritization
        field_context = AgriculturalOperationContext.FIELD_CULTIVATION
        transport_context = AgriculturalOperationContext.TRANSPORT_MODE
        maintenance_context = AgriculturalOperationContext.MAINTENANCE_MODE

        assert field_context.priority_modifier > transport_context.priority_modifier
        assert transport_context.priority_modifier > maintenance_context.priority_modifier


class TestMessageClassificationSystem:
    """Test message classification for CAN bus traffic prioritization."""

    def test_emergency_message_classification(self) -> None:
        """Test emergency message classification for immediate processing."""
        # RED: Emergency messages must be classified with highest priority
        classifier = MessageClassification()

        emergency_message = {
            "pgn": 0xFECA,  # Emergency stop PGN
            "source": "TRACTOR_01",
            "data": b"\x01\x00\x00\x00\x00\x00\x00\x00",  # Emergency stop active
            "timestamp": datetime.now(UTC),
        }

        classification_result = classifier.classify_message(emergency_message)

        assert classification_result.qos_level == QoSLevel.EMERGENCY
        assert classification_result.requires_immediate_processing is True
        assert classification_result.can_be_throttled is False

    def test_safety_critical_message_classification(self) -> None:
        """Test safety-critical message classification for agricultural equipment."""
        # RED: Safety messages must have critical priority
        classifier = MessageClassification()

        safety_message = {
            "pgn": 0xF003,  # Electronic Engine Controller 2 (speed/position)
            "source": "TRACTOR_02",
            "data": b"\x64\x32\x00\x00\x00\x00\x00\x00",  # Speed data
            "timestamp": datetime.now(UTC),
        }

        classification_result = classifier.classify_message(safety_message)

        assert classification_result.qos_level == QoSLevel.CRITICAL
        assert classification_result.safety_related is True
        assert classification_result.throttling_sensitivity == "high"

    def test_operational_message_classification_by_context(self) -> None:
        """Test operational message classification varies by agricultural context."""
        # RED: GPS messages should have higher priority during field operations
        classifier = MessageClassification()

        gps_message = {
            "pgn": 0xF005,  # GPS position
            "source": "TRACTOR_03",
            "data": b"\x12\x34\x56\x78\x9A\xBC\xDE\xF0",
            "timestamp": datetime.now(UTC),
        }

        # Field operation context
        field_classification_result = classifier.classify_message(
            gps_message, context=AgriculturalOperationContext.FIELD_CULTIVATION
        )

        # Transport context
        transport_classification_result = classifier.classify_message(
            gps_message, context=AgriculturalOperationContext.TRANSPORT_MODE
        )

        assert (
            field_classification_result.effective_priority
            > transport_classification_result.effective_priority
        )
        assert field_classification_result.qos_level == QoSLevel.OPERATIONAL
        assert transport_classification_result.qos_level == QoSLevel.INFORMATIONAL


class TestAdvancedMessagePrioritizer:
    """Test the advanced message prioritization framework."""

    def test_prioritizer_initialization_with_agricultural_profiles(self) -> None:
        """Test prioritizer initialization with agricultural operation profiles."""
        # RED: Prioritizer must initialize with equipment-specific profiles
        prioritizer = AdvancedMessagePrioritizer(
            equipment_id="FIELD_CULTIVATOR_01",
            operation_profile="field_cultivation",
            fleet_coordination_enabled=True,
        )

        assert prioritizer.equipment_id == "FIELD_CULTIVATOR_01"
        assert prioritizer.operation_profile == "field_cultivation"
        assert prioritizer.fleet_coordination_enabled is True
        assert prioritizer.current_context == AgriculturalOperationContext.FIELD_CULTIVATION

    def test_message_prioritization_with_qos_framework(self) -> None:
        """Test message prioritization using QoS framework for agricultural operations."""
        # RED: Messages must be prioritized correctly based on QoS levels and context
        prioritizer = AdvancedMessagePrioritizer(
            equipment_id="TRACTOR_01", operation_profile="field_cultivation"
        )

        messages = [
            {
                "pgn": 0xF001,  # Engine RPM (informational)
                "source": "TRACTOR_01",
                "data": b"\x64\x00\x00\x00\x00\x00\x00\x00",
                "timestamp": datetime.now(UTC),
                "message_id": "msg_001",
            },
            {
                "pgn": 0xFECA,  # Emergency stop (emergency)
                "source": "TRACTOR_02",
                "data": b"\x01\x00\x00\x00\x00\x00\x00\x00",
                "timestamp": datetime.now(UTC),
                "message_id": "msg_002",
            },
            {
                "pgn": 0xF005,  # GPS position (operational in field context)
                "source": "TRACTOR_03",
                "data": b"\x12\x34\x56\x78\x9A\xBC\xDE\xF0",
                "timestamp": datetime.now(UTC),
                "message_id": "msg_003",
            },
        ]

        prioritized_messages = prioritizer.prioritize_message_batch(messages)

        # Emergency message should be first
        assert prioritized_messages[0].message_id == "msg_002"
        assert prioritized_messages[0].qos_level == QoSLevel.EMERGENCY

        # GPS (operational) should be second
        assert prioritized_messages[1].message_id == "msg_003"
        assert prioritized_messages[1].qos_level == QoSLevel.OPERATIONAL

        # Engine RPM (informational) should be last
        assert prioritized_messages[2].message_id == "msg_001"
        assert prioritized_messages[2].qos_level == QoSLevel.INFORMATIONAL

    def test_fleet_coordination_priority_boost(self) -> None:
        """Test priority boost for fleet coordination messages."""
        # RED: Fleet coordination messages should receive priority boost
        prioritizer = AdvancedMessagePrioritizer(
            equipment_id="TRACTOR_01",
            operation_profile="field_cultivation",
            fleet_coordination_enabled=True,
        )

        fleet_coordination_message = {
            "pgn": 0xEF00,  # Proprietary fleet coordination PGN
            "source": "FLEET_COORDINATOR",
            "data": b"\x01\x02\x03\x04\x05\x06\x07\x08",
            "timestamp": datetime.now(UTC),
            "fleet_coordination": True,
        }

        prioritized = prioritizer.prioritize_single_message(fleet_coordination_message)

        assert prioritized.fleet_coordination_boost is True
        assert prioritized.effective_priority > prioritized.base_priority

    def test_adaptive_throttling_decision_framework(self) -> None:
        """Test adaptive throttling decisions based on network conditions and QoS."""
        # RED: Throttling decisions must consider QoS levels and network state
        prioritizer = AdvancedMessagePrioritizer(
            equipment_id="TRACTOR_01", operation_profile="field_cultivation"
        )

        # Simulate high network congestion
        network_state = {
            "congestion_level": 0.8,  # 80% congestion
            "available_bandwidth": 125000,  # 125 kbps available
            "queue_depth": 150,
            "error_rate": 0.02,
        }

        high_priority_message = {
            "pgn": 0xFECA,  # Emergency stop
            "source": "TRACTOR_02",
            "data": b"\x01\x00\x00\x00\x00\x00\x00\x00",
            "timestamp": datetime.now(UTC),
        }

        low_priority_message = {
            "pgn": 0xF001,  # Engine RPM
            "source": "TRACTOR_01",
            "data": b"\x64\x00\x00\x00\x00\x00\x00\x00",
            "timestamp": datetime.now(UTC),
        }

        high_priority_decision = prioritizer.make_throttling_decision(
            high_priority_message, network_state
        )
        low_priority_decision = prioritizer.make_throttling_decision(
            low_priority_message, network_state
        )

        # Emergency messages should never be throttled
        assert high_priority_decision.should_throttle is False
        assert high_priority_decision.delay_ms == 0

        # Low priority messages should be throttled under congestion
        assert low_priority_decision.should_throttle is True
        assert low_priority_decision.delay_ms > 0

    def test_agricultural_operation_context_switching(self) -> None:
        """Test context switching between agricultural operations affects prioritization."""
        # RED: Context switching must dynamically adjust message priorities
        prioritizer = AdvancedMessagePrioritizer(
            equipment_id="TRACTOR_01", operation_profile="adaptive"
        )

        gps_message = {
            "pgn": 0xF005,  # GPS position
            "source": "TRACTOR_01",
            "data": b"\x12\x34\x56\x78\x9A\xBC\xDE\xF0",
            "timestamp": datetime.now(UTC),
        }

        # Set field cultivation context
        prioritizer.set_operation_context(AgriculturalOperationContext.FIELD_CULTIVATION)
        field_prioritization = prioritizer.prioritize_single_message(gps_message)

        # Switch to transport context
        prioritizer.set_operation_context(AgriculturalOperationContext.TRANSPORT_MODE)
        transport_prioritization = prioritizer.prioritize_single_message(gps_message)

        # GPS should have higher priority during field operations
        assert field_prioritization.effective_priority > transport_prioritization.effective_priority
        assert field_prioritization.qos_level == QoSLevel.OPERATIONAL
        assert transport_prioritization.qos_level == QoSLevel.INFORMATIONAL


class TestTrafficThrottlingDecisionFramework:
    """Test the traffic throttling decision framework for network optimization."""

    def test_throttling_decision_respects_qos_constraints(self) -> None:
        """Test that throttling decisions respect QoS level constraints."""
        # RED: Throttling must never violate QoS level maximum delays
        decision_framework = TrafficThrottlingDecision()

        emergency_message = Mock()
        emergency_message.qos_level = QoSLevel.EMERGENCY
        emergency_message.max_allowable_delay = 50

        critical_message = Mock()
        critical_message.qos_level = QoSLevel.CRITICAL
        critical_message.max_allowable_delay = 200

        # Under severe congestion
        severe_congestion = {"congestion_level": 0.95, "queue_depth": 300}

        emergency_decision = decision_framework.evaluate_throttling(
            emergency_message, severe_congestion
        )
        critical_decision = decision_framework.evaluate_throttling(
            critical_message, severe_congestion
        )

        # Emergency should never be throttled beyond QoS limits
        assert emergency_decision.delay_ms <= emergency_message.max_allowable_delay

        # Critical should respect QoS constraints even under congestion
        assert critical_decision.delay_ms <= critical_message.max_allowable_delay

    def test_adaptive_throttling_based_on_agricultural_patterns(self) -> None:
        """Test adaptive throttling based on agricultural operation patterns."""
        # RED: Throttling should adapt to agricultural work patterns and fleet coordination
        decision_framework = TrafficThrottlingDecision()

        # Simulate coordinated field operation with multiple tractors
        fleet_operation_state = {
            "active_tractors": 5,
            "coordination_mode": "synchronized_cultivation",
            "field_coverage_percentage": 0.45,
            "inter_tractor_spacing": 50.0,  # meters
        }

        coordination_message = Mock()
        coordination_message.qos_level = QoSLevel.OPERATIONAL
        coordination_message.fleet_coordination = True
        coordination_message.operation_context = AgriculturalOperationContext.FIELD_CULTIVATION

        decision = decision_framework.evaluate_throttling(
            coordination_message,
            network_state={"congestion_level": 0.6},
            agricultural_context=fleet_operation_state,
        )

        # Fleet coordination during active field work should have minimal throttling
        assert decision.agricultural_priority_boost is True
        assert decision.delay_ms < 500  # Should prioritize coordination messages


class TestMessagePrioritizationPerformance:
    """Test performance characteristics of the message prioritization system."""

    def test_prioritization_performance_under_high_message_volume(self) -> None:
        """Test prioritization performance with high message volumes typical in fleet operations."""
        # RED: System must handle high-volume message prioritization efficiently
        prioritizer = AdvancedMessagePrioritizer(
            equipment_id="FLEET_COORDINATOR", operation_profile="fleet_management"
        )

        # Generate large batch of messages simulating active fleet operations
        message_batch = []
        for i in range(1000):  # 1000 messages representing busy fleet
            message_batch.append(
                {
                    "pgn": 0xF005 + (i % 10),  # Varying PGNs
                    "source": f"TRACTOR_{i % 5}",  # 5 tractors
                    "data": bytes([i % 256] * 8),
                    "timestamp": datetime.now(UTC),
                    "message_id": f"msg_{i:04d}",
                }
            )

        # Measure prioritization performance
        start_time = datetime.now(UTC)
        prioritized_messages = prioritizer.prioritize_message_batch(message_batch)
        end_time = datetime.now(UTC)

        processing_time_ms = (end_time - start_time).total_seconds() * 1000

        # Must process 1000 messages in under 100ms for real-time performance
        assert processing_time_ms < 100
        assert len(prioritized_messages) == 1000
        assert all(isinstance(msg, PrioritizedMessage) for msg in prioritized_messages)

    def test_memory_efficiency_with_message_prioritization(self) -> None:
        """Test memory efficiency of prioritization framework during extended operations."""
        # RED: System must maintain memory efficiency during long-running operations
        prioritizer = AdvancedMessagePrioritizer(
            equipment_id="TRACTOR_01", operation_profile="field_cultivation"
        )

        # Simulate extended operation with message cleanup
        for batch_number in range(100):  # 100 batches
            batch_messages = []
            for i in range(50):  # 50 messages per batch
                batch_messages.append(
                    {
                        "pgn": 0xF001,
                        "source": "TRACTOR_01",
                        "data": b"\x64\x00\x00\x00\x00\x00\x00\x00",
                        "timestamp": datetime.now(UTC),
                        "message_id": f"batch_{batch_number}_msg_{i}",
                    }
                )

            prioritized = prioritizer.prioritize_message_batch(batch_messages)

            # Verify memory cleanup after processing
            assert len(prioritized) == 50

        # System should maintain stable memory usage
        memory_stats = prioritizer.get_memory_statistics()
        assert memory_stats["cached_classifications"] < 1000  # Reasonable cache size
        assert memory_stats["active_contexts"] <= 5  # Limited context retention
