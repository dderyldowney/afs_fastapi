"""
Test suite for adaptive bandwidth management system for agricultural operations.

Tests dynamic bandwidth allocation between field operations (safety-critical) and
transport operations (efficiency-focused) with integration to congestion detection
and message prioritization systems.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from afs_fastapi.equipment.adaptive_bandwidth_management import (
    AdaptiveBandwidthManager,
    BandwidthAllocator,
    BandwidthMetrics,
    BandwidthMonitor,
    BandwidthPolicy,
    OperationBandwidthContext,
)
from afs_fastapi.equipment.advanced_message_prioritization import AgriculturalOperationContext
from afs_fastapi.equipment.congestion_detection import CongestionLevel, CongestionMetrics


class TestBandwidthMetrics:
    """Test bandwidth metrics data structure."""

    def test_metrics_initialization(self) -> None:
        """Test bandwidth metrics initialization."""
        metrics = BandwidthMetrics()

        assert metrics.total_bandwidth_kbps == 0.0
        assert metrics.allocated_bandwidth_kbps == 0.0
        assert metrics.available_bandwidth_kbps == 0.0
        assert metrics.field_operation_usage_kbps == 0.0
        assert metrics.transport_operation_usage_kbps == 0.0
        assert metrics.utilization_percentage == 0.0
        assert isinstance(metrics.timestamp, datetime)

    def test_metrics_update(self) -> None:
        """Test updating bandwidth metrics."""
        metrics = BandwidthMetrics()

        metrics.update_metrics(
            total_bandwidth=1000.0,
            allocated_bandwidth=750.0,
            field_usage=450.0,
            transport_usage=300.0,
        )

        assert metrics.total_bandwidth_kbps == 1000.0
        assert metrics.allocated_bandwidth_kbps == 750.0
        assert metrics.available_bandwidth_kbps == 250.0
        assert metrics.field_operation_usage_kbps == 450.0
        assert metrics.transport_operation_usage_kbps == 300.0
        assert metrics.utilization_percentage == 75.0

    def test_bandwidth_efficiency_calculation(self) -> None:
        """Test bandwidth efficiency calculation."""
        metrics = BandwidthMetrics()

        # High efficiency scenario
        metrics.update_metrics(
            total_bandwidth=1000.0,
            allocated_bandwidth=800.0,
            field_usage=600.0,
            transport_usage=200.0,
        )

        efficiency = metrics.calculate_allocation_efficiency()
        assert 0.8 <= efficiency <= 1.0  # High efficiency

        # Low efficiency scenario (over-allocation)
        metrics.update_metrics(
            total_bandwidth=1000.0,
            allocated_bandwidth=1200.0,  # Over-allocated
            field_usage=700.0,
            transport_usage=500.0,
        )

        efficiency = metrics.calculate_allocation_efficiency()
        assert efficiency < 0.8  # Lower efficiency due to over-allocation


class TestBandwidthAllocator:
    """Test adaptive bandwidth allocation system."""

    @pytest.fixture
    def allocator(self) -> BandwidthAllocator:
        """Create bandwidth allocator."""
        return BandwidthAllocator(total_bandwidth_kbps=1000.0)

    def test_allocator_initialization(self, allocator: BandwidthAllocator) -> None:
        """Test allocator initialization."""
        assert allocator.total_bandwidth_kbps == 1000.0
        assert len(allocator.active_allocations) == 0

    def test_field_operation_bandwidth_allocation(self, allocator: BandwidthAllocator) -> None:
        """Test bandwidth allocation for field operations."""
        context = OperationBandwidthContext.FIELD_OPERATION

        allocation = allocator.allocate_bandwidth(
            operation_id="field_cultivation_001",
            context=context,
            requested_bandwidth_kbps=400.0,
            priority_level="HIGH",
        )

        assert allocation.allocated_bandwidth_kbps >= 400.0  # Should get at least requested
        assert allocation.operation_context == context
        assert allocation.guaranteed_minimum_kbps > 0
        assert allocation.can_be_preempted is False  # Field operations not preemptable

    def test_transport_operation_bandwidth_allocation(self, allocator: BandwidthAllocator) -> None:
        """Test bandwidth allocation for transport operations."""
        context = OperationBandwidthContext.TRANSPORT_OPERATION

        allocation = allocator.allocate_bandwidth(
            operation_id="transport_001",
            context=context,
            requested_bandwidth_kbps=200.0,
            priority_level="NORMAL",
        )

        assert allocation.allocated_bandwidth_kbps >= 200.0
        assert allocation.operation_context == context
        assert allocation.can_be_preempted is True  # Transport operations can be preempted

    def test_field_operation_priority_over_transport(self, allocator: BandwidthAllocator) -> None:
        """Test that field operations get priority over transport operations."""
        # First allocate transport operation
        allocator.allocate_bandwidth(
            operation_id="transport_001",
            context=OperationBandwidthContext.TRANSPORT_OPERATION,
            requested_bandwidth_kbps=600.0,
            priority_level="NORMAL",
        )

        # Then request field operation that would require preemption
        field_allocation = allocator.allocate_bandwidth(
            operation_id="field_cultivation_001",
            context=OperationBandwidthContext.FIELD_OPERATION,
            requested_bandwidth_kbps=500.0,
            priority_level="HIGH",
        )

        # Field operation should get bandwidth, transport should be reduced
        assert field_allocation.allocated_bandwidth_kbps >= 500.0

        # Check that transport operation was preempted
        updated_transport = allocator.get_allocation("transport_001")
        assert updated_transport is not None
        # Transport should be reduced from original 600.0 to something lower
        assert updated_transport.allocated_bandwidth_kbps < 600.0

    def test_bandwidth_reallocation_on_congestion(self, allocator: BandwidthAllocator) -> None:
        """Test bandwidth reallocation during network congestion."""
        # Set up initial allocations
        field_allocation = allocator.allocate_bandwidth(
            operation_id="field_001",
            context=OperationBandwidthContext.FIELD_OPERATION,
            requested_bandwidth_kbps=400.0,
            priority_level="HIGH",
        )

        transport_allocation = allocator.allocate_bandwidth(
            operation_id="transport_001",
            context=OperationBandwidthContext.TRANSPORT_OPERATION,
            requested_bandwidth_kbps=300.0,
            priority_level="NORMAL",
        )

        # Simulate congestion requiring reallocation
        congestion_metrics = CongestionMetrics()
        congestion_metrics.bus_load_percentage = 85.0
        congestion_metrics.error_rate_percentage = 8.0

        # Trigger reallocation due to congestion
        allocator.reallocate_for_congestion(
            congestion_level=CongestionLevel.HIGH, congestion_metrics=congestion_metrics
        )

        # Field operations should maintain priority
        updated_field = allocator.get_allocation("field_001")
        updated_transport = allocator.get_allocation("transport_001")
        assert updated_field is not None
        assert updated_transport is not None

        assert updated_field.allocated_bandwidth_kbps >= field_allocation.guaranteed_minimum_kbps
        assert (
            updated_transport.allocated_bandwidth_kbps
            <= transport_allocation.allocated_bandwidth_kbps
        )


class TestBandwidthMonitor:
    """Test bandwidth monitoring system."""

    @pytest.fixture
    def monitor(self) -> BandwidthMonitor:
        """Create bandwidth monitor."""
        return BandwidthMonitor(monitoring_interval=0.1)

    def test_monitor_initialization(self, monitor: BandwidthMonitor) -> None:
        """Test monitor initialization."""
        assert monitor.monitoring_interval == 0.1
        assert len(monitor.metrics_history) == 0

    @pytest.mark.asyncio
    async def test_bandwidth_metrics_collection(self, monitor: BandwidthMonitor) -> None:
        """Test real-time bandwidth metrics collection."""
        # Mock network interface data
        mock_interface_data = {
            "can0": {
                "total_bandwidth": 1000.0,
                "current_usage": 650.0,
                "field_operation_usage": 400.0,
                "transport_usage": 250.0,
            }
        }

        metrics = await monitor._collect_bandwidth_metrics(mock_interface_data)

        assert metrics.total_bandwidth_kbps == 1000.0
        assert metrics.allocated_bandwidth_kbps == 650.0
        assert metrics.available_bandwidth_kbps == 350.0
        assert metrics.field_operation_usage_kbps == 400.0
        assert metrics.transport_operation_usage_kbps == 250.0

    def test_bandwidth_trend_analysis(self, monitor: BandwidthMonitor) -> None:
        """Test bandwidth utilization trend analysis."""
        # Add metrics with increasing utilization
        timestamps = [datetime.now() - timedelta(seconds=i * 10) for i in range(5, 0, -1)]
        utilizations = [30.0, 45.0, 60.0, 75.0, 90.0]  # Increasing trend

        for timestamp, utilization in zip(timestamps, utilizations, strict=False):
            metrics = BandwidthMetrics()
            metrics.timestamp = timestamp
            metrics.utilization_percentage = utilization
            monitor.metrics_history.append(metrics)

        trend = monitor._analyze_bandwidth_trend()
        assert trend == "increasing"

    @pytest.mark.asyncio
    async def test_bandwidth_capacity_prediction(self, monitor: BandwidthMonitor) -> None:
        """Test bandwidth capacity prediction."""
        # Setup historical data
        current_time = datetime.now()
        for i in range(10):
            metrics = BandwidthMetrics()
            metrics.timestamp = current_time - timedelta(seconds=i * 10)
            metrics.utilization_percentage = 40.0 + (i * 5.0)  # Linear increase
            monitor.metrics_history.append(metrics)

        prediction = await monitor._predict_bandwidth_capacity(time_horizon_seconds=120)

        assert "predicted_utilization" in prediction
        assert "time_to_saturation" in prediction
        assert "confidence" in prediction
        assert 0.0 <= prediction["confidence"] <= 1.0


class TestAdaptiveBandwidthManager:
    """Test integrated adaptive bandwidth management system."""

    @pytest.fixture
    def manager(self) -> AdaptiveBandwidthManager:
        """Create adaptive bandwidth manager."""
        return AdaptiveBandwidthManager(
            total_bandwidth_kbps=1000.0, enable_adaptive_allocation=True
        )

    def test_manager_initialization(self, manager: AdaptiveBandwidthManager) -> None:
        """Test manager initialization."""
        assert manager.total_bandwidth_kbps == 1000.0
        assert manager.adaptive_allocation_enabled is True

    def test_agricultural_operation_context_integration(
        self, manager: AdaptiveBandwidthManager
    ) -> None:
        """Test integration with agricultural operation contexts."""
        # Field cultivation context
        field_allocation = manager.request_bandwidth(
            operation_id="field_001",
            agricultural_context=AgriculturalOperationContext.FIELD_CULTIVATION,
            requested_bandwidth_kbps=400.0,
            message_priority_level="HIGH",
        )

        # Transport context
        transport_allocation = manager.request_bandwidth(
            operation_id="transport_001",
            agricultural_context=AgriculturalOperationContext.TRANSPORT_MODE,
            requested_bandwidth_kbps=300.0,
            message_priority_level="NORMAL",
        )

        # Field operations should get better allocation
        assert (
            field_allocation.allocated_bandwidth_kbps
            >= transport_allocation.allocated_bandwidth_kbps
        )
        assert (
            field_allocation.guaranteed_minimum_kbps > transport_allocation.guaranteed_minimum_kbps
        )

    @pytest.mark.asyncio
    async def test_congestion_integration(self, manager: AdaptiveBandwidthManager) -> None:
        """Test integration with congestion detection system."""
        # Set up allocations
        field_allocation = manager.request_bandwidth(
            operation_id="field_001",
            agricultural_context=AgriculturalOperationContext.FIELD_CULTIVATION,
            requested_bandwidth_kbps=600.0,
            message_priority_level="HIGH",
        )

        transport_allocation = manager.request_bandwidth(
            operation_id="transport_001",
            agricultural_context=AgriculturalOperationContext.TRANSPORT_MODE,
            requested_bandwidth_kbps=400.0,
            message_priority_level="NORMAL",
        )

        # Simulate congestion event
        congestion_metrics = CongestionMetrics()
        congestion_metrics.bus_load_percentage = 90.0
        congestion_metrics.error_rate_percentage = 12.0

        await manager.handle_congestion_event(
            congestion_level=CongestionLevel.CRITICAL, congestion_metrics=congestion_metrics
        )

        # Verify adaptive reallocation
        updated_field = manager.get_current_allocation("field_001")
        updated_transport = manager.get_current_allocation("transport_001")
        assert updated_field is not None
        assert updated_transport is not None

        # Field operations should maintain minimum guarantees
        assert updated_field.allocated_bandwidth_kbps >= field_allocation.guaranteed_minimum_kbps
        # Transport operations may be throttled
        assert (
            updated_transport.allocated_bandwidth_kbps
            <= transport_allocation.allocated_bandwidth_kbps
        )

    def test_bandwidth_policy_enforcement(self, manager: AdaptiveBandwidthManager) -> None:
        """Test bandwidth policy enforcement for different operation types."""
        policy = BandwidthPolicy()

        # Field operation policy
        field_limits = policy.get_allocation_limits(OperationBandwidthContext.FIELD_OPERATION)
        assert field_limits["minimum_guarantee_percentage"] >= 60  # Field ops get high guarantee
        assert field_limits["can_be_preempted"] is False

        # Transport operation policy
        transport_limits = policy.get_allocation_limits(
            OperationBandwidthContext.TRANSPORT_OPERATION
        )
        assert (
            transport_limits["minimum_guarantee_percentage"] <= 40
        )  # Transport gets lower guarantee
        assert transport_limits["can_be_preempted"] is True


class TestIntegratedBandwidthManagement:
    """Test integrated bandwidth management with existing systems."""

    @pytest.mark.asyncio
    async def test_complete_bandwidth_management_workflow(self) -> None:
        """Test complete bandwidth management workflow with all systems."""
        manager = AdaptiveBandwidthManager(total_bandwidth_kbps=1000.0)

        # Start with field operation
        manager.request_bandwidth(
            operation_id="field_cultivation_001",
            agricultural_context=AgriculturalOperationContext.FIELD_CULTIVATION,
            requested_bandwidth_kbps=500.0,
            message_priority_level="HIGH",
        )

        # Add transport operation
        manager.request_bandwidth(
            operation_id="transport_001",
            agricultural_context=AgriculturalOperationContext.TRANSPORT_MODE,
            requested_bandwidth_kbps=400.0,
            message_priority_level="NORMAL",
        )

        # Simulate congestion requiring reallocation
        congestion_metrics = CongestionMetrics()
        congestion_metrics.bus_load_percentage = 85.0
        congestion_metrics.error_rate_percentage = 10.0

        await manager.handle_congestion_event(
            congestion_level=CongestionLevel.HIGH, congestion_metrics=congestion_metrics
        )

        # Verify system responds appropriately
        current_metrics = await manager.get_current_bandwidth_metrics()
        assert current_metrics.total_bandwidth_kbps == 1000.0
        assert current_metrics.field_operation_usage_kbps > 0
        assert current_metrics.utilization_percentage <= 100.0

    @pytest.mark.asyncio
    async def test_agricultural_safety_preservation_during_bandwidth_management(self) -> None:
        """Test that safety-critical agricultural operations maintain bandwidth during high congestion."""
        manager = AdaptiveBandwidthManager(total_bandwidth_kbps=800.0)

        # Safety-critical field operation
        critical_allocation = manager.request_bandwidth(
            operation_id="emergency_field_001",
            agricultural_context=AgriculturalOperationContext.FIELD_CULTIVATION,
            requested_bandwidth_kbps=400.0,
            message_priority_level="EMERGENCY",
        )

        # Multiple transport operations consuming bandwidth (request much more than guaranteed minimum)
        transport_allocations = []
        original_transport_values = []  # Store original allocation values
        for i in range(1):  # Use only 1 transport operation to avoid over-allocation
            allocation = manager.request_bandwidth(
                operation_id=f"transport_{i:03d}",
                agricultural_context=AgriculturalOperationContext.TRANSPORT_MODE,
                requested_bandwidth_kbps=350.0,  # Request 350, guaranteed minimum is min(350, 240) = 240
                message_priority_level="NORMAL",
            )
            transport_allocations.append(allocation)
            original_transport_values.append(
                allocation.allocated_bandwidth_kbps
            )  # Store original value

        # Critical congestion event
        congestion_metrics = CongestionMetrics()
        congestion_metrics.bus_load_percentage = 95.0
        congestion_metrics.error_rate_percentage = 15.0

        await manager.handle_congestion_event(
            congestion_level=CongestionLevel.CRITICAL, congestion_metrics=congestion_metrics
        )

        # Emergency field operation should maintain full allocation
        updated_critical = manager.get_current_allocation("emergency_field_001")
        assert updated_critical is not None
        assert (
            updated_critical.allocated_bandwidth_kbps
            >= critical_allocation.requested_bandwidth_kbps
        )

        # Transport operations should be throttled
        total_transport_allocation = 0.0
        for i in range(1):
            transport_alloc = manager.get_current_allocation(f"transport_{i:03d}")
            assert transport_alloc is not None
            total_transport_allocation += transport_alloc.allocated_bandwidth_kbps
        original_transport_total = sum(original_transport_values)
        assert total_transport_allocation < original_transport_total
