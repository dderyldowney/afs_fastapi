"""
Test suite for CAN network congestion detection and adaptive traffic throttling.

Tests sophisticated congestion detection algorithms and adaptive throttling mechanisms
designed for agricultural fleet operations with real-time safety requirements.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from afs_fastapi.equipment.congestion_detection import (
    CongestionLevel,
    CongestionMetrics,
    NetworkCongestionDetector,
    ThrottleAction,
    TrafficThrottler,
)


class TestCongestionMetrics:
    """Test congestion metrics data structure."""

    def test_metrics_initialization(self) -> None:
        """Test congestion metrics initialization."""
        metrics = CongestionMetrics()

        assert metrics.bus_load_percentage == 0.0
        assert metrics.message_rate_per_second == 0.0
        assert metrics.error_rate_percentage == 0.0
        assert metrics.queue_depth == 0
        assert metrics.average_latency_ms == 0.0
        assert metrics.peak_latency_ms == 0.0
        assert isinstance(metrics.timestamp, datetime)

    def test_metrics_update(self) -> None:
        """Test updating congestion metrics."""
        metrics = CongestionMetrics()

        metrics.update_metrics(
            bus_load=75.5,
            message_rate=250.0,
            error_rate=2.5,
            queue_depth=45,
            avg_latency=15.2,
            peak_latency=35.7,
        )

        assert metrics.bus_load_percentage == 75.5
        assert metrics.message_rate_per_second == 250.0
        assert metrics.error_rate_percentage == 2.5
        assert metrics.queue_depth == 45
        assert metrics.average_latency_ms == 15.2
        assert metrics.peak_latency_ms == 35.7

    def test_congestion_score_calculation(self) -> None:
        """Test congestion score calculation algorithm."""
        metrics = CongestionMetrics()

        # Low congestion scenario
        metrics.update_metrics(
            bus_load=25.0,
            message_rate=100.0,
            error_rate=0.1,
            queue_depth=5,
            avg_latency=5.0,
            peak_latency=10.0,
        )

        score = metrics.calculate_congestion_score()
        assert 0.0 <= score <= 0.3  # Low congestion

        # High congestion scenario
        metrics.update_metrics(
            bus_load=85.0,
            message_rate=800.0,
            error_rate=5.0,
            queue_depth=200,
            avg_latency=45.0,
            peak_latency=120.0,
        )

        score = metrics.calculate_congestion_score()
        assert 0.7 <= score <= 1.0  # High congestion


class TestNetworkCongestionDetector:
    """Test network congestion detection system."""

    @pytest.fixture
    def detector(self) -> NetworkCongestionDetector:
        """Create congestion detector."""
        return NetworkCongestionDetector(
            monitoring_interval=0.1, history_window_size=5  # Fast for testing
        )

    def test_detector_initialization(self, detector: NetworkCongestionDetector) -> None:
        """Test detector initialization."""
        assert detector.monitoring_interval == 0.1
        assert detector.history_window_size == 5
        assert len(detector.metrics_history) == 0
        assert detector.current_congestion_level == CongestionLevel.NORMAL

    @pytest.mark.asyncio
    async def test_metrics_collection(self, detector: NetworkCongestionDetector) -> None:
        """Test real-time metrics collection."""
        # Mock interface status data
        mock_status = MagicMock()
        mock_status.bus_load_percentage = 60.0
        mock_status.errors_total = 25
        mock_status.messages_sent = 1000
        mock_status.messages_received = 1500

        # Mock message queue depth
        with patch.object(detector, "_get_queue_depth", return_value=30):
            with patch.object(detector, "_measure_latency", return_value=(12.5, 28.0)):
                metrics = await detector._collect_metrics({"can0": mock_status})

        assert metrics.bus_load_percentage == 60.0
        assert metrics.error_rate_percentage == 1.0  # 25/(1000+1500) * 100
        assert metrics.queue_depth == 30
        assert metrics.average_latency_ms == 12.5
        assert metrics.peak_latency_ms == 28.0

    def test_congestion_level_classification(self, detector: NetworkCongestionDetector) -> None:
        """Test congestion level classification."""
        # Test normal level
        normal_score = 0.25
        level = detector._classify_congestion_level(normal_score)
        assert level == CongestionLevel.NORMAL

        # Test moderate level
        moderate_score = 0.55
        level = detector._classify_congestion_level(moderate_score)
        assert level == CongestionLevel.MODERATE

        # Test high level
        high_score = 0.75
        level = detector._classify_congestion_level(high_score)
        assert level == CongestionLevel.HIGH

        # Test critical level
        critical_score = 0.95
        level = detector._classify_congestion_level(critical_score)
        assert level == CongestionLevel.CRITICAL

    def test_trending_analysis(self, detector: NetworkCongestionDetector) -> None:
        """Test congestion trending analysis."""
        # Add metrics with increasing congestion
        timestamps = [datetime.now() - timedelta(seconds=i * 10) for i in range(5, 0, -1)]
        scores = [0.2, 0.35, 0.5, 0.7, 0.85]  # Increasing trend

        for timestamp, score in zip(timestamps, scores, strict=False):
            metrics = CongestionMetrics()
            metrics.timestamp = timestamp
            metrics.bus_load_percentage = score * 100
            detector.metrics_history.append(metrics)

        trend = detector._analyze_congestion_trend()
        assert trend == "increasing"

        # Test stable trend
        detector.metrics_history.clear()
        stable_scores = [0.5, 0.52, 0.48, 0.51, 0.49]
        for timestamp, score in zip(timestamps, stable_scores, strict=False):
            metrics = CongestionMetrics()
            metrics.timestamp = timestamp
            metrics.bus_load_percentage = score * 100
            detector.metrics_history.append(metrics)

        trend = detector._analyze_congestion_trend()
        assert trend == "stable"

    @pytest.mark.asyncio
    async def test_congestion_prediction(self, detector: NetworkCongestionDetector) -> None:
        """Test congestion prediction algorithm."""
        # Setup historical data with clear pattern
        current_time = datetime.now()
        for i in range(10):
            metrics = CongestionMetrics()
            metrics.timestamp = current_time - timedelta(seconds=i * 10)
            metrics.bus_load_percentage = 30.0 + (i * 5.0)  # Linear increase
            detector.metrics_history.append(metrics)

        prediction = await detector._predict_congestion(time_horizon_seconds=60)

        assert prediction["predicted_level"] in [level.value for level in CongestionLevel]
        assert "confidence" in prediction
        assert "estimated_time_to_critical" in prediction
        assert 0.0 <= prediction["confidence"] <= 1.0


class TestTrafficThrottler:
    """Test adaptive traffic throttling system."""

    @pytest.fixture
    def throttler(self) -> TrafficThrottler:
        """Create traffic throttler."""
        return TrafficThrottler(enable_adaptive_throttling=True, safety_margin_percentage=15.0)

    def test_throttler_initialization(self, throttler: TrafficThrottler) -> None:
        """Test throttler initialization."""
        assert throttler.enable_adaptive_throttling is True
        assert throttler.safety_margin_percentage == 15.0
        assert len(throttler.active_throttles) == 0

    def test_throttle_decision_normal_conditions(self, throttler: TrafficThrottler) -> None:
        """Test throttle decisions under normal conditions."""
        metrics = CongestionMetrics()
        metrics.update_metrics(
            bus_load=25.0,
            message_rate=150.0,
            error_rate=0.2,
            queue_depth=10,
            avg_latency=5.0,
            peak_latency=12.0,
        )

        decision = throttler.make_throttle_decision(metrics, CongestionLevel.NORMAL)

        assert decision.action == ThrottleAction.NONE
        assert decision.severity_factor == 1.0
        assert decision.affected_priorities == []

    def test_throttle_decision_moderate_congestion(self, throttler: TrafficThrottler) -> None:
        """Test throttle decisions under moderate congestion."""
        metrics = CongestionMetrics()
        metrics.update_metrics(
            bus_load=65.0,
            message_rate=500.0,
            error_rate=3.0,
            queue_depth=80,
            avg_latency=25.0,
            peak_latency=60.0,
        )

        decision = throttler.make_throttle_decision(metrics, CongestionLevel.MODERATE)

        assert decision.action == ThrottleAction.REDUCE_LOW_PRIORITY
        assert 0.7 <= decision.severity_factor <= 0.9
        assert "LOW" in decision.affected_priorities

    def test_throttle_decision_high_congestion(self, throttler: TrafficThrottler) -> None:
        """Test throttle decisions under high congestion."""
        metrics = CongestionMetrics()
        metrics.update_metrics(
            bus_load=80.0,
            message_rate=750.0,
            error_rate=8.0,
            queue_depth=150,
            avg_latency=45.0,
            peak_latency=100.0,
        )

        decision = throttler.make_throttle_decision(metrics, CongestionLevel.HIGH)

        assert decision.action == ThrottleAction.REDUCE_NORMAL_PRIORITY
        assert 0.4 <= decision.severity_factor <= 0.7
        assert "NORMAL" in decision.affected_priorities

    def test_throttle_decision_critical_congestion(self, throttler: TrafficThrottler) -> None:
        """Test throttle decisions under critical congestion."""
        metrics = CongestionMetrics()
        metrics.update_metrics(
            bus_load=95.0,
            message_rate=950.0,
            error_rate=15.0,
            queue_depth=300,
            avg_latency=80.0,
            peak_latency=200.0,
        )

        decision = throttler.make_throttle_decision(metrics, CongestionLevel.CRITICAL)

        assert decision.action == ThrottleAction.EMERGENCY_THROTTLE
        assert 0.1 <= decision.severity_factor <= 0.4
        assert "HIGH" in decision.affected_priorities
        assert decision.emergency_mode is True

    def test_agricultural_operation_context(self, throttler: TrafficThrottler) -> None:
        """Test throttling considers agricultural operation context."""
        metrics = CongestionMetrics()
        metrics.update_metrics(
            bus_load=70.0,
            message_rate=600.0,
            error_rate=4.0,
            queue_depth=100,
            avg_latency=30.0,
            peak_latency=75.0,
        )

        # Field operations - more conservative throttling to preserve safety
        field_decision = throttler.make_throttle_decision(
            metrics, CongestionLevel.MODERATE, operation_context="field_operation"
        )

        # Transport operations - more aggressive throttling allowed
        transport_decision = throttler.make_throttle_decision(
            metrics, CongestionLevel.MODERATE, operation_context="transport"
        )

        # Field operations should have more conservative throttling
        assert field_decision.severity_factor >= transport_decision.severity_factor

    @pytest.mark.asyncio
    async def test_adaptive_throttle_adjustment(self, throttler: TrafficThrottler) -> None:
        """Test adaptive throttle adjustment over time."""
        # Start with moderate congestion
        metrics = CongestionMetrics()
        metrics.update_metrics(
            bus_load=65.0,
            message_rate=500.0,
            error_rate=3.0,
            queue_depth=80,
            avg_latency=25.0,
            peak_latency=60.0,
        )

        initial_decision = throttler.make_throttle_decision(metrics, CongestionLevel.MODERATE)
        await throttler.apply_throttle_decision(initial_decision)

        # Simulate congestion worsening
        metrics.update_metrics(
            bus_load=80.0,
            message_rate=750.0,
            error_rate=8.0,
            queue_depth=150,
            avg_latency=45.0,
            peak_latency=100.0,
        )

        adjusted_decision = throttler.make_throttle_decision(metrics, CongestionLevel.HIGH)

        # Should escalate throttling
        assert adjusted_decision.action.value > initial_decision.action.value
        assert adjusted_decision.severity_factor < initial_decision.severity_factor

    def test_throttle_recovery(self, throttler: TrafficThrottler) -> None:
        """Test throttle recovery when congestion decreases."""
        # Apply some throttling first
        throttler.active_throttles = ["LOW", "NORMAL"]

        # Congestion returns to normal
        metrics = CongestionMetrics()
        metrics.update_metrics(
            bus_load=30.0,
            message_rate=200.0,
            error_rate=0.5,
            queue_depth=15,
            avg_latency=8.0,
            peak_latency=20.0,
        )

        decision = throttler.make_throttle_decision(metrics, CongestionLevel.NORMAL)

        assert decision.action == ThrottleAction.RESTORE_NORMAL
        assert decision.recovery_mode is True


class TestIntegratedCongestionManagement:
    """Test integrated congestion detection and throttling."""

    @pytest.mark.asyncio
    async def test_complete_congestion_workflow(self) -> None:
        """Test complete congestion detection and response workflow."""
        detector = NetworkCongestionDetector(monitoring_interval=0.1)
        throttler = TrafficThrottler(enable_adaptive_throttling=True)

        # Simulate interface status indicating high load
        mock_status = MagicMock()
        mock_status.bus_load_percentage = 85.0
        mock_status.errors_total = 50
        mock_status.messages_sent = 1000
        mock_status.messages_received = 1500

        # Mock supporting methods
        with patch.object(detector, "_get_queue_depth", return_value=120):
            with patch.object(detector, "_measure_latency", return_value=(35.0, 85.0)):
                metrics = await detector._collect_metrics({"can0": mock_status})

        # Detect congestion level
        congestion_score = metrics.calculate_congestion_score()
        congestion_level = detector._classify_congestion_level(congestion_score)

        # Make throttling decision
        decision = throttler.make_throttle_decision(metrics, congestion_level)

        # Verify appropriate response
        assert congestion_level in [CongestionLevel.HIGH, CongestionLevel.CRITICAL]
        assert decision.action != ThrottleAction.NONE
        assert decision.severity_factor < 1.0

    @pytest.mark.asyncio
    async def test_agricultural_safety_preservation(self) -> None:
        """Test that safety-critical messages are preserved during throttling."""
        throttler = TrafficThrottler(enable_adaptive_throttling=True)

        # Critical congestion scenario
        metrics = CongestionMetrics()
        metrics.update_metrics(
            bus_load=90.0,
            message_rate=900.0,
            error_rate=12.0,
            queue_depth=250,
            avg_latency=70.0,
            peak_latency=180.0,
        )

        decision = throttler.make_throttle_decision(metrics, CongestionLevel.CRITICAL)

        # Safety-critical messages should never be throttled
        assert "CRITICAL" not in decision.affected_priorities
        assert decision.preserve_safety_messages is True

    @pytest.mark.asyncio
    async def test_field_vs_transport_operation_handling(self) -> None:
        """Test different handling for field vs transport operations."""
        throttler = TrafficThrottler(enable_adaptive_throttling=True)

        # Moderate congestion scenario
        metrics = CongestionMetrics()
        metrics.update_metrics(
            bus_load=65.0,
            message_rate=500.0,
            error_rate=3.5,
            queue_depth=85,
            avg_latency=28.0,
            peak_latency=65.0,
        )

        # Field operation - higher precision requirements
        field_decision = throttler.make_throttle_decision(
            metrics, CongestionLevel.MODERATE, operation_context="field_operation"
        )

        # Transport operation - can tolerate more latency
        transport_decision = throttler.make_throttle_decision(
            metrics, CongestionLevel.MODERATE, operation_context="transport"
        )

        # Field operations should be more conservative with throttling
        assert field_decision.severity_factor >= transport_decision.severity_factor

        # Field operations might have different priority handling
        if field_decision.affected_priorities and transport_decision.affected_priorities:
            # Field should preserve more priority levels
            assert len(field_decision.affected_priorities) <= len(
                transport_decision.affected_priorities
            )
