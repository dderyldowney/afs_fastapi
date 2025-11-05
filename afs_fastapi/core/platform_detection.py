"""Platform detection utility for CAN interface selection.

This module provides cross-platform CAN interface detection and selection,
ensuring optimal CAN communication regardless of the underlying operating system.
"""

from __future__ import annotations

import logging
import platform
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class PlatformType(Enum):
    """Supported platform types for CAN communication."""

    LINUX = "linux"
    MACOS = "macos"
    WINDOWS = "windows"
    UNKNOWN = "unknown"


class CANInterfaceCapability(Enum):
    """CAN interface capabilities by platform."""

    SOCKETCAN_AVAILABLE = "socketcan_available"
    VIRTUAL_ONLY = "virtual_only"
    THIRDPARTY_ONLY = "thirdparty_only"


def detect_platform() -> PlatformType:
    """Detect the current platform.

    Returns
    -------
    PlatformType
        Detected platform type
    """
    system = platform.system().lower()

    if system == "linux":
        return PlatformType.LINUX
    elif system == "darwin":
        return PlatformType.MACOS
    elif system == "windows":
        return PlatformType.WINDOWS
    else:
        return PlatformType.UNKNOWN


def get_can_capabilities(platform: PlatformType | None = None) -> dict[str, Any]:
    """Get CAN interface capabilities for the detected platform.

    Parameters
    ----------
    platform : PlatformType, optional
        Platform type to check. If None, auto-detects.

    Returns
    -------
    dict[str, Any]
        Dictionary containing platform capabilities and recommended interface
    """
    if platform is None:
        platform = detect_platform()

    capabilities = {
        "platform": platform.value,
        "capabilities": [],
        "recommended_interface": None,
        "available_interfaces": [],
        "notes": [],
    }

    if platform == PlatformType.LINUX:
        capabilities.update(
            {
                "capabilities": [
                    CANInterfaceCapability.SOCKETCAN_AVAILABLE,
                    CANInterfaceCapability.VIRTUAL_ONLY,
                    CANInterfaceCapability.THIRDPARTY_ONLY,
                ],
                "recommended_interface": "socketcan",
                "available_interfaces": ["socketcan", "virtual", "pcan", "kvaser", "ixxat"],
                "notes": [
                    "SocketCAN provides native kernel-level CAN support",
                    "Virtual CAN available for testing without hardware",
                    "Third-party USB adapters supported via python-can",
                ],
            }
        )

    elif platform == PlatformType.MACOS:
        capabilities.update(
            {
                "capabilities": [
                    CANInterfaceCapability.VIRTUAL_ONLY,
                    CANInterfaceCapability.THIRDPARTY_ONLY,
                ],
                "recommended_interface": "virtual",
                "available_interfaces": ["virtual", "pcan", "kvaser"],
                "notes": [
                    "SocketCAN not available on macOS",
                    "Virtual CAN provides full testing capabilities",
                    "Third-party USB adapters supported via python-can",
                ],
            }
        )

    elif platform == PlatformType.WINDOWS:
        capabilities.update(
            {
                "capabilities": [
                    CANInterfaceCapability.VIRTUAL_ONLY,
                    CANInterfaceCapability.THIRDPARTY_ONLY,
                ],
                "recommended_interface": "virtual",
                "available_interfaces": ["virtual", "pcan", "kvaser", "ixxat", "usb2can"],
                "notes": [
                    "SocketCAN not available on Windows",
                    "Virtual CAN provides full testing capabilities",
                    "Extensive third-party USB adapter support",
                ],
            }
        )

    else:  # UNKNOWN
        capabilities.update(
            {
                "capabilities": [CANInterfaceCapability.VIRTUAL_ONLY],
                "recommended_interface": "virtual",
                "available_interfaces": ["virtual"],
                "notes": [
                    "Unknown platform detected",
                    "Virtual CAN fallback ensures basic functionality",
                    "Consider checking python-can compatibility",
                ],
            }
        )

    logger.info(
        f"Platform detection complete: {platform.value} - {capabilities['recommended_interface']}"
    )
    return capabilities


def select_optimal_can_interface(
    preferred_interface: str | None = None, allow_fallback: bool = True
) -> dict[str, Any]:
    """Select the optimal CAN interface for the current platform.

    Parameters
    ----------
    preferred_interface : str, optional
        Preferred interface type. If None, uses platform recommendation.
    allow_fallback : bool, default True
        Whether to allow fallback to virtual CAN if preferred interface unavailable.

    Returns
    -------
    dict[str, Any]
        Selected interface configuration with fallback information
    """
    capabilities = get_can_capabilities()

    # Determine target interface
    target_interface = preferred_interface or capabilities["recommended_interface"]

    result = {
        "selected_interface": target_interface,
        "platform": capabilities["platform"],
        "fallback_used": False,
        "configuration": {},
        "notes": [],
    }

    # Check if preferred interface is available on this platform
    if target_interface not in capabilities["available_interfaces"]:
        if allow_fallback:
            result["selected_interface"] = "virtual"
            result["fallback_used"] = True
            result["notes"].append(
                f"Preferred interface '{target_interface}' not available on {capabilities['platform']}. "
                f"Falling back to virtual CAN."
            )
        else:
            raise ValueError(
                f"Interface '{target_interface}' not available on {capabilities['platform']}. "
                f"Available interfaces: {capabilities['available_interfaces']}"
            )

    # Set interface-specific configuration
    if result["selected_interface"] == "virtual":
        result["configuration"] = {
            "interface": "virtual",
            "channel": "vcan0",
            "bitrate": 500000,
            "notes": "Virtual CAN bus for cross-platform testing",
        }
        result["notes"].append("Using virtual CAN for cross-platform compatibility")

    elif result["selected_interface"] == "socketcan":
        result["configuration"] = {
            "interface": "socketcan",
            "channel": "can0",
            "bitrate": 500000,
            "notes": "Linux SocketCAN for production use",
        }
        result["notes"].append("Linux SocketCAN provides optimal performance")

    else:
        # Third-party interface
        result["configuration"] = {
            "interface": target_interface,
            "channel": "0",  # Default for many USB adapters
            "bitrate": 500000,
            "notes": f"Third-party {target_interface} interface",
        }
        result["notes"].append(f"Using {target_interface} third-party interface")

    logger.info(
        f"Selected CAN interface: {result['selected_interface']} on {capabilities['platform']}"
    )
    return result


def get_interface_recommendations() -> dict[str, str]:
    """Get interface recommendations for different use cases.

    Returns
    -------
    dict[str, str]
        Recommendations mapping use cases to interface types
    """
    return {
        "development": "virtual",
        "testing": "virtual",
        "production_linux": "socketcan",
        "production_other": "thirdparty_usb",
        "ci_cd": "virtual",
        "demonstration": "virtual",
    }
