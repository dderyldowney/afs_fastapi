"""
CAN network congestion detection and adaptive traffic throttling for agricultural operations.

This module provides sophisticated congestion detection algorithms and adaptive throttling
mechanisms designed for real-world agricultural fleet operations with safety-critical
messaging requirements and variable operational contexts.

Implementation follows Test-First Development (TDD) RED-GREEN-REFACTOR cycle.
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np

# Configure logging for congestion detection
logger = logging.getLogger(__name__)


class CongestionLevel(Enum):
    """Network congestion severity levels for agricultural CAN networks."""

    NORMAL = "normal"  # < 40% capacity utilization
    MODERATE = "moderate"  # 40-60% capacity utilization
    HIGH = "high"  # 60-80% capacity utilization
    CRITICAL = "critical"  # > 80% capacity utilization


class ThrottleAction(Enum):
    """Traffic throttling actions for congestion management."""

    NONE = 0  # No throttling needed
    REDUCE_LOW_PRIORITY = 1  # Throttle low priority messages
    REDUCE_NORMAL_PRIORITY = 2  # Throttle normal priority messages
    REDUCE_HIGH_PRIORITY = 3  # Throttle high priority messages (extreme)
    EMERGENCY_THROTTLE = 4  # Emergency throttling mode
    RESTORE_NORMAL = 5  # Restore normal traffic flow


@dataclass
class CongestionMetrics:
    """Real-time congestion metrics for CAN network monitoring."""

    bus_load_percentage: float = 0.0
    message_rate_per_second: float = 0.0
    error_rate_percentage: float = 0.0
    queue_depth: int = 0
    average_latency_ms: float = 0.0
    peak_latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def update_metrics(
        self,
        bus_load: float,
        message_rate: float,
        error_rate: float,
        queue_depth: int,
        avg_latency: float,
        peak_latency: float,
    ) -> None:
        """Update all congestion metrics.

        Parameters
        ----------
        bus_load : float
            Bus load percentage (0-100)
        message_rate : float
            Messages per second
        error_rate : float
            Error rate percentage (0-100)
        queue_depth : int
            Current message queue depth
        avg_latency : float
            Average message latency in milliseconds
        peak_latency : float
            Peak message latency in milliseconds
        """
        self.bus_load_percentage = bus_load
        self.message_rate_per_second = message_rate
        self.error_rate_percentage = error_rate
        self.queue_depth = queue_depth
        self.average_latency_ms = avg_latency
        self.peak_latency_ms = peak_latency
        self.timestamp = datetime.now()

    def calculate_congestion_score(self) -> float:
        """Calculate overall congestion score (0.0 to 1.0).

        Returns
        -------
        float
            Congestion score where 0.0 = no congestion, 1.0 = critical congestion
        """
        # Weighted scoring algorithm for agricultural CAN networks
        weights = {
            "bus_load": 0.35,  # Bus utilization is primary indicator
            "message_rate": 0.15,  # Message frequency impact
            "error_rate": 0.25,  # Errors indicate network stress
            "queue_depth": 0.15,  # Queue backlog indicator
            "latency": 0.10,  # Latency impact on real-time operations
        }

        # Normalize metrics to 0-1 scale with more aggressive scaling
        bus_load_score = min(self.bus_load_percentage / 90.0, 1.0)  # Scale to 90% max

        # Message rate scoring (normalize against typical agricultural CAN rates)
        message_rate_score = min(self.message_rate_per_second / 800.0, 1.0)

        # Error rate scoring - more sensitive to errors
        error_rate_score = min(self.error_rate_percentage / 5.0, 1.0)

        # Queue depth scoring (normalize against typical queue sizes)
        queue_depth_score = min(self.queue_depth / 150.0, 1.0)

        # Latency scoring (normalize against agricultural tolerance)
        latency_score = min(self.average_latency_ms / 80.0, 1.0)

        # Calculate weighted score
        congestion_score = (
            weights["bus_load"] * bus_load_score
            + weights["message_rate"] * message_rate_score
            + weights["error_rate"] * error_rate_score
            + weights["queue_depth"] * queue_depth_score
            + weights["latency"] * latency_score
        )

        return min(congestion_score, 1.0)


@dataclass
class ThrottleDecision:
    """Decision structure for traffic throttling actions."""

    action: ThrottleAction
    severity_factor: float  # 0.0 (full throttle) to 1.0 (no throttle)
    affected_priorities: list[str]
    estimated_relief_time_ms: float = 0.0
    emergency_mode: bool = False
    recovery_mode: bool = False
    preserve_safety_messages: bool = True
    operation_context: str | None = None
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


class NetworkCongestionDetector:
    """Advanced congestion detection system for agricultural CAN networks."""

    def __init__(
        self,
        monitoring_interval: float = 1.0,
        history_window_size: int = 30,
        prediction_horizon_seconds: int = 60,
    ) -> None:
        """Initialize congestion detector.

        Parameters
        ----------
        monitoring_interval : float
            Metrics collection interval in seconds
        history_window_size : int
            Number of historical metrics to maintain
        prediction_horizon_seconds : int
            Time horizon for congestion prediction
        """
        self.monitoring_interval = monitoring_interval
        self.history_window_size = history_window_size
        self.prediction_horizon_seconds = prediction_horizon_seconds

        # Historical metrics storage
        self.metrics_history: deque[CongestionMetrics] = deque(maxlen=history_window_size)

        # Current state
        self.current_congestion_level = CongestionLevel.NORMAL
        self.last_detection_time = datetime.now()

        # Monitoring task
        self._monitoring_task: asyncio.Task | None = None
        self._is_monitoring = False

    async def start_monitoring(self, interface_manager) -> None:
        """Start continuous congestion monitoring.

        Parameters
        ----------
        interface_manager
            CAN interface manager for metrics collection
        """
        if self._is_monitoring:
            return

        self._is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop(interface_manager))
        logger.info("Started network congestion monitoring")

    async def stop_monitoring(self) -> None:
        """Stop congestion monitoring."""
        self._is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped network congestion monitoring")

    async def _monitoring_loop(self, interface_manager) -> None:
        """Main monitoring loop for continuous congestion detection."""
        while self._is_monitoring:
            try:
                # Collect current metrics
                interface_status = self._get_interface_status(interface_manager)
                current_metrics = await self._collect_metrics(interface_status)

                # Add to history
                self.metrics_history.append(current_metrics)

                # Update congestion level
                congestion_score = current_metrics.calculate_congestion_score()
                self.current_congestion_level = self._classify_congestion_level(congestion_score)

                # Log significant changes
                if len(self.metrics_history) > 1:
                    previous_level = self._classify_congestion_level(
                        self.metrics_history[-2].calculate_congestion_score()
                    )
                    if self.current_congestion_level != previous_level:
                        logger.info(
                            f"Congestion level changed: {previous_level.value} -> "
                            f"{self.current_congestion_level.value}"
                        )

                await asyncio.sleep(self.monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Congestion monitoring error: {e}")
                await asyncio.sleep(self.monitoring_interval)

    def _get_interface_status(self, interface_manager) -> dict[str, Any]:
        """Get status from all CAN interfaces.

        Parameters
        ----------
        interface_manager
            CAN interface manager

        Returns
        -------
        dict[str, Any]
            Interface status by interface ID
        """
        # This method would integrate with the actual interface manager
        # For now, return empty dict - will be mocked in tests
        return {}

    async def _collect_metrics(self, interface_status: dict[str, Any]) -> CongestionMetrics:
        """Collect comprehensive congestion metrics from interfaces.

        Parameters
        ----------
        interface_status : dict[str, Any]
            Current interface status data

        Returns
        -------
        CongestionMetrics
            Current congestion metrics
        """
        metrics = CongestionMetrics()

        if not interface_status:
            return metrics

        # Aggregate metrics across all interfaces
        total_bus_load = 0.0
        total_message_rate = 0.0
        total_errors = 0
        total_messages = 0
        interface_count = 0

        for _interface_id, status in interface_status.items():
            if status and hasattr(status, "bus_load_percentage"):
                total_bus_load += status.bus_load_percentage
                interface_count += 1

                # Calculate message rate and error rate
                if hasattr(status, "messages_sent") and hasattr(status, "messages_received"):
                    interface_messages = status.messages_sent + status.messages_received
                    total_messages += interface_messages

                    # Estimate message rate (messages per second)
                    # This would need time-based calculation in real implementation
                    total_message_rate += interface_messages / 60.0  # Rough estimate

                if hasattr(status, "errors_total"):
                    total_errors += status.errors_total

        # Calculate aggregated metrics
        if interface_count > 0:
            metrics.bus_load_percentage = total_bus_load / interface_count
            metrics.message_rate_per_second = total_message_rate

        if total_messages > 0:
            metrics.error_rate_percentage = (total_errors / total_messages) * 100.0

        # Get queue depth and latency measurements
        metrics.queue_depth = self._get_queue_depth()
        avg_latency, peak_latency = await self._measure_latency()
        metrics.average_latency_ms = avg_latency
        metrics.peak_latency_ms = peak_latency

        return metrics

    def _get_queue_depth(self) -> int:
        """Get current message queue depth.

        Returns
        -------
        int
            Current queue depth
        """
        # This would integrate with the actual message queue
        # Mocked in tests
        return 0

    async def _measure_latency(self) -> tuple[float, float]:
        """Measure current network latency.

        Returns
        -------
        tuple[float, float]
            (average_latency_ms, peak_latency_ms)
        """
        # This would implement actual latency measurement
        # Mocked in tests
        return 0.0, 0.0

    def _classify_congestion_level(self, congestion_score: float) -> CongestionLevel:
        """Classify congestion level based on score.

        Parameters
        ----------
        congestion_score : float
            Congestion score (0.0 to 1.0)

        Returns
        -------
        CongestionLevel
            Classified congestion level
        """
        if congestion_score < 0.4:
            return CongestionLevel.NORMAL
        elif congestion_score < 0.6:
            return CongestionLevel.MODERATE
        elif congestion_score < 0.8:
            return CongestionLevel.HIGH
        else:
            return CongestionLevel.CRITICAL

    def _analyze_congestion_trend(self) -> str:
        """Analyze congestion trend from historical data.

        Returns
        -------
        str
            Trend direction: "increasing", "decreasing", "stable"
        """
        if len(self.metrics_history) < 3:
            return "stable"

        # Calculate trend using recent metrics
        recent_scores = [
            metrics.calculate_congestion_score() for metrics in list(self.metrics_history)[-5:]
        ]

        if len(recent_scores) < 3:
            return "stable"

        # Simple linear trend analysis
        x = list(range(len(recent_scores)))
        slope = np.polyfit(x, recent_scores, 1)[0]

        if slope > 0.02:
            return "increasing"
        elif slope < -0.02:
            return "decreasing"
        else:
            return "stable"

    async def _predict_congestion(self, time_horizon_seconds: int = 60) -> dict[str, Any]:
        """Predict future congestion levels.

        Parameters
        ----------
        time_horizon_seconds : int
            Time horizon for prediction

        Returns
        -------
        dict[str, Any]
            Prediction results with confidence metrics
        """
        if len(self.metrics_history) < 5:
            return {
                "predicted_level": CongestionLevel.NORMAL.value,
                "confidence": 0.5,
                "estimated_time_to_critical": None,
            }

        # Simple trend-based prediction
        recent_scores = [
            metrics.calculate_congestion_score() for metrics in list(self.metrics_history)[-10:]
        ]

        # Linear extrapolation
        x = list(range(len(recent_scores)))
        coefficients = np.polyfit(x, recent_scores, 1)
        slope, intercept = coefficients

        # Project forward
        future_x = len(recent_scores) + (time_horizon_seconds / self.monitoring_interval)
        predicted_score = slope * future_x + intercept
        predicted_score = max(0.0, min(1.0, predicted_score))

        predicted_level = self._classify_congestion_level(predicted_score)

        # Calculate confidence based on trend consistency
        score_variance = np.var(recent_scores)
        confidence = max(0.3, 1.0 - (float(score_variance) * 5))

        # Estimate time to critical if trending upward
        time_to_critical = None
        if slope > 0 and predicted_score < 0.8:
            time_to_critical = (0.8 - recent_scores[-1]) / slope * self.monitoring_interval

        return {
            "predicted_level": predicted_level.value,
            "confidence": confidence,
            "estimated_time_to_critical": time_to_critical,
        }


class TrafficThrottler:
    """Adaptive traffic throttling system for agricultural CAN networks."""

    def __init__(
        self,
        enable_adaptive_throttling: bool = True,
        safety_margin_percentage: float = 20.0,
        recovery_hysteresis: float = 0.1,
    ) -> None:
        """Initialize traffic throttler.

        Parameters
        ----------
        enable_adaptive_throttling : bool
            Enable adaptive throttling algorithms
        safety_margin_percentage : float
            Safety margin for throttling decisions
        recovery_hysteresis : float
            Hysteresis factor for throttle recovery
        """
        self.enable_adaptive_throttling = enable_adaptive_throttling
        self.safety_margin_percentage = safety_margin_percentage
        self.recovery_hysteresis = recovery_hysteresis

        # Active throttling state
        self.active_throttles: list[str] = []
        self.last_throttle_time = datetime.now()
        self.throttle_history: deque[ThrottleDecision] = deque(maxlen=50)

    def make_throttle_decision(
        self,
        metrics: CongestionMetrics,
        congestion_level: CongestionLevel,
        operation_context: str | None = None,
    ) -> ThrottleDecision:
        """Make adaptive throttling decision based on current conditions.

        Parameters
        ----------
        metrics : CongestionMetrics
            Current congestion metrics
        congestion_level : CongestionLevel
            Current congestion level
        operation_context : str | None
            Agricultural operation context ("field_operation", "transport", etc.)

        Returns
        -------
        ThrottleDecision
            Throttling decision with recommended actions
        """
        if not self.enable_adaptive_throttling:
            return ThrottleDecision(
                action=ThrottleAction.NONE,
                severity_factor=1.0,
                affected_priorities=[],
                operation_context=operation_context,
            )

        # Check for recovery conditions first
        if self.active_throttles and congestion_level == CongestionLevel.NORMAL:
            return self._create_recovery_decision(metrics, operation_context)

        # Make throttling decision based on congestion level
        if congestion_level == CongestionLevel.NORMAL:
            return self._handle_normal_congestion(metrics, operation_context)
        elif congestion_level == CongestionLevel.MODERATE:
            return self._handle_moderate_congestion(metrics, operation_context)
        elif congestion_level == CongestionLevel.HIGH:
            return self._handle_high_congestion(metrics, operation_context)
        else:  # CRITICAL
            return self._handle_critical_congestion(metrics, operation_context)

    def _handle_normal_congestion(
        self, metrics: CongestionMetrics, operation_context: str | None
    ) -> ThrottleDecision:
        """Handle normal congestion conditions."""
        return ThrottleDecision(
            action=ThrottleAction.NONE,
            severity_factor=1.0,
            affected_priorities=[],
            operation_context=operation_context,
            preserve_safety_messages=True,
        )

    def _handle_moderate_congestion(
        self, metrics: CongestionMetrics, operation_context: str | None
    ) -> ThrottleDecision:
        """Handle moderate congestion conditions."""
        # Adjust severity based on operation context
        base_severity = 0.8
        if operation_context == "field_operation":
            # More conservative for field operations (higher severity factor = less throttling)
            severity_factor = base_severity * 1.1
        else:
            severity_factor = base_severity

        return ThrottleDecision(
            action=ThrottleAction.REDUCE_LOW_PRIORITY,
            severity_factor=severity_factor,
            affected_priorities=["LOW"],
            operation_context=operation_context,
            preserve_safety_messages=True,
            estimated_relief_time_ms=5000.0,
        )

    def _handle_high_congestion(
        self, metrics: CongestionMetrics, operation_context: str | None
    ) -> ThrottleDecision:
        """Handle high congestion conditions."""
        base_severity = 0.6
        if operation_context == "field_operation":
            # More conservative for field operations (higher severity factor = less throttling)
            severity_factor = base_severity * 1.1
        else:
            severity_factor = base_severity

        return ThrottleDecision(
            action=ThrottleAction.REDUCE_NORMAL_PRIORITY,
            severity_factor=severity_factor,
            affected_priorities=["NORMAL"],
            operation_context=operation_context,
            preserve_safety_messages=True,
            estimated_relief_time_ms=10000.0,
        )

    def _handle_critical_congestion(
        self, metrics: CongestionMetrics, operation_context: str | None
    ) -> ThrottleDecision:
        """Handle critical congestion conditions."""
        # Emergency throttling - very aggressive
        base_severity = 0.3
        if operation_context == "field_operation":
            # More conservative for field operations (higher severity factor = less throttling)
            severity_factor = base_severity * 1.1
        else:
            severity_factor = base_severity

        return ThrottleDecision(
            action=ThrottleAction.EMERGENCY_THROTTLE,
            severity_factor=severity_factor,
            affected_priorities=["HIGH"],
            operation_context=operation_context,
            emergency_mode=True,
            preserve_safety_messages=True,
            estimated_relief_time_ms=20000.0,
            confidence=0.9,
        )

    def _create_recovery_decision(
        self, metrics: CongestionMetrics, operation_context: str | None
    ) -> ThrottleDecision:
        """Create throttle recovery decision."""
        return ThrottleDecision(
            action=ThrottleAction.RESTORE_NORMAL,
            severity_factor=1.0,
            affected_priorities=[],
            operation_context=operation_context,
            recovery_mode=True,
            preserve_safety_messages=True,
        )

    async def apply_throttle_decision(self, decision: ThrottleDecision) -> None:
        """Apply throttling decision to active traffic management.

        Parameters
        ----------
        decision : ThrottleDecision
            Throttling decision to apply
        """
        # Record the decision
        self.throttle_history.append(decision)
        self.last_throttle_time = datetime.now()

        if decision.recovery_mode:
            # Clear active throttles
            self.active_throttles.clear()
            logger.info("Restored normal traffic flow - congestion resolved")
        elif decision.action != ThrottleAction.NONE:
            # Apply throttling
            self.active_throttles = decision.affected_priorities.copy()
            logger.warning(
                f"Applied {decision.action.name} throttling "
                f"(severity: {decision.severity_factor:.2f}) "
                f"to priorities: {decision.affected_priorities}"
            )

        # In a real implementation, this would integrate with the message routing
        # and priority systems to actually throttle traffic
