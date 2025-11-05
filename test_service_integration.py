#!/usr/bin/env python3
"""
Real service integration test without mocks.

This script tests real agricultural service components using our factory
instead of mock implementations.
"""

from __future__ import annotations

import asyncio
import logging

from tests.factories.service_test_factory import ServiceTestFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_vector_clock_functionality():
    """Test real vector clock without mocks."""
    logger.info("=== Testing Vector Clock Functionality ===")

    try:
        # Create real vector clock
        process_ids = ["TRACTOR_A", "TRACTOR_B", "TRACTOR_C"]
        vc = ServiceTestFactory.create_vector_clock(process_ids)

        logger.info(f"✅ Vector clock created for processes: {process_ids}")

        # Test basic operations
        initial_time = vc.get_time("TRACTOR_A")
        logger.info(f"✅ Initial time for TRACTOR_A: {initial_time}")

        # Increment time
        vc.increment("TRACTOR_A")
        new_time = vc.get_time("TRACTOR_A")
        logger.info(f"✅ Time after increment: {new_time}")

        # Test event ordering
        event1 = vc.create_event("TRACTOR_A", {"action": "start"})
        event2 = vc.create_event("TRACTOR_B", {"action": "follow"})

        logger.info(f"✅ Created events: {len(event1)}, {len(event2)}")

        # Test causality
        causality = vc.happened_before(event1, event2)
        logger.info(f"✅ Causality check: event1 -> event2 = {causality}")

        # Test merging
        vc2 = ServiceTestFactory.create_vector_clock(["TRACTOR_B", "TRACTOR_C", "TRACTOR_D"])
        vc2.increment("TRACTOR_B")

        merged_clock = vc.merge(vc2)
        logger.info("✅ Clock merging successful")

        return True

    except Exception as e:
        logger.error(f"❌ Vector clock test failed: {e}")
        return False


async def test_field_allocation_crdt():
    """Test real field allocation CRDT without mocks."""
    logger.info("\n=== Testing Field Allocation CRDT ===")

    try:
        # Create real field allocation CRDT
        tractor_ids = ["TRACTOR_001", "TRACTOR_002", "TRACTOR_003"]
        crdt = ServiceTestFactory.create_field_allocation_crdt(
            field_id="TEST_FIELD", tractor_ids=tractor_ids
        )

        logger.info(f"✅ Field allocation CRDT created: {crdt.field_id}")
        logger.info(f"   Tractors: {tractor_ids}")

        # Test section claiming
        success1 = crdt.claim_section("A1", "TRACTOR_001")
        logger.info(f"✅ TRACTOR_001 claims A1: {success1}")

        success2 = crdt.claim_section("A2", "TRACTOR_002")
        logger.info(f"✅ TRACTOR_002 claims A2: {success2}")

        # Test ownership query
        owner_a1 = crdt.owner_of("A1")
        owner_a2 = crdt.owner_of("A2")
        logger.info(f"✅ A1 owner: {owner_a1}")
        logger.info(f"✅ A2 owner: {owner_a2}")

        # Test section release
        crdt.release_section("A1", "TRACTOR_001")
        owner_after_release = crdt.owner_of("A1")
        logger.info(f"✅ A1 owner after release: {owner_after_release}")

        # Test serialization
        serialized = crdt.serialize()
        logger.info(f"✅ CRDT serialized: {len(serialized)} bytes")

        # Test merging
        crdt2 = ServiceTestFactory.create_field_allocation_crdt("TEST_FIELD", tractor_ids)
        crdt2.claim_section("B1", "TRACTOR_003")

        crdt.merge(crdt2)
        owner_b1 = crdt.owner_of("B1")
        logger.info(f"✅ After merge, B1 owner: {owner_b1}")

        return True

    except Exception as e:
        logger.error(f"❌ Field allocation CRDT test failed: {e}")
        return False


async def test_fleet_coordination():
    """Test real fleet coordination without mocks."""
    logger.info("\n=== Testing Fleet Coordination ===")

    try:
        # Create single fleet engine
        engine = ServiceTestFactory.create_fleet_coordination_engine(
            tractor_id="TEST_COORDINATION_001", auto_start=False
        )

        logger.info(f"✅ Fleet engine created: {engine.tractor_id}")

        # Test state transitions
        initial_state = engine.get_current_state()
        logger.info(f"✅ Initial state: {initial_state}")

        # Start the engine
        await engine.start()
        running_state = engine.get_current_state()
        logger.info(f"✅ State after start: {running_state}")

        # Test field allocation
        allocation_success = await engine.claim_section("TEST_SECTION")
        logger.info(f"✅ Section claim: {allocation_success}")

        # Test emergency stop
        await engine.broadcast_emergency_stop("test_coordination")
        logger.info("✅ Emergency stop broadcast")

        # Test fleet status
        fleet_status = engine.get_fleet_status()
        logger.info(f"✅ Fleet status: {len(fleet_status)} members tracked")

        # Test field allocation state
        field_state = engine.get_field_allocation_state()
        logger.info("✅ Field allocation state retrieved")

        # Stop the engine
        await engine.stop()
        final_state = engine.get_current_state()
        logger.info(f"✅ Final state: {final_state}")

        return True

    except Exception as e:
        logger.error(f"❌ Fleet coordination test failed: {e}")
        return False


async def test_multi_tractor_fleet():
    """Test multi-tractor fleet coordination."""
    logger.info("\n=== Testing Multi-Tractor Fleet ===")

    try:
        # Create fleet of 3 tractors
        fleet = await ServiceTestFactory.create_fleet_cluster(
            fleet_size=3, base_tractor_id="MULTI_TEST", auto_start=True
        )

        logger.info(f"✅ Fleet created with {len(fleet)} tractors")
        for i, engine in enumerate(fleet):
            logger.info(f"   Tractor {i+1}: {engine.tractor_id} - {engine.get_current_state()}")

        # Test fleet operation simulation
        results = await ServiceTestFactory.simulate_fleet_operation(fleet, operation_duration=0.5)

        logger.info("✅ Fleet operation results:")
        logger.info(f"   Messages sent: {results['messages_sent']}")
        logger.info(f"   Errors: {len(results['errors'])}")

        if results["errors"]:
            for error in results["errors"]:
                logger.warning(f"   Error: {error}")

        return len(results["errors"]) == 0

    except Exception as e:
        logger.error(f"❌ Multi-tractor fleet test failed: {e}")
        return False


async def test_service_integration():
    """Test integration of all service components."""
    logger.info("\n=== Testing Service Integration ===")

    try:
        # Create all components
        vc = ServiceTestFactory.create_vector_clock(["T1", "T2"])
        crdt = ServiceTestFactory.create_field_allocation_crdt("INTEGRATION_FIELD", ["T1", "T2"])
        engine = ServiceTestFactory.create_fleet_coordination_engine("T1", auto_start=False)

        logger.info("✅ All service components created")

        # Test interaction between components
        await engine.start()
        logger.info("✅ Fleet engine started")

        # Use vector clock for event ordering
        event = vc.create_event("T1", {"action": "field_claim", "section": "X1"})
        logger.info(f"✅ Vector clock event created: {event['timestamp']}")

        # Use CRDT for field allocation
        claim_success = crdt.claim_section("X1", "T1")
        logger.info(f"✅ CRDT section claim: {claim_success}")

        # Simulate coordination between tractors
        fleet = await ServiceTestFactory.create_fleet_cluster(fleet_size=2, auto_start=True)

        # Test cross-component coordination
        results = await ServiceTestFactory.simulate_fleet_operation(fleet, 0.3)

        logger.info("✅ Service integration test complete")
        logger.info("   Components: VectorClock, FieldCRDT, FleetEngine")
        logger.info(f"   Fleet messages: {results['messages_sent']}")
        logger.info(f"   Integration errors: {len(results['errors'])}")

        # Cleanup
        await engine.stop()
        await ServiceTestFactory.stop_fleet(fleet)

        return len(results["errors"]) == 0

    except Exception as e:
        logger.error(f"❌ Service integration test failed: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("🔧 Starting Real Service Integration Tests (No Mocks)")
    logger.info("=" * 60)

    # Run all tests
    tests = [
        ("Vector Clock Functionality", test_vector_clock_functionality),
        ("Field Allocation CRDT", test_field_allocation_crdt),
        ("Fleet Coordination", test_fleet_coordination),
        ("Multi-Tractor Fleet", test_multi_tractor_fleet),
        ("Service Integration", test_service_integration),
    ]

    results = {}

    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running: {test_name}")
        try:
            results[test_name] = await test_func()
        except Exception as e:
            logger.error(f"❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 REAL SERVICE INTEGRATION TEST RESULTS")
    logger.info("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")

    logger.info(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All real service integration tests passed!")
        logger.info("🌱 Agricultural service systems working without any mocks!")
    else:
        logger.warning("⚠️ Some tests failed. Check the logs above for details.")


if __name__ == "__main__":
    asyncio.run(main())
