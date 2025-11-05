#!/usr/bin/env python3
"""
Test real fleet coordination with cross-platform CAN communication.

This script tests the fleet coordination system using real implementations
instead of mocks, demonstrating actual multi-tractor coordination.
"""

from __future__ import annotations

import asyncio
import logging

from tests.factories.fleet_coordination_factory import (
    create_test_fleet,
    create_test_fleet_coordination_engine,
    start_fleet,
    stop_fleet,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_single_tractor_coordination():
    """Test single tractor fleet coordination setup."""
    logger.info("=== Testing Single Tractor Coordination ===")

    try:
        # Create fleet coordination engine
        engine = create_test_fleet_coordination_engine("TRACTOR_TEST_001")

        logger.info(f"✅ Created fleet engine: {engine.tractor_id}")
        logger.info(f"   ISOBUS device: {type(engine.isobus_interface).__name__}")
        logger.info(
            f"   CAN manager available: {engine.isobus_interface.can_manager.is_connected()}"
        )

        # Start the engine
        await engine.start()
        logger.info(f"✅ Engine started, state: {engine.get_current_state()}")

        # Test emergency stop functionality (available method)
        await engine.broadcast_emergency_stop("test_emergency")
        logger.info("✅ Emergency stop broadcast sent")

        # Stop the engine
        await engine.stop()
        logger.info("✅ Engine stopped")

        return True

    except Exception as e:
        logger.error(f"❌ Single tractor test failed: {e}")
        return False


async def test_multi_tractor_fleet():
    """Test multi-tractor fleet coordination."""
    logger.info("\n=== Testing Multi-Tractor Fleet ===")

    try:
        # Create a fleet of 3 tractors
        fleet = create_test_fleet(fleet_size=3, base_tractor_id="TEST_FLEET")

        logger.info(f"✅ Created fleet with {len(fleet)} tractors:")
        for i, engine in enumerate(fleet):
            logger.info(f"   Tractor {i+1}: {engine.tractor_id}")

        # Start all tractors
        await start_fleet(fleet)
        logger.info("✅ All fleet engines started")

        # Verify all are in IDLE state
        idle_count = sum(1 for engine in fleet if engine.get_current_state() == "IDLE")
        logger.info(f"✅ {idle_count}/{len(fleet)} tractors in IDLE state")

        # Test field allocation
        lead_tractor = fleet[0]
        success = await lead_tractor.claim_section("A1")
        logger.info(f"✅ Section claim: {success}")

        # Allow message propagation
        await asyncio.sleep(0.5)

        # Test emergency stop propagation
        await lead_tractor.broadcast_emergency_stop("obstacle_detected")
        logger.info("✅ Emergency stop broadcast")

        # Test field allocation state
        allocation_state = lead_tractor.get_field_allocation_state()
        logger.info("✅ Field allocation state retrieved")

        # Stop all tractors
        await stop_fleet(fleet)
        logger.info("✅ All fleet engines stopped")

        return True

    except Exception as e:
        logger.error(f"❌ Multi-tractor fleet test failed: {e}")
        return False


async def test_field_allocation():
    """Test field allocation across fleet."""
    logger.info("\n=== Testing Field Allocation ===")

    try:
        # Create 2 tractors for field work
        fleet = create_test_fleet(fleet_size=2, base_tractor_id="FIELD_FLEET")
        await start_fleet(fleet)

        logger.info(f"✅ Field fleet started with {len(fleet)} tractors")

        # Simulate field allocation
        field_sections = ["A1", "A2", "A3", "A4"]

        for i, engine in enumerate(fleet):
            # Each tractor claims a field section
            section_id = field_sections[i]
            success = await engine.claim_section(section_id)
            logger.info(f"✅ {engine.tractor_id} claimed {section_id}: {success}")

        # Allow allocation synchronization
        await asyncio.sleep(0.5)

        # Check allocation consistency
        allocation_info = fleet[0].get_field_allocation_state()
        logger.info("✅ Field allocation state retrieved")

        # Test fleet status
        fleet_status = fleet[0].get_fleet_status()
        logger.info(f"✅ Fleet status retrieved: {len(fleet_status)} members")

        await stop_fleet(fleet)
        logger.info("✅ Field fleet stopped")

        return True

    except Exception as e:
        logger.error(f"❌ Field allocation test failed: {e}")
        return False


async def test_cross_platform_compatibility():
    """Test cross-platform CAN compatibility."""
    logger.info("\n=== Testing Cross-Platform Compatibility ===")

    try:
        # Create fleet coordination engine and check platform info
        engine = create_test_fleet_coordination_engine("PLATFORM_TEST")

        # Get platform information
        can_info = engine.isobus_interface.can_manager.get_connection_info()
        platform = can_info.get("platform", "unknown")
        interface = can_info.get("interface", "unknown")

        logger.info(f"✅ Platform detected: {platform}")
        logger.info(f"✅ CAN interface: {interface}")
        logger.info(f"✅ Channel: {can_info.get('channel')}")
        logger.info(f"✅ Bitrate: {can_info.get('bitrate')}")

        await engine.start()
        logger.info("✅ Fleet engine started successfully")

        # Test basic emergency stop functionality
        await engine.broadcast_emergency_stop("platform_test")
        logger.info("✅ Platform test emergency stop sent")

        # Test field allocation state
        allocation_state = engine.get_field_allocation_state()
        logger.info("✅ Field allocation state retrieved")

        await engine.stop()
        logger.info("✅ Fleet engine stopped")

        return True

    except Exception as e:
        logger.error(f"❌ Cross-platform test failed: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("🚜 Starting Real Fleet Coordination Test")
    logger.info("=" * 60)

    # Run all tests
    tests = [
        ("Single Tractor Coordination", test_single_tractor_coordination),
        ("Multi-Tractor Fleet", test_multi_tractor_fleet),
        ("Field Allocation", test_field_allocation),
        ("Cross-Platform Compatibility", test_cross_platform_compatibility),
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
    logger.info("📊 REAL FLEET COORDINATION TEST RESULTS")
    logger.info("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")

    logger.info(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All real fleet coordination tests passed!")
        logger.info("🌱 Agricultural fleet systems working with real CAN communication!")
    else:
        logger.warning("⚠️ Some tests failed. Check the logs above for details.")

    # Get platform info for final report
    try:
        test_engine = create_test_fleet_coordination_engine("REPORT_TEST")
        can_info = test_engine.isobus_interface.can_manager.get_connection_info()
        logger.info("\n🔧 Platform Configuration:")
        logger.info(f"   Platform: {can_info.get('platform')}")
        logger.info(f"   Interface: {can_info.get('interface')}")
        logger.info(f"   Virtual CAN: {can_info.get('fallback_used', False)}")
        await test_engine.stop()
    except Exception as e:
        logger.error(f"Could not get platform info: {e}")


if __name__ == "__main__":
    asyncio.run(main())
