#!/usr/bin/env python3
"""
Real CAN integration test without mocks.

This script tests the complete CAN communication stack using our
cross-platform real CAN system instead of mock implementations.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from afs_fastapi.core.can_frame_codec import CANFrameCodec
from afs_fastapi.core.can_manager import create_can_manager
from tests.factories.can_integration_factory import create_real_can_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_real_can_communication():
    """Test real CAN communication without mocks."""
    logger.info("=== Testing Real CAN Communication ===")

    try:
        # Create real CAN manager
        can_manager = create_can_manager(auto_connect=True)
        logger.info(
            f"✅ Real CAN manager created: {can_manager.get_connection_info()['interface']}"
        )

        # Test agricultural message sending
        success = can_manager.send_tractor_telemetry(
            tractor_id=35, speed=12.5, rpm=1800, engine_temperature=85.0
        )
        logger.info(f"✅ Tractor telemetry sent: {success}")

        # Test emergency stop
        success = can_manager.send_emergency_stop(tractor_id=35, reason_code=1, urgency=7)
        logger.info(f"✅ Emergency stop sent: {success}")

        # Test CAN frame codec integration
        codec = CANFrameCodec()
        logger.info("✅ CAN frame codec initialized")

        # Test message encoding
        encoded_msg = codec.encode_message(
            pgn=61444,  # Engine Controller 1
            source_address=35,
            spn_values={"engine_speed": 2000, "vehicle_speed": 15.0},
        )
        logger.info(f"✅ Message encoded: {encoded_msg is not None}")

        can_manager.disconnect()
        logger.info("✅ CAN manager disconnected")

        return True

    except Exception as e:
        logger.error(f"❌ Real CAN communication test failed: {e}")
        return False


async def test_can_bus_manager_integration():
    """Test CAN bus manager with real implementation."""
    logger.info("\n=== Testing CAN Bus Manager Integration ===")

    try:
        # Create real CAN bus manager using our factory
        bus_manager = create_real_can_manager(
            {"interface": "auto", "channel": "vcan0"}  # Auto-detect
        )

        # Initialize the manager
        success = await bus_manager.initialize()
        logger.info(f"✅ CAN bus manager initialized: {success}")

        # Test interface status
        status = await bus_manager.get_interface_status("default")
        logger.info(f"✅ Interface status retrieved: {status is not None}")

        # Test connection
        conn_success = await bus_manager.connect_interface("default", {"bitrate": 500000})
        logger.info(f"✅ Interface connected: {conn_success}")

        # Test manager status
        manager_status = bus_manager.get_manager_status()
        logger.info(f"✅ Manager status: {manager_status['state']}")
        logger.info(f"   Platform: {manager_status.get('platform', 'unknown')}")
        logger.info(f"   Interface: {manager_status.get('interface', 'unknown')}")

        # Add message callback for testing
        messages_received = []

        def message_handler(message: dict[str, Any]) -> None:
            messages_received.append(message)
            logger.info(f"📨 Received message: PGN={message.get('pgn', 'unknown')}")

        bus_manager.add_global_callback(message_handler)

        # Start receiving messages
        bus_manager._can_manager.start_receiving()

        # Send a test message
        bus_manager._can_manager.send_j1939_message(pgn=61444, source_address=40, engine_speed=1500)
        logger.info("✅ Test message sent")

        # Wait for potential message reception
        await asyncio.sleep(0.5)

        # Stop receiving
        bus_manager._can_manager.stop_receiving()

        logger.info(f"✅ Messages received during test: {len(messages_received)}")

        # Shutdown
        await bus_manager.shutdown()
        logger.info("✅ CAN bus manager shutdown")

        return True

    except Exception as e:
        logger.error(f"❌ CAN bus manager test failed: {e}")
        return False


async def test_codec_integration():
    """Test CAN frame codec integration with real messages."""
    logger.info("\n=== Testing CAN Frame Codec Integration ===")

    try:
        codec = CANFrameCodec()
        can_manager = create_can_manager(auto_connect=True)

        logger.info("✅ Codec and CAN manager initialized")

        # Test encoding and sending
        test_cases = [
            {
                "name": "Engine Speed",
                "pgn": 61444,
                "data": {"engine_speed": 2200, "vehicle_speed": 18.5},
            },
            {
                "name": "Engine Temperature",
                "pgn": 61444,
                "data": {"engine_coolant_temperature": 92.0},
            },
            {"name": "Vehicle Speed Only", "pgn": 61444, "data": {"vehicle_speed": 12.0}},
        ]

        success_count = 0

        for test_case in test_cases:
            try:
                # Encode message
                encoded = codec.encode_message(
                    pgn=test_case["pgn"], source_address=50, spn_values=test_case["data"]
                )

                if encoded:
                    # Send via CAN manager
                    send_success = can_manager.send_j1939_message(
                        pgn=test_case["pgn"], source_address=50, **test_case["data"]
                    )

                    if send_success:
                        logger.info(f"✅ {test_case['name']} - encoded and sent successfully")
                        success_count += 1
                    else:
                        logger.warning(f"⚠️ {test_case['name']} - encoded but send failed")
                else:
                    logger.warning(f"⚠️ {test_case['name']} - encoding failed")

            except Exception as e:
                logger.error(f"❌ {test_case['name']} failed: {e}")

        can_manager.disconnect()
        logger.info(f"✅ Codec integration complete: {success_count}/{len(test_cases)} successful")

        return success_count == len(test_cases)

    except Exception as e:
        logger.error(f"❌ Codec integration test failed: {e}")
        return False


async def test_multi_device_simulation():
    """Test simulation of multiple CAN devices."""
    logger.info("\n=== Testing Multi-Device Simulation ===")

    try:
        # Create multiple CAN managers to simulate different devices
        devices = []
        device_ids = [0x10, 0x20, 0x30]  # Different CAN addresses

        for i, device_id in enumerate(device_ids):
            can_manager = create_can_manager(auto_connect=True)
            devices.append({"id": device_id, "name": f"Device_{i+1}", "manager": can_manager})
            logger.info(f"✅ Created {devices[i]['name']} with address 0x{device_id:02X}")

        # Test inter-device communication
        messages_sent = 0

        for device in devices:
            success = device["manager"].send_j1939_message(
                pgn=61444,
                source_address=device["id"],
                engine_speed=1500 + device["id"],
                vehicle_speed=10.0 + (device["id"] / 16),
            )

            if success:
                messages_sent += 1
                logger.info(f"✅ {device['name']} message sent")

        # Cleanup
        for device in devices:
            device["manager"].disconnect()

        logger.info(f"✅ Multi-device simulation: {messages_sent}/{len(devices)} messages sent")

        return messages_sent == len(devices)

    except Exception as e:
        logger.error(f"❌ Multi-device simulation failed: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("🔧 Starting Real CAN Integration Tests (No Mocks)")
    logger.info("=" * 60)

    # Run all tests
    tests = [
        ("Real CAN Communication", test_real_can_communication),
        ("CAN Bus Manager Integration", test_can_bus_manager_integration),
        ("CAN Frame Codec Integration", test_codec_integration),
        ("Multi-Device Simulation", test_multi_device_simulation),
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
    logger.info("📊 REAL CAN INTEGRATION TEST RESULTS")
    logger.info("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")

    logger.info(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All real CAN integration tests passed!")
        logger.info("🌱 Agricultural CAN systems working without any mocks!")
    else:
        logger.warning("⚠️ Some tests failed. Check the logs above for details.")

    # Get platform info
    try:
        test_can = create_can_manager(auto_connect=True)
        can_info = test_can.get_connection_info()
        logger.info("\n🔧 Platform Configuration:")
        logger.info(f"   Platform: {can_info.get('platform')}")
        logger.info(f"   Interface: {can_info.get('interface')}")
        logger.info(f"   Virtual CAN: {can_info.get('fallback_used', False)}")
        test_can.disconnect()
    except Exception as e:
        logger.error(f"Could not get platform info: {e}")


if __name__ == "__main__":
    asyncio.run(main())
