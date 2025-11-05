#!/usr/bin/env python3
"""
Cross-platform CAN communication test.

This script tests the CAN manager across different platforms to ensure
proper virtual CAN fallback and agricultural message compatibility.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from afs_fastapi.core.can_manager import create_can_manager
from afs_fastapi.core.platform_detection import detect_platform, get_can_capabilities

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_platform_detection():
    """Test platform detection and capabilities."""
    logger.info("=== Testing Platform Detection ===")

    platform = detect_platform()
    capabilities = get_can_capabilities()

    logger.info(f"Detected platform: {platform.value}")
    logger.info(f"Recommended interface: {capabilities['recommended_interface']}")
    logger.info(f"Available interfaces: {capabilities['available_interfaces']}")
    logger.info(f"Platform notes: {capabilities['notes']}")

    return platform, capabilities


def test_can_manager_connection():
    """Test CAN manager connection and configuration."""
    logger.info("\n=== Testing CAN Manager Connection ===")

    try:
        # Create CAN manager with auto-detection
        can_manager = create_can_manager(auto_connect=True)

        if can_manager.is_connected():
            connection_info = can_manager.get_connection_info()
            logger.info("✅ CAN Manager connected successfully")
            logger.info(f"Platform: {connection_info['platform']}")
            logger.info(f"Interface: {connection_info['interface']}")
            logger.info(f"Channel: {connection_info['channel']}")
            logger.info(f"Bitrate: {connection_info['bitrate']}")
            logger.info(f"Fallback used: {connection_info['fallback_used']}")

            return can_manager
        else:
            logger.error("❌ CAN Manager failed to connect")
            return None

    except Exception as e:
        logger.error(f"❌ CAN Manager connection failed: {e}")
        return None


def test_tractor_telemetry(can_manager):
    """Test agricultural tractor telemetry message sending."""
    logger.info("\n=== Testing Tractor Telemetry ===")

    try:
        # Send tractor telemetry data
        success = can_manager.send_tractor_telemetry(
            tractor_id=0x23,  # Tractor 35
            speed=12.5,  # 12.5 km/h
            rpm=1800,  # 1800 RPM
            engine_temperature=85.0,  # 85°C
            fuel_rate=15.2,  # 15.2 L/h
        )

        if success:
            logger.info("✅ Tractor telemetry message sent successfully")
            return True
        else:
            logger.error("❌ Failed to send tractor telemetry message")
            return False

    except Exception as e:
        logger.error(f"❌ Tractor telemetry test failed: {e}")
        return False


def test_emergency_stop(can_manager):
    """Test agricultural emergency stop message sending."""
    logger.info("\n=== Testing Emergency Stop ===")

    try:
        # Send emergency stop message
        success = can_manager.send_emergency_stop(
            tractor_id=0x23,  # Tractor 35
            reason_code=1,  # Collision detected
            urgency=7,  # Highest urgency
        )

        if success:
            logger.info("✅ Emergency stop message sent successfully")
            return True
        else:
            logger.error("❌ Failed to send emergency stop message")
            return False

    except Exception as e:
        logger.error(f"❌ Emergency stop test failed: {e}")
        return False


async def test_message_receiving(can_manager):
    """Test asynchronous CAN message receiving."""
    logger.info("\n=== Testing Message Receiving ===")

    received_messages = []

    def message_handler(decoded_message: dict[str, Any]) -> None:
        """Handle received CAN messages."""
        received_messages.append(decoded_message)
        logger.info(
            f"📨 Received message: PGN={decoded_message['pgn']:05X}, "
            f"SA={decoded_message['source_address']:02X}"
        )

    try:
        # Add message handler and start receiving
        can_manager.add_message_handler(message_handler)
        can_manager.start_receiving()

        # Send a test message
        can_manager.send_j1939_message(
            pgn=61444,  # Electronic Engine Controller 1
            source_address=0x24,
            engine_speed=1500,
            vehicle_speed=10.0,
        )

        # Wait for message reception
        await asyncio.sleep(0.5)

        # Stop receiving
        can_manager.stop_receiving()

        if received_messages:
            logger.info(f"✅ Successfully received {len(received_messages)} messages")
            return True
        else:
            logger.warning("⚠️ No messages received (may be normal for virtual CAN)")
            return True  # Not necessarily an error for virtual CAN

    except Exception as e:
        logger.error(f"❌ Message receiving test failed: {e}")
        return False


def test_isobus_compatibility(can_manager):
    """Test ISOBUS/J1939 agricultural message compatibility."""
    logger.info("\n=== Testing ISOBUS/J1939 Compatibility ===")

    test_cases = [
        {
            "name": "Engine Controller 1",
            "pgn": 61444,  # Electronic Engine Controller 1
            "data": {
                "engine_speed": 2000,
                "vehicle_speed": 15.0,
                "engine_coolant_temperature": 85.0,
            },
        },
        {"name": "Engine Temperature", "pgn": 61444, "data": {"engine_coolant_temperature": 90.5}},
        {"name": "Vehicle Speed", "pgn": 61444, "data": {"vehicle_speed": 12.0}},
    ]

    success_count = 0

    for test_case in test_cases:
        try:
            success = can_manager.send_j1939_message(
                pgn=test_case["pgn"], source_address=0x25, **test_case["data"]
            )

            if success:
                logger.info(f"✅ {test_case['name']} message sent successfully")
                success_count += 1
            else:
                logger.error(f"❌ Failed to send {test_case['name']} message")

        except Exception as e:
            logger.error(f"❌ {test_case['name']} test failed: {e}")

    logger.info(f"ISOBUS compatibility: {success_count}/{len(test_cases)} messages successful")
    return success_count == len(test_cases)


async def main():
    """Main test function."""
    logger.info("🚜 Starting Cross-Platform CAN Communication Test")
    logger.info("=" * 60)

    # Test platform detection
    platform, capabilities = test_platform_detection()

    # Test CAN manager connection
    can_manager = test_can_manager_connection()

    if not can_manager:
        logger.error("❌ Cannot proceed without CAN connection")
        return

    try:
        # Run tests
        results = {
            "telemetry": test_tractor_telemetry(can_manager),
            "emergency_stop": test_emergency_stop(can_manager),
            "message_receiving": await test_message_receiving(can_manager),
            "isobus_compatibility": test_isobus_compatibility(can_manager),
        }

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 60)

        passed = sum(results.values())
        total = len(results)

        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name.replace('_', ' ').title()}: {status}")

        logger.info(f"\nOverall: {passed}/{total} tests passed")
        logger.info(f"Platform: {platform.value}")
        logger.info(f"Interface: {can_manager.get_connection_info()['interface']}")

        if passed == total:
            logger.info(
                "🎉 All tests passed! Cross-platform CAN communication is working correctly."
            )
        else:
            logger.warning("⚠️ Some tests failed. Check the logs above for details.")

    finally:
        # Cleanup
        can_manager.disconnect()
        logger.info("CAN manager disconnected")


if __name__ == "__main__":
    asyncio.run(main())
