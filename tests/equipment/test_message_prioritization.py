"""
Test message prioritization system for CAN traffic management.

This module tests comprehensive message prioritization, traffic management,
and network optimization for high-throughput agricultural ISOBUS operations.

Implementation follows Test-First Development (TDD) RED phase.
"""

from __future__ import annotations

from datetime import datetime

from afs_fastapi.equipment.farm_tractors import ISOBUSMessage
from afs_fastapi.equipment.message_prioritization import (
    BandwidthManager,
    CongestionController,
    MessageScheduler,
    NetworkOptimizer,
    PriorityQueue,
    TrafficAnalyzer,
    TrafficClass,
    TrafficShaper,
)
from afs_fastapi.equipment.reliable_isobus import ISOBUSPriority


class TestTrafficClassification:
    """Test traffic classification for agricultural message prioritization."""

    def test_traffic_class_initialization(self) -> None:
        """Test traffic class creation with agricultural parameters."""
        # RED: Test agricultural traffic class definition

        emergency_class = TrafficClass(
            class_id="EMERGENCY_SAFETY",
            priority_level=0,
            max_bandwidth_percentage=50.0,  # Reserve 50% for emergency
            guaranteed_bandwidth_kbps=64.0,  # Guarantee 64 Kbps
            max_latency_ms=10.0,  # 10ms max latency
            max_jitter_ms=2.0,  # 2ms max jitter
            description="Emergency stop and safety-critical messages",
        )

        assert emergency_class.class_id == "EMERGENCY_SAFETY"
        assert emergency_class.priority_level == 0
        assert emergency_class.max_bandwidth_percentage == 50.0
        assert emergency_class.guaranteed_bandwidth_kbps == 64.0
        assert emergency_class.max_latency_ms == 10.0

    def test_agricultural_traffic_classes(self) -> None:
        """Test comprehensive agricultural traffic class definitions."""
        # RED: Test complete set of agricultural traffic classes

        traffic_analyzer = TrafficAnalyzer()

        # Create all agricultural traffic classes
        classes = traffic_analyzer.get_default_agricultural_classes()

        # Should have classes for all agricultural scenarios
        expected_classes = {
            "EMERGENCY_SAFETY",
            "COLLISION_AVOIDANCE",
            "FIELD_COORDINATION",
            "IMPLEMENT_CONTROL",
            "TELEMETRY_STREAMING",
            "STATUS_UPDATES",
            "DIAGNOSTICS",
            "BEST_EFFORT",
        }

        actual_classes = {cls.class_id for cls in classes}
        assert actual_classes == expected_classes

        # Verify priority ordering (lower number = higher priority)
        priorities = [cls.priority_level for cls in classes]
        assert priorities == sorted(priorities)  # Should be in ascending order

    def test_message_classification(self) -> None:
        """Test automatic message classification based on content."""
        # RED: Test automatic classification of ISOBUS messages

        traffic_analyzer = TrafficAnalyzer()

        # Emergency stop message
        emergency_msg = ISOBUSMessage(
            pgn=0xE001,  # Emergency PGN
            source_address=0x23,
            destination_address=0xFF,
            data=b"\x01\x00\x00\x00",  # Emergency stop command
            timestamp=datetime.now(),
        )

        classification = traffic_analyzer.classify_message(emergency_msg)
        assert classification.traffic_class.class_id == "EMERGENCY_SAFETY"
        assert classification.confidence_score >= 0.95

        # Regular telemetry message
        telemetry_msg = ISOBUSMessage(
            pgn=0xE004,  # Telemetry PGN
            source_address=0x23,
            destination_address=0x25,
            data=b"\x12\x34\x56\x78",
            timestamp=datetime.now(),
        )

        classification = traffic_analyzer.classify_message(telemetry_msg)
        assert classification.traffic_class.class_id == "TELEMETRY_STREAMING"
        assert classification.confidence_score >= 0.80


class TestPriorityQueue:
    """Test priority queue implementation for message scheduling."""

    def test_priority_queue_initialization(self) -> None:
        """Test priority queue setup for agricultural message handling."""
        # RED: Test priority queue configuration

        priority_queue = PriorityQueue(
            max_queue_size=1000,
            priority_levels=8,
            aging_enabled=True,
            aging_factor=0.1,
        )

        assert priority_queue.max_queue_size == 1000
        assert priority_queue.priority_levels == 8
        assert priority_queue.aging_enabled is True
        assert priority_queue.current_size == 0

    def test_message_enqueue_by_priority(self) -> None:
        """Test message enqueueing with priority ordering."""
        # RED: Test priority-based message ordering

        priority_queue = PriorityQueue()

        # Create messages with different priorities
        emergency_msg = ISOBUSMessage(
            pgn=0xE001,
            source_address=0x23,
            destination_address=0xFF,
            data=b"\x01",
            timestamp=datetime.now(),
        )

        telemetry_msg = ISOBUSMessage(
            pgn=0xE004,
            source_address=0x23,
            destination_address=0x25,
            data=b"\x02",
            timestamp=datetime.now(),
        )

        diagnostics_msg = ISOBUSMessage(
            pgn=0xE006,
            source_address=0x23,
            destination_address=0x25,
            data=b"\x03",
            timestamp=datetime.now(),
        )

        # Enqueue in non-priority order
        priority_queue.enqueue(telemetry_msg, priority=ISOBUSPriority.STATUS_UPDATE)
        priority_queue.enqueue(emergency_msg, priority=ISOBUSPriority.EMERGENCY_STOP)
        priority_queue.enqueue(diagnostics_msg, priority=ISOBUSPriority.DIAGNOSTICS)

        # Should dequeue in priority order
        first_msg = priority_queue.dequeue()
        assert first_msg is not None
        assert first_msg.pgn == 0xE001  # Emergency message first

        second_msg = priority_queue.dequeue()
        assert second_msg is not None
        assert second_msg.pgn == 0xE004  # Telemetry second

        third_msg = priority_queue.dequeue()
        assert third_msg is not None
        assert third_msg.pgn == 0xE006  # Diagnostics last

    def test_queue_overflow_handling(self) -> None:
        """Test queue overflow protection for high-traffic scenarios."""
        # RED: Test queue overflow behavior

        priority_queue = PriorityQueue(max_queue_size=3)

        # Fill queue to capacity
        for i in range(3):
            msg = ISOBUSMessage(
                pgn=0xE004,
                source_address=0x23,
                destination_address=0x25,
                data=bytes([i]),
                timestamp=datetime.now(),
            )
            result = priority_queue.enqueue(msg, priority=ISOBUSPriority.STATUS_UPDATE)
            assert result is True

        # Queue should be full
        assert priority_queue.is_full() is True

        # Adding another message should fail
        overflow_msg = ISOBUSMessage(
            pgn=0xE004,
            source_address=0x23,
            destination_address=0x25,
            data=b"\xFF",
            timestamp=datetime.now(),
        )
        result = priority_queue.enqueue(overflow_msg, priority=ISOBUSPriority.STATUS_UPDATE)
        assert result is False

    def test_priority_aging_mechanism(self) -> None:
        """Test priority aging to prevent starvation."""
        # RED: Test message aging for fairness

        priority_queue = PriorityQueue(aging_enabled=True, aging_factor=0.1)

        # Add low-priority message
        old_msg = ISOBUSMessage(
            pgn=0xE006,
            source_address=0x23,
            destination_address=0x25,
            data=b"\x01",
            timestamp=datetime.now(),
        )
        priority_queue.enqueue(old_msg, priority=ISOBUSPriority.DIAGNOSTICS)

        # Simulate aging process
        for _ in range(10):
            priority_queue.age_messages()

        # Aged message should have improved priority
        aged_priority = priority_queue.get_effective_priority(old_msg)
        assert aged_priority < ISOBUSPriority.DIAGNOSTICS


class TestTrafficShaper:
    """Test traffic shaping for bandwidth management."""

    def test_traffic_shaper_initialization(self) -> None:
        """Test traffic shaper setup for agricultural CAN networks."""
        # RED: Test traffic shaper configuration

        shaper = TrafficShaper(
            total_bandwidth_kbps=500.0,  # 500 Kbps CAN network
            shaping_algorithm="token_bucket",
            burst_size_bytes=1024,
            measurement_window_ms=100,
        )

        assert shaper.total_bandwidth_kbps == 500.0
        assert shaper.shaping_algorithm == "token_bucket"
        assert shaper.burst_size_bytes == 1024
        assert shaper.measurement_window_ms == 100

    def test_bandwidth_allocation_by_class(self) -> None:
        """Test bandwidth allocation across traffic classes."""
        # RED: Test proportional bandwidth allocation

        shaper = TrafficShaper(total_bandwidth_kbps=500.0)

        # Define bandwidth allocation percentages
        allocations = {
            "EMERGENCY_SAFETY": 30.0,  # 150 Kbps
            "COLLISION_AVOIDANCE": 20.0,  # 100 Kbps
            "FIELD_COORDINATION": 20.0,  # 100 Kbps
            "IMPLEMENT_CONTROL": 15.0,  # 75 Kbps
            "TELEMETRY_STREAMING": 10.0,  # 50 Kbps
            "STATUS_UPDATES": 3.0,  # 15 Kbps
            "DIAGNOSTICS": 2.0,  # 10 Kbps
        }

        shaper.configure_class_allocations(allocations)

        # Verify allocations
        emergency_bandwidth = shaper.get_allocated_bandwidth("EMERGENCY_SAFETY")
        assert emergency_bandwidth == 150.0

        telemetry_bandwidth = shaper.get_allocated_bandwidth("TELEMETRY_STREAMING")
        assert telemetry_bandwidth == 50.0

    def test_token_bucket_algorithm(self) -> None:
        """Test token bucket traffic shaping algorithm."""
        # RED: Test token bucket implementation

        shaper = TrafficShaper(
            total_bandwidth_kbps=100.0,
            shaping_algorithm="token_bucket",
            burst_size_bytes=1024,
        )

        # Should allow messages within rate limit
        message_size = 64  # 64 byte message
        for _ in range(10):  # Send 10 messages
            can_send = shaper.can_send_message("TELEMETRY_STREAMING", message_size)
            assert can_send is True
            shaper.consume_tokens("TELEMETRY_STREAMING", message_size)

        # After burst, should be rate limited
        large_message_size = 2048  # 2KB message
        can_send_large = shaper.can_send_message("TELEMETRY_STREAMING", large_message_size)
        assert can_send_large is False


class TestCongestionController:
    """Test congestion control for network optimization."""

    def test_congestion_detection(self) -> None:
        """Test congestion detection mechanisms."""
        # RED: Test network congestion detection

        controller = CongestionController(
            congestion_threshold=0.8,  # 80% utilization threshold
            measurement_window_seconds=1.0,
            backoff_strategy="exponential",
        )

        # Simulate high network utilization
        for _ in range(100):
            controller.record_message_transmission(
                message_size=64,
                transmission_time_ms=5.0,
                queue_depth=50,
            )

        congestion_level = controller.get_congestion_level()
        assert congestion_level > 0.8  # Should detect congestion

        is_congested = controller.is_network_congested()
        assert is_congested is True

    def test_congestion_response_actions(self) -> None:
        """Test congestion response mechanisms."""
        # RED: Test congestion mitigation strategies

        controller = CongestionController()

        # Trigger congestion state
        controller.set_congestion_state(True)

        # Should implement backoff for non-critical traffic
        backoff_factor = controller.get_backoff_factor("DIAGNOSTICS")
        assert backoff_factor > 1.0  # Should delay non-critical messages

        # Should not affect emergency traffic
        emergency_backoff = controller.get_backoff_factor("EMERGENCY_SAFETY")
        assert emergency_backoff == 1.0  # No delay for emergency

    def test_adaptive_rate_control(self) -> None:
        """Test adaptive transmission rate control."""
        # RED: Test dynamic rate adjustment

        controller = CongestionController()

        # Under normal conditions
        normal_rate = controller.get_transmission_rate("TELEMETRY_STREAMING")
        assert normal_rate == 1.0  # Full rate

        # Under congestion
        controller.set_congestion_state(True)
        congested_rate = controller.get_transmission_rate("TELEMETRY_STREAMING")
        assert congested_rate < 1.0  # Reduced rate


class TestBandwidthManager:
    """Test bandwidth management for agricultural operations."""

    def test_bandwidth_monitoring(self) -> None:
        """Test real-time bandwidth utilization monitoring."""
        # RED: Test bandwidth measurement and tracking

        manager = BandwidthManager(
            total_bandwidth_kbps=500.0,
            monitoring_interval_ms=100,
        )

        # Simulate message transmissions
        manager.record_transmission(
            traffic_class="TELEMETRY_STREAMING",
            message_size_bytes=64,
            transmission_time_ms=1.0,
        )

        utilization = manager.get_current_utilization()
        assert 0.0 <= utilization <= 1.0

        class_utilization = manager.get_class_utilization("TELEMETRY_STREAMING")
        assert class_utilization > 0.0

    def test_bandwidth_reservation(self) -> None:
        """Test bandwidth reservation for critical traffic."""
        # RED: Test guaranteed bandwidth allocation

        manager = BandwidthManager(total_bandwidth_kbps=500.0)

        # Reserve bandwidth for emergency traffic
        reservation_success = manager.reserve_bandwidth(
            traffic_class="EMERGENCY_SAFETY",
            reserved_kbps=100.0,
            priority=0,
        )

        assert reservation_success is True

        # Check available bandwidth
        available = manager.get_available_bandwidth()
        assert available == 400.0  # 500 - 100 reserved

        # Verify reservation is active
        reservations = manager.get_active_reservations()
        assert "EMERGENCY_SAFETY" in reservations
        assert reservations["EMERGENCY_SAFETY"]["reserved_kbps"] == 100.0


class TestMessageScheduler:
    """Test message scheduling for optimized delivery."""

    def test_scheduler_initialization(self) -> None:
        """Test message scheduler setup for agricultural operations."""
        # RED: Test scheduler configuration

        scheduler = MessageScheduler(
            scheduling_algorithm="weighted_fair_queuing",
            max_pending_messages=1000,
            enable_preemption=True,
        )

        assert scheduler.scheduling_algorithm == "weighted_fair_queuing"
        assert scheduler.max_pending_messages == 1000
        assert scheduler.enable_preemption is True

    def test_weighted_fair_queuing(self) -> None:
        """Test weighted fair queuing algorithm."""
        # RED: Test WFQ implementation

        scheduler = MessageScheduler(scheduling_algorithm="weighted_fair_queuing")

        # Configure class weights
        weights = {
            "EMERGENCY_SAFETY": 40,
            "COLLISION_AVOIDANCE": 30,
            "FIELD_COORDINATION": 20,
            "TELEMETRY_STREAMING": 10,
        }
        scheduler.configure_class_weights(weights)

        # Schedule messages from different classes
        for class_id in weights.keys():
            for i in range(5):  # 5 messages per class
                msg = ISOBUSMessage(
                    pgn=0xE000 + i,
                    source_address=0x23,
                    destination_address=0x25,
                    data=bytes([i]),
                    timestamp=datetime.now(),
                )
                scheduler.schedule_message(msg, traffic_class=class_id)

        # Verify scheduling respects weights
        scheduled_counts: dict[str, int] = {}
        for _ in range(10):  # Schedule 10 messages
            next_msg, returned_class_id = scheduler.get_next_scheduled_message()
            if next_msg and returned_class_id is not None:
                scheduled_counts[returned_class_id] = scheduled_counts.get(returned_class_id, 0) + 1

        # Emergency should get most scheduling opportunities
        assert scheduled_counts.get("EMERGENCY_SAFETY", 0) >= scheduled_counts.get(
            "TELEMETRY_STREAMING", 0
        )

    def test_preemptive_scheduling(self) -> None:
        """Test preemptive scheduling for urgent messages."""
        # RED: Test message preemption capabilities

        scheduler = MessageScheduler(enable_preemption=True)

        # Schedule low-priority message
        low_priority_msg = ISOBUSMessage(
            pgn=0xE006,
            source_address=0x23,
            destination_address=0x25,
            data=b"\x01",
            timestamp=datetime.now(),
        )
        scheduler.schedule_message(low_priority_msg, traffic_class="DIAGNOSTICS")

        # Schedule high-priority message (should preempt)
        emergency_msg = ISOBUSMessage(
            pgn=0xE001,
            source_address=0x23,
            destination_address=0xFF,
            data=b"\x02",
            timestamp=datetime.now(),
        )
        preempted = scheduler.schedule_message(
            emergency_msg, traffic_class="EMERGENCY_SAFETY", preempt_lower_priority=True
        )

        assert preempted is True

        # Emergency message should be scheduled first
        next_msg, class_id = scheduler.get_next_scheduled_message()
        assert next_msg is not None
        assert next_msg.pgn == 0xE001  # Emergency message
        assert class_id == "EMERGENCY_SAFETY"


class TestNetworkOptimizer:
    """Test network optimization for agricultural efficiency."""

    def test_network_optimization_analysis(self) -> None:
        """Test network performance analysis and optimization."""
        # RED: Test network optimization recommendations

        optimizer = NetworkOptimizer(
            target_utilization=0.75,  # 75% target utilization
            optimization_interval_seconds=60,
        )

        # Provide network statistics
        stats = {
            "total_messages": 1000,
            "average_latency_ms": 15.0,
            "packet_loss_rate": 0.02,
            "utilization_percentage": 85.0,  # Over target
            "congestion_events": 5,
        }

        optimizer.update_network_statistics(stats)

        # Get optimization recommendations
        recommendations = optimizer.get_optimization_recommendations()

        assert len(recommendations) > 0
        assert any("bandwidth" in rec.lower() for rec in recommendations)
        assert any("priority" in rec.lower() for rec in recommendations)

    def test_dynamic_parameter_adjustment(self) -> None:
        """Test dynamic adjustment of network parameters."""
        # RED: Test adaptive parameter tuning

        optimizer = NetworkOptimizer()

        # Simulate network conditions requiring adjustment
        optimizer.analyze_traffic_patterns(
            {
                "emergency_percentage": 5.0,
                "telemetry_percentage": 60.0,
                "diagnostics_percentage": 30.0,
                "peak_hour_multiplier": 2.5,
            }
        )

        # Should recommend parameter adjustments
        adjustments = optimizer.get_parameter_adjustments()

        assert "priority_weights" in adjustments
        assert "bandwidth_allocation" in adjustments
        assert "congestion_threshold" in adjustments

        # Verify adjustments are reasonable
        priority_weights = adjustments["priority_weights"]
        assert priority_weights["EMERGENCY_SAFETY"] > priority_weights["DIAGNOSTICS"]
