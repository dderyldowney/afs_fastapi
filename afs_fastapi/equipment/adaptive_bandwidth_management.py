"""
Adaptive bandwidth management system for agricultural CAN network operations.

This module provides sophisticated bandwidth allocation and monitoring for multi-tractor
fleet coordination with priority-based allocation between safety-critical field
operations and efficiency-focused transport operations.

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

from afs_fastapi.equipment.advanced_message_prioritization import AgriculturalOperationContext
from afs_fastapi.equipment.congestion_detection import CongestionLevel, CongestionMetrics

# Configure logging for bandwidth management
logger = logging.getLogger(__name__)


class OperationBandwidthContext(Enum):
    """Bandwidth allocation contexts for different agricultural operations."""

    FIELD_OPERATION = "field_operation"  # Safety-critical field work
    TRANSPORT_OPERATION = "transport_operation"  # Efficiency-focused transport
    MAINTENANCE_OPERATION = "maintenance_operation"  # Equipment maintenance
    EMERGENCY_OPERATION = "emergency_operation"  # Emergency/safety operations


@dataclass
class BandwidthMetrics:
    """Real-time bandwidth metrics for agricultural CAN networks."""

    total_bandwidth_kbps: float = 0.0
    allocated_bandwidth_kbps: float = 0.0
    available_bandwidth_kbps: float = 0.0
    field_operation_usage_kbps: float = 0.0
    transport_operation_usage_kbps: float = 0.0
    utilization_percentage: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def update_metrics(
        self,
        total_bandwidth: float,
        allocated_bandwidth: float,
        field_usage: float,
        transport_usage: float,
    ) -> None:
        """Update all bandwidth metrics.

        Parameters
        ----------
        total_bandwidth : float
            Total available bandwidth in kbps
        allocated_bandwidth : float
            Currently allocated bandwidth in kbps
        field_usage : float
            Bandwidth used by field operations in kbps
        transport_usage : float
            Bandwidth used by transport operations in kbps
        """
        self.total_bandwidth_kbps = total_bandwidth
        self.allocated_bandwidth_kbps = allocated_bandwidth
        self.available_bandwidth_kbps = max(0.0, total_bandwidth - allocated_bandwidth)
        self.field_operation_usage_kbps = field_usage
        self.transport_operation_usage_kbps = transport_usage
        self.utilization_percentage = (
            (allocated_bandwidth / total_bandwidth * 100.0) if total_bandwidth > 0 else 0.0
        )
        self.timestamp = datetime.now()

    def calculate_allocation_efficiency(self) -> float:
        """Calculate bandwidth allocation efficiency.

        Returns
        -------
        float
            Efficiency score (0.0 to 1.0) where 1.0 is optimal allocation
        """
        if self.total_bandwidth_kbps == 0:
            return 0.0

        # Efficiency decreases if over-allocated or severely under-utilized
        utilization_ratio = self.allocated_bandwidth_kbps / self.total_bandwidth_kbps

        if utilization_ratio <= 1.0:
            # Penalize under-utilization and over-utilization differently
            if utilization_ratio < 0.3:
                # Severe under-utilization
                return utilization_ratio * 2.0  # Scale up low utilization
            else:
                # Good utilization range
                return min(1.0, utilization_ratio + 0.2)
        else:
            # Over-allocation penalty
            over_allocation_penalty = 1.0 / utilization_ratio
            return max(0.0, over_allocation_penalty - 0.2)


@dataclass
class BandwidthAllocation:
    """Represents a bandwidth allocation for an agricultural operation."""

    operation_id: str
    operation_context: OperationBandwidthContext
    requested_bandwidth_kbps: float
    allocated_bandwidth_kbps: float
    guaranteed_minimum_kbps: float
    priority_level: str
    can_be_preempted: bool = True
    allocation_timestamp: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


class BandwidthPolicy:
    """Bandwidth allocation policies for different agricultural operations."""

    def __init__(self) -> None:
        """Initialize bandwidth policy framework."""
        self._field_operation_policy = {
            "minimum_guarantee_percentage": 60,  # Field ops get 60% minimum guarantee
            "can_be_preempted": False,
            "priority_multiplier": 1.5,
            "emergency_reserve_percentage": 20,
        }

        self._transport_operation_policy = {
            "minimum_guarantee_percentage": 30,  # Transport gets 30% minimum guarantee
            "can_be_preempted": True,
            "priority_multiplier": 1.0,
            "emergency_reserve_percentage": 5,
        }

        self._emergency_operation_policy = {
            "minimum_guarantee_percentage": 80,  # Emergency gets 80% minimum guarantee
            "can_be_preempted": False,
            "priority_multiplier": 2.0,
            "emergency_reserve_percentage": 50,
        }

    def get_allocation_limits(self, context: OperationBandwidthContext) -> dict[str, Any]:
        """Get allocation limits for a specific operation context.

        Parameters
        ----------
        context : OperationBandwidthContext
            The operation context to get limits for

        Returns
        -------
        dict[str, Any]
            Policy limits including minimum guarantees and constraints
        """
        if context == OperationBandwidthContext.FIELD_OPERATION:
            return self._field_operation_policy.copy()
        elif context == OperationBandwidthContext.TRANSPORT_OPERATION:
            return self._transport_operation_policy.copy()
        elif context == OperationBandwidthContext.EMERGENCY_OPERATION:
            return self._emergency_operation_policy.copy()
        else:
            # Default to transport policy for unknown contexts
            return self._transport_operation_policy.copy()

    def calculate_guaranteed_minimum(
        self, context: OperationBandwidthContext, requested_bandwidth: float, total_bandwidth: float
    ) -> float:
        """Calculate guaranteed minimum bandwidth for an operation context."""
        policy = self.get_allocation_limits(context)
        policy_minimum = total_bandwidth * (float(policy["minimum_guarantee_percentage"]) / 100.0)
        # Guaranteed minimum should not exceed requested bandwidth
        return min(requested_bandwidth, policy_minimum)


class BandwidthAllocator:
    """Core bandwidth allocation system for agricultural operations."""

    def __init__(self, total_bandwidth_kbps: float) -> None:
        """Initialize bandwidth allocator.

        Parameters
        ----------
        total_bandwidth_kbps : float
            Total available bandwidth in kilobits per second
        """
        self.total_bandwidth_kbps = total_bandwidth_kbps
        self.active_allocations: dict[str, BandwidthAllocation] = {}
        self.policy = BandwidthPolicy()
        self._allocation_history: deque[BandwidthAllocation] = deque(maxlen=100)

    def allocate_bandwidth(
        self,
        operation_id: str,
        context: OperationBandwidthContext,
        requested_bandwidth_kbps: float,
        priority_level: str,
    ) -> BandwidthAllocation:
        """Allocate bandwidth for an agricultural operation.

        Parameters
        ----------
        operation_id : str
            Unique identifier for the operation
        context : OperationBandwidthContext
            Agricultural operation context
        requested_bandwidth_kbps : float
            Requested bandwidth in kbps
        priority_level : str
            Priority level (HIGH, NORMAL, LOW, EMERGENCY)

        Returns
        -------
        BandwidthAllocation
            Allocation result with actual allocated bandwidth
        """
        policy_limits = self.policy.get_allocation_limits(context)
        guaranteed_minimum = self.policy.calculate_guaranteed_minimum(
            context, requested_bandwidth_kbps, self.total_bandwidth_kbps
        )

        # Calculate current usage
        current_allocated = sum(
            alloc.allocated_bandwidth_kbps for alloc in self.active_allocations.values()
        )
        available_bandwidth = self.total_bandwidth_kbps - current_allocated

        # Determine allocation amount
        if context == OperationBandwidthContext.FIELD_OPERATION or priority_level == "EMERGENCY":
            # Field operations and emergency get priority allocation
            if available_bandwidth >= requested_bandwidth_kbps:
                allocated_amount = requested_bandwidth_kbps
            else:
                # Preempt transport operations if necessary
                allocated_amount = self._preempt_for_priority_operation(
                    requested_bandwidth_kbps, context
                )
        else:
            # Transport and other operations get best-effort allocation
            allocated_amount = min(requested_bandwidth_kbps, available_bandwidth)

        allocation = BandwidthAllocation(
            operation_id=operation_id,
            operation_context=context,
            requested_bandwidth_kbps=requested_bandwidth_kbps,
            allocated_bandwidth_kbps=allocated_amount,
            guaranteed_minimum_kbps=guaranteed_minimum,
            priority_level=priority_level,
            can_be_preempted=policy_limits["can_be_preempted"],
        )

        self.active_allocations[operation_id] = allocation
        self._allocation_history.append(allocation)

        logger.info(
            f"Allocated {allocated_amount:.1f} kbps to {operation_id} "
            f"({context.value}, priority: {priority_level})"
        )

        return allocation

    def _preempt_for_priority_operation(
        self, requested_bandwidth: float, requesting_context: OperationBandwidthContext
    ) -> float:
        """Preempt lower priority operations to satisfy higher priority request."""
        current_allocated = sum(
            alloc.allocated_bandwidth_kbps for alloc in self.active_allocations.values()
        )
        available = self.total_bandwidth_kbps - current_allocated

        if available >= requested_bandwidth:
            return requested_bandwidth

        # Find preemptable allocations (transport operations)
        preemptable_allocations = [
            alloc for alloc in self.active_allocations.values() if alloc.can_be_preempted
        ]

        # Sort by priority (transport operations first, then by current allocation)
        preemptable_allocations.sort(
            key=lambda a: (
                a.operation_context != OperationBandwidthContext.TRANSPORT_OPERATION,
                a.priority_level != "NORMAL",
                -a.allocated_bandwidth_kbps,
            )
        )

        freed_bandwidth = available
        for allocation in preemptable_allocations:
            if freed_bandwidth >= requested_bandwidth:
                break

            # For field operations requesting bandwidth, reduce transport operations more aggressively
            if requesting_context == OperationBandwidthContext.FIELD_OPERATION:
                # Reduce transport to 50% of guaranteed minimum if necessary for field operations
                target_allocation = min(
                    allocation.guaranteed_minimum_kbps * 0.5, allocation.allocated_bandwidth_kbps
                )
            else:
                # Normal preemption - reduce to guaranteed minimum
                target_allocation = allocation.guaranteed_minimum_kbps

            current_allocation = allocation.allocated_bandwidth_kbps
            if current_allocation > target_allocation:
                reduction = current_allocation - target_allocation
                allocation.allocated_bandwidth_kbps = target_allocation
                allocation.last_updated = datetime.now()
                freed_bandwidth += reduction

                logger.warning(
                    f"Preempted {reduction:.1f} kbps from {allocation.operation_id} "
                    f"for priority operation (new allocation: {target_allocation:.1f} kbps)"
                )

        return min(requested_bandwidth, freed_bandwidth)

    def get_allocation(self, operation_id: str) -> BandwidthAllocation | None:
        """Get current allocation for an operation."""
        return self.active_allocations.get(operation_id)

    def reallocate_for_congestion(
        self, congestion_level: CongestionLevel, congestion_metrics: CongestionMetrics
    ) -> dict[str, float]:
        """Reallocate bandwidth during network congestion events.

        Parameters
        ----------
        congestion_level : CongestionLevel
            Current network congestion level
        congestion_metrics : CongestionMetrics
            Detailed congestion metrics

        Returns
        -------
        dict[str, float]
            Mapping of operation_id to new bandwidth allocation
        """
        reallocation_results = {}

        if congestion_level in [CongestionLevel.HIGH, CongestionLevel.CRITICAL]:
            # Aggressive reallocation for high congestion
            congestion_factor = 0.6 if congestion_level == CongestionLevel.HIGH else 0.4

            for operation_id, allocation in self.active_allocations.items():
                # Emergency operations are never reduced during congestion
                if (
                    allocation.operation_context == OperationBandwidthContext.EMERGENCY_OPERATION
                    or allocation.priority_level == "EMERGENCY"
                ):
                    # Maintain emergency operations at full allocation
                    reallocation_results[operation_id] = allocation.allocated_bandwidth_kbps
                elif allocation.can_be_preempted:
                    # Reduce preemptable operations
                    new_allocation = max(
                        allocation.guaranteed_minimum_kbps,
                        allocation.allocated_bandwidth_kbps * congestion_factor,
                    )
                    allocation.allocated_bandwidth_kbps = new_allocation
                    allocation.last_updated = datetime.now()
                    reallocation_results[operation_id] = new_allocation
                else:
                    # Maintain other non-preemptable operations (field operations)
                    reallocation_results[operation_id] = allocation.allocated_bandwidth_kbps

            logger.warning(
                f"Reallocated bandwidth due to {congestion_level.value} congestion: "
                f"{len(reallocation_results)} operations affected"
            )

        return reallocation_results


class BandwidthMonitor:
    """Real-time bandwidth monitoring system for agricultural CAN networks."""

    def __init__(self, monitoring_interval: float = 1.0, history_window_size: int = 60) -> None:
        """Initialize bandwidth monitor.

        Parameters
        ----------
        monitoring_interval : float
            Monitoring interval in seconds
        history_window_size : int
            Number of historical metrics to maintain
        """
        self.monitoring_interval = monitoring_interval
        self.history_window_size = history_window_size
        self.metrics_history: deque[BandwidthMetrics] = deque(maxlen=history_window_size)

        # Monitoring state
        self._monitoring_task: asyncio.Task[None] | None = None
        self._is_monitoring = False

    async def start_monitoring(self, interface_manager: Any) -> None:
        """Start continuous bandwidth monitoring."""
        if self._is_monitoring:
            return

        self._is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop(interface_manager))
        logger.info("Started bandwidth monitoring")

    async def stop_monitoring(self) -> None:
        """Stop bandwidth monitoring."""
        self._is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped bandwidth monitoring")

    async def _monitoring_loop(self, interface_manager: Any) -> None:
        """Main monitoring loop for bandwidth collection."""
        while self._is_monitoring:
            try:
                # Collect bandwidth metrics from interfaces
                interface_data = self._get_interface_data(interface_manager)
                current_metrics = await self._collect_bandwidth_metrics(interface_data)

                # Add to history
                self.metrics_history.append(current_metrics)

                # Analyze trends
                if len(self.metrics_history) > 5:
                    trend = self._analyze_bandwidth_trend()
                    if trend == "increasing" and current_metrics.utilization_percentage > 80:
                        logger.warning(
                            f"Bandwidth utilization trending upward: "
                            f"{current_metrics.utilization_percentage:.1f}%"
                        )

                await asyncio.sleep(self.monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Bandwidth monitoring error: {e}")
                await asyncio.sleep(self.monitoring_interval)

    def _get_interface_data(self, interface_manager: Any) -> dict[str, Any]:
        """Get bandwidth data from CAN interfaces."""
        # This would integrate with actual interface manager
        # Mocked for testing
        return {}

    async def _collect_bandwidth_metrics(self, interface_data: dict[str, Any]) -> BandwidthMetrics:
        """Collect comprehensive bandwidth metrics.

        Parameters
        ----------
        interface_data : dict[str, Any]
            Interface bandwidth data

        Returns
        -------
        BandwidthMetrics
            Current bandwidth metrics
        """
        metrics = BandwidthMetrics()

        if not interface_data:
            return metrics

        # Aggregate metrics across interfaces
        total_bandwidth = 0.0
        total_usage = 0.0
        field_usage = 0.0
        transport_usage = 0.0

        for _interface_id, data in interface_data.items():
            if isinstance(data, dict):
                total_bandwidth += data.get("total_bandwidth", 0.0)
                total_usage += data.get("current_usage", 0.0)
                field_usage += data.get("field_operation_usage", 0.0)
                transport_usage += data.get("transport_usage", 0.0)

        # Update metrics
        metrics.update_metrics(
            total_bandwidth=total_bandwidth,
            allocated_bandwidth=total_usage,
            field_usage=field_usage,
            transport_usage=transport_usage,
        )

        return metrics

    def _analyze_bandwidth_trend(self) -> str:
        """Analyze bandwidth utilization trend.

        Returns
        -------
        str
            Trend direction: "increasing", "decreasing", "stable"
        """
        if len(self.metrics_history) < 3:
            return "stable"

        # Calculate trend using recent utilization
        recent_utilizations = [
            metrics.utilization_percentage for metrics in list(self.metrics_history)[-5:]
        ]

        if len(recent_utilizations) < 3:
            return "stable"

        # Simple linear trend analysis
        x = list(range(len(recent_utilizations)))
        slope = np.polyfit(x, recent_utilizations, 1)[0]

        if slope > 2.0:  # Increasing by more than 2% per interval
            return "increasing"
        elif slope < -2.0:  # Decreasing by more than 2% per interval
            return "decreasing"
        else:
            return "stable"

    async def _predict_bandwidth_capacity(self, time_horizon_seconds: int = 120) -> dict[str, Any]:
        """Predict bandwidth capacity usage.

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
                "predicted_utilization": 50.0,
                "time_to_saturation": None,
                "confidence": 0.5,
            }

        # Simple trend-based prediction
        recent_utilizations = [
            metrics.utilization_percentage for metrics in list(self.metrics_history)[-10:]
        ]

        # Linear extrapolation
        x = list(range(len(recent_utilizations)))
        coefficients = np.polyfit(x, recent_utilizations, 1)
        slope, intercept = coefficients

        # Project forward
        future_x = len(recent_utilizations) + (time_horizon_seconds / self.monitoring_interval)
        predicted_utilization = slope * future_x + intercept
        predicted_utilization = max(0.0, min(100.0, predicted_utilization))

        # Calculate confidence based on trend consistency
        utilization_variance = np.var(recent_utilizations)
        confidence = max(0.3, 1.0 - (float(utilization_variance) / 100))

        # Estimate time to saturation if trending upward
        time_to_saturation = None
        if slope > 0 and predicted_utilization < 95.0:
            current_utilization = recent_utilizations[-1]
            time_to_saturation = (95.0 - current_utilization) / slope * self.monitoring_interval

        return {
            "predicted_utilization": predicted_utilization,
            "time_to_saturation": time_to_saturation,
            "confidence": confidence,
        }


class AdaptiveBandwidthManager:
    """Integrated adaptive bandwidth management system for agricultural operations."""

    def __init__(
        self,
        total_bandwidth_kbps: float,
        enable_adaptive_allocation: bool = True,
        monitoring_interval: float = 1.0,
    ) -> None:
        """Initialize adaptive bandwidth manager.

        Parameters
        ----------
        total_bandwidth_kbps : float
            Total available bandwidth
        enable_adaptive_allocation : bool
            Enable adaptive allocation algorithms
        monitoring_interval : float
            Monitoring interval in seconds
        """
        self.total_bandwidth_kbps = total_bandwidth_kbps
        self.adaptive_allocation_enabled = enable_adaptive_allocation

        # Core components
        self.allocator = BandwidthAllocator(total_bandwidth_kbps)
        self.monitor = BandwidthMonitor(monitoring_interval)
        self.policy = BandwidthPolicy()

        # State tracking
        self.current_metrics: BandwidthMetrics | None = None

    def request_bandwidth(
        self,
        operation_id: str,
        agricultural_context: AgriculturalOperationContext,
        requested_bandwidth_kbps: float,
        message_priority_level: str,
    ) -> BandwidthAllocation:
        """Request bandwidth allocation for an agricultural operation.

        Parameters
        ----------
        operation_id : str
            Unique operation identifier
        agricultural_context : AgriculturalOperationContext
            Agricultural operation context
        requested_bandwidth_kbps : float
            Requested bandwidth amount
        message_priority_level : str
            Message priority level

        Returns
        -------
        BandwidthAllocation
            Bandwidth allocation result
        """
        # Map agricultural context to bandwidth context
        if agricultural_context == AgriculturalOperationContext.FIELD_CULTIVATION:
            bandwidth_context = OperationBandwidthContext.FIELD_OPERATION
        elif agricultural_context == AgriculturalOperationContext.TRANSPORT_MODE:
            bandwidth_context = OperationBandwidthContext.TRANSPORT_OPERATION
        else:
            bandwidth_context = OperationBandwidthContext.TRANSPORT_OPERATION

        # Handle emergency priority
        if message_priority_level == "EMERGENCY":
            bandwidth_context = OperationBandwidthContext.EMERGENCY_OPERATION

        return self.allocator.allocate_bandwidth(
            operation_id=operation_id,
            context=bandwidth_context,
            requested_bandwidth_kbps=requested_bandwidth_kbps,
            priority_level=message_priority_level,
        )

    async def handle_congestion_event(
        self, congestion_level: CongestionLevel, congestion_metrics: CongestionMetrics
    ) -> None:
        """Handle network congestion by reallocating bandwidth.

        Parameters
        ----------
        congestion_level : CongestionLevel
            Current congestion level
        congestion_metrics : CongestionMetrics
            Detailed congestion metrics
        """
        if not self.adaptive_allocation_enabled:
            return

        reallocation_results = self.allocator.reallocate_for_congestion(
            congestion_level, congestion_metrics
        )

        if reallocation_results:
            logger.info(
                f"Bandwidth reallocation completed: {len(reallocation_results)} "
                f"operations affected by {congestion_level.value} congestion"
            )

    def get_current_allocation(self, operation_id: str) -> BandwidthAllocation | None:
        """Get current bandwidth allocation for an operation."""
        return self.allocator.get_allocation(operation_id)

    async def get_current_bandwidth_metrics(self) -> BandwidthMetrics:
        """Get current bandwidth metrics."""
        if self.current_metrics is None:
            # Create default metrics if monitoring not started
            self.current_metrics = BandwidthMetrics()
            self.current_metrics.total_bandwidth_kbps = self.total_bandwidth_kbps

            # Calculate current allocation from active allocations
            total_allocated = sum(
                alloc.allocated_bandwidth_kbps
                for alloc in self.allocator.active_allocations.values()
            )

            field_usage = sum(
                alloc.allocated_bandwidth_kbps
                for alloc in self.allocator.active_allocations.values()
                if alloc.operation_context == OperationBandwidthContext.FIELD_OPERATION
            )

            transport_usage = sum(
                alloc.allocated_bandwidth_kbps
                for alloc in self.allocator.active_allocations.values()
                if alloc.operation_context == OperationBandwidthContext.TRANSPORT_OPERATION
            )

            self.current_metrics.update_metrics(
                total_bandwidth=self.total_bandwidth_kbps,
                allocated_bandwidth=total_allocated,
                field_usage=field_usage,
                transport_usage=transport_usage,
            )

        return self.current_metrics

    async def start_monitoring(self, interface_manager: Any = None) -> None:
        """Start bandwidth monitoring."""
        await self.monitor.start_monitoring(interface_manager)

    async def stop_monitoring(self) -> None:
        """Stop bandwidth monitoring."""
        await self.monitor.stop_monitoring()
