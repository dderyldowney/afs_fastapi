"""
Real service test factory for agricultural robotics.

This module provides real implementations for service testing, replacing
mocks with actual functional components across all agricultural systems.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from afs_fastapi.services.field_allocation import FieldAllocationCRDT
from afs_fastapi.services.fleet import FleetCoordinationEngine
from afs_fastapi.services.synchronization import VectorClock
from tests.factories.fleet_coordination_factory import (
    TestISOBUSDevice,
    create_test_fleet_coordination_engine,
)

logger = logging.getLogger(__name__)


class ServiceTestFactory:
    """Factory for creating service components.

    This factory provides implementations of agricultural service
    components for integration testing.
    """

    @staticmethod
    def create_fleet_coordination_engine(
        tractor_id: str, auto_start: bool = False, with_real_can: bool = True
    ) -> FleetCoordinationEngine:
        """Create a real fleet coordination engine.

        Parameters
        ----------
        tractor_id : str
            Unique identifier for the tractor
        auto_start : bool, default False
            Whether to automatically start the engine
        with_real_can : bool, default True
            Whether to use real CAN communication

        Returns
        -------
        FleetCoordinationEngine
            Real fleet coordination engine
        """
        if with_real_can:
            return create_test_fleet_coordination_engine(tractor_id, auto_start=auto_start)
        else:
            # Create with minimal ISOBUS device for isolated testing
            isobus_device = TestISOBUSDevice(tractor_id)
            return FleetCoordinationEngine(tractor_id, isobus_device)

    @staticmethod
    def create_vector_clock(process_ids: list[str]) -> VectorClock:
        """Create a real vector clock for distributed coordination.

        Parameters
        ----------
        process_ids : list[str]
            List of process IDs (tractor IDs)

        Returns
        -------
        VectorClock
            Real vector clock implementation
        """
        return VectorClock(process_ids)

    @staticmethod
    def create_field_allocation_crdt(
        field_id: str = "test_field", tractor_ids: list[str] | None = None
    ) -> FieldAllocationCRDT:
        """Create a real field allocation CRDT.

        Parameters
        ----------
        field_id : str, default "test_field"
            Field identifier
        tractor_ids : list[str], optional
            List of tractor IDs. If None, uses default.

        Returns
        -------
        FieldAllocationCRDT
            Real field allocation CRDT implementation
        """
        if tractor_ids is None:
            tractor_ids = ["TRACTOR_001", "TRACTOR_002", "TRACTOR_003"]

        return FieldAllocationCRDT(field_id=field_id, tractor_ids=tractor_ids)

    @staticmethod
    async def create_fleet_cluster(
        fleet_size: int = 3, base_tractor_id: str = "TEST_FLEET", auto_start: bool = False
    ) -> list[FleetCoordinationEngine]:
        """Create a cluster of fleet coordination engines.

        Parameters
        ----------
        fleet_size : int, default 3
            Number of tractors in the fleet
        base_tractor_id : str, default "TEST_FLEET"
            Base name for tractor IDs
        auto_start : bool, default False
            Whether to automatically start all engines

        Returns
        -------
        list[FleetCoordinationEngine]
            List of real fleet coordination engines
        """
        fleet = []

        for i in range(fleet_size):
            tractor_id = f"{base_tractor_id}_{i+1:03d}"
            engine = ServiceTestFactory.create_fleet_coordination_engine(
                tractor_id=tractor_id, auto_start=False
            )
            fleet.append(engine)

        if auto_start:
            start_tasks = [engine.start() for engine in fleet]
            await asyncio.gather(*start_tasks)

        return fleet

    @staticmethod
    async def simulate_fleet_operation(
        fleet: list[FleetCoordinationEngine], operation_duration: float = 1.0
    ) -> dict[str, Any]:
        """Simulate fleet operation with real communication.

        Parameters
        ----------
        fleet : list[FleetCoordinationEngine]
            Fleet of coordination engines
        operation_duration : float, default 1.0
            Duration of simulation in seconds

        Returns
        -------
        dict[str, Any]
            Operation results and statistics
        """
        results = {
            "fleet_size": len(fleet),
            "operation_duration": operation_duration,
            "messages_sent": 0,
            "state_changes": 0,
            "errors": [],
        }

        try:
            # Start all engines
            await ServiceTestFactory.start_fleet(fleet)

            # Simulate field allocation
            field_sections = ["A1", "A2", "A3", "A4", "A5", "A6"]

            for i, engine in enumerate(fleet):
                section_id = field_sections[i % len(field_sections)]
                try:
                    success = await engine.claim_section(section_id)
                    if success:
                        results["messages_sent"] += 1
                        logger.info(f"✅ {engine.tractor_id} claimed {section_id}")
                    else:
                        results["errors"].append(
                            f"{engine.tractor_id} failed to claim {section_id}"
                        )
                except Exception as e:
                    results["errors"].append(f"{engine.tractor_id} error: {e}")

            # Let operations run
            await asyncio.sleep(operation_duration)

            # Test emergency stop propagation
            try:
                lead_tractor = fleet[0]
                await lead_tractor.broadcast_emergency_stop("test_simulation")
                results["messages_sent"] += 1
                logger.info("✅ Emergency stop broadcast successful")
            except Exception as e:
                results["errors"].append(f"Emergency stop failed: {e}")

            # Stop all engines
            await ServiceTestFactory.stop_fleet(fleet)

        except Exception as e:
            results["errors"].append(f"Fleet operation error: {e}")

        return results

    @staticmethod
    async def start_fleet(fleet: list[FleetCoordinationEngine]) -> None:
        """Start all engines in a fleet.

        Parameters
        ----------
        fleet : list[FleetCoordinationEngine]
            Fleet of coordination engines
        """
        start_tasks = [engine.start() for engine in fleet]
        await asyncio.gather(*start_tasks)

    @staticmethod
    async def stop_fleet(fleet: list[FleetCoordinationEngine]) -> None:
        """Stop all engines in a fleet.

        Parameters
        ----------
        fleet : list[FleetCoordinationEngine]
            Fleet of coordination engines
        """
        stop_tasks = [engine.stop() for engine in fleet]
        await asyncio.gather(*stop_tasks)


# Convenience functions for backward compatibility
def create_real_fleet_engine(tractor_id: str, **kwargs) -> FleetCoordinationEngine:
    """Create a real fleet engine (backward compatibility)."""
    return ServiceTestFactory.create_fleet_coordination_engine(tractor_id, **kwargs)


def create_real_vector_clock(process_ids: list[str]) -> VectorClock:
    """Create a real vector clock (backward compatibility)."""
    return ServiceTestFactory.create_vector_clock(process_ids)


def create_real_field_crdt(**kwargs) -> FieldAllocationCRDT:
    """Create a real field allocation CRDT (backward compatibility)."""
    return ServiceTestFactory.create_field_allocation_crdt(**kwargs)


class ImplementationFactory:
    """Factory for creating real implementations.

    This class provides real implementations for common patterns
    in existing tests, migrating from mocks to actual implementations.
    """

    @staticmethod
    def create_async_implementation(*args, **kwargs) -> Any:
        """Create real async implementations."""
        # Determine what type of object is being mocked
        if args and hasattr(args[0], "__name__"):
            class_name = args[0].__name__

            if "ISOBUS" in class_name or "isobus" in class_name.lower():
                return TestISOBUSDevice("TEST_TRACTOR")
            elif "Fleet" in class_name or "fleet" in class_name.lower():
                return create_real_fleet_engine("TEST_FLEET_ENGINE")
            elif "VectorClock" in class_name:
                return create_real_vector_clock(["TEST_PROCESS"])
            elif "FieldAllocation" in class_name:
                return create_real_field_crdt()

        # Fallback to simple async object
        class SimpleAsyncObject:
            async def __call__(self, *args, **kwargs):
                return True

            async def start(self):
                pass

            async def stop(self):
                pass

        return SimpleAsyncObject()

    @staticmethod
    def Mock(*args, **kwargs) -> Any:
        """Replace Mock with real synchronous implementations."""
        if args and hasattr(args[0], "__name__"):
            class_name = args[0].__name__

            if "VectorClock" in class_name:
                return create_real_vector_clock(["TEST_PROCESS"])
            elif "FieldAllocation" in class_name:
                return create_real_field_crdt()

        # Fallback to simple object
        class SimpleObject:
            def __call__(self, *args, **kwargs):
                return True

        return SimpleObject()
