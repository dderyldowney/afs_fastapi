"""
Test suite for enhanced Linux SocketCAN integration.

Tests production-grade SocketCAN features for Linux agricultural systems,
including interface discovery, monitoring, and optimization capabilities.
"""

from __future__ import annotations

import asyncio
import subprocess
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import can
import pytest

from afs_fastapi.equipment.can_error_handling import CANErrorHandler
from afs_fastapi.equipment.physical_can_interface import (
    BusSpeed,
    CANInterfaceType,
    InterfaceConfiguration,
)
from afs_fastapi.equipment.socketcan_linux import LinuxSocketCANManager  # Reverted to original name
from afs_fastapi.equipment.socketcan_linux import (
    CANStatistics,
    EnhancedSocketCANInterface,
    LinuxCANInterfaceInfo,
    SocketCANState,
)


class TestLinuxSocketCANManager:  # Reverted to original name
    """Test Linux-specific SocketCAN management functionality."""

    @pytest.fixture
    def linux_manager(self) -> LinuxSocketCANManager:  # Reverted to original name
        """Create Linux SocketCAN manager for testing."""
        return LinuxSocketCANManager()  # Reverted to original name

    @pytest.mark.asyncio
    async def test_interface_discovery(
        self, linux_manager: LinuxSocketCANManager
    ) -> None:  # Reverted to original name
        """Test automatic CAN interface discovery on Linux systems."""
        # Mock ip link show output
        mock_output = """2: can0: <UP,LOWER_UP> mtu 16 qdisc pfifo_fast state UP qlen 10
    link/can
    can state ERROR-ACTIVE (berr-counter tx 0 rx 0) restart-ms 100
    bitrate 250000 sample-point 0.875
    tq 250 prop-seg 6 phase-seg1 7 phase-seg2 2 sjw 1
3: can1: <NO-CARRIER,NOARP,UP> mtu 16 qdisc pfifo_fast state DOWN qlen 10
    link/can
    can <NOARP,UP,ECHO>"""

        with patch.object(linux_manager, "_run_command", return_value=(mock_output, "")):
            interfaces = await linux_manager.discover_can_interfaces()

            assert len(interfaces) == 2

            # Check first interface (can0)
            can0 = interfaces[0]
            assert can0.name == "can0"
            assert can0.state == SocketCANState.UP
            assert can0.mtu == 16
            assert can0.tx_queue_len == 10
            assert can0.bitrate == 250000
            assert can0.sample_point == 0.875
            assert can0.restart_ms == 100

            # Check second interface (can1)
            can1 = interfaces[1]
            assert can1.name == "can1"
            assert can1.state == SocketCANState.DOWN
            assert can1.mtu == 16

    @pytest.mark.asyncio
    async def test_interface_discovery_failure(
        self, linux_manager: LinuxSocketCANManager
    ) -> None:  # Reverted to original name
        """Test handling of interface discovery failures."""
        with patch.object(
            linux_manager,
            "_run_command",
            side_effect=subprocess.CalledProcessError(1, ["ip"], "Command failed"),
        ):
            interfaces = await linux_manager.discover_can_interfaces()

            assert len(interfaces) == 0

    @pytest.mark.asyncio
    async def test_interface_configuration(
        self, linux_manager: LinuxSocketCANManager
    ) -> None:  # Reverted to original name
        """Test CAN interface configuration on Linux."""
        mock_run_command = AsyncMock(return_value=("", ""))

        with patch.object(linux_manager, "_run_command", mock_run_command):
            result = await linux_manager.configure_interface(
                interface_name="can0",
                bitrate=250000,
                sample_point=0.875,
                restart_ms=100,
            )

            assert result is True

            # Verify commands were called
            assert mock_run_command.call_count == 3

            # Check down command
            mock_run_command.assert_any_call(["ip", "link", "set", "can0", "down"])

            # Check configuration command
            mock_run_command.assert_any_call(
                [
                    "ip",
                    "link",
                    "set",
                    "can0",
                    "type",
                    "can",
                    "bitrate",
                    "250000",
                    "sample-point",
                    "0.875",
                    "restart-ms",
                    "100",
                ]
            )

            # Check up command
            mock_run_command.assert_any_call(["ip", "link", "set", "can0", "up"])

    @pytest.mark.asyncio
    async def test_interface_configuration_with_fd(
        self, linux_manager: LinuxSocketCANManager  # Reverted to original name
    ) -> None:
        """Test CAN FD interface configuration."""
        mock_run_command = AsyncMock(return_value=("", ""))

        with patch.object(linux_manager, "_run_command", mock_run_command):
            result = await linux_manager.configure_interface(
                interface_name="can0",
                bitrate=500000,
                fd_enabled=True,
            )

            assert result is True

            # Verify FD configuration was included
            mock_run_command.assert_any_call(
                [
                    "ip",
                    "link",
                    "set",
                    "can0",
                    "type",
                    "can",
                    "bitrate",
                    "500000",
                    "restart-ms",
                    "100",
                    "fd",
                    "on",
                ]
            )

    @pytest.mark.asyncio
    async def test_interface_configuration_failure(
        self, linux_manager: LinuxSocketCANManager  # Reverted to original name
    ) -> None:
        """Test handling of interface configuration failures."""
        with patch.object(
            linux_manager,
            "_run_command",
            side_effect=subprocess.CalledProcessError(1, ["ip"], "Permission denied"),
        ):
            result = await linux_manager.configure_interface("can0", 250000)

            assert result is False

    @pytest.mark.asyncio
    async def test_statistics_parsing_from_ip_command(
        self, linux_manager: LinuxSocketCANManager  # Reverted to original name
    ) -> None:
        """Test parsing statistics from ip command output."""
        mock_ip_output = """3: can0: <UP,LOWER_UP> mtu 16 qdisc pfifo_fast state UP qlen 10
    link/can
    RX: bytes  packets  errors  dropped overrun mcast
    15648    196      0       0       0       0
    TX: bytes  packets  errors  dropped carrier collsns
    12480    156      2       1       0       0"""

        with patch.object(linux_manager, "_run_command", return_value=(mock_ip_output, "")):
            stats = await linux_manager.get_interface_statistics("can0")

            assert stats is not None
            assert stats.interface_name == "can0"
            assert stats.rx_bytes == 15648
            assert stats.rx_packets == 196
            assert stats.rx_errors == 0
            assert stats.rx_dropped == 0
            assert stats.tx_bytes == 12480
            assert stats.tx_packets == 156
            assert stats.tx_errors == 2
            assert stats.tx_dropped == 1

    @pytest.mark.asyncio
    async def test_statistics_parsing_from_proc(
        self, linux_manager: LinuxSocketCANManager
    ) -> None:  # Reverted to original name
        """Test parsing statistics from /proc/net/can/stats."""
        mock_proc_content = """rx_packets: 1250
tx_packets: 980
rx_errors: 5
tx_errors: 2
rx_dropped: 0
tx_dropped: 1"""

        mock_path = MagicMock()
        mock_path.exists.return_value = True

        with (
            patch("pathlib.Path", return_value=mock_path),
            patch("builtins.open", mock_open(read_data=mock_proc_content)),
        ):

            stats = await linux_manager._parse_proc_stats("can0", mock_path)

            assert stats.interface_name == "can0"
            assert stats.rx_packets == 1250
            assert stats.tx_packets == 980
            assert stats.rx_errors == 5
            assert stats.tx_errors == 2

    def test_can_filter_creation(
        self, linux_manager: LinuxSocketCANManager
    ) -> None:  # Reverted to original name
        """Test creation of CAN message filters."""
        filter_specs = [
            (0x123, 0x7FF, False),  # Standard frame filter
            (0x18F00400, 0x1FFFF00, True),  # Extended frame filter
        ]

        filters = linux_manager.create_can_filters(filter_specs)

        assert len(filters) == 2

        # Check standard filter
        assert filters[0].can_id == 0x123
        assert filters[0].can_mask == 0x7FF
        assert filters[0].extended is False

        # Check extended filter
        assert filters[1].can_id == 0x18F00400
        assert filters[1].can_mask == 0x1FFFF00
        assert filters[1].extended is True

    def test_agricultural_filters_creation(
        self, linux_manager: LinuxSocketCANManager
    ) -> None:  # Reverted to original name
        """Test creation of standard agricultural CAN filters."""
        agricultural_filters = linux_manager.create_agricultural_filters()

        assert len(agricultural_filters) >= 8  # Should have standard agricultural filters

        # Check for Engine Controller filter (EEC1)
        eec1_filter = None
        for f in agricultural_filters:
            if f.can_id == 0x18F00400:
                eec1_filter = f
                break

        assert eec1_filter is not None
        assert eec1_filter.can_mask == 0x1FFFF00
        assert eec1_filter.extended is True

    @pytest.mark.asyncio
    async def test_monitoring_lifecycle(
        self, linux_manager: LinuxSocketCANManager
    ) -> None:  # Reverted to original name
        """Test starting and stopping interface monitoring."""
        mock_stats = CANStatistics(
            interface_name="can0",
            rx_packets=100,
            tx_packets=80,
        )

        with patch.object(linux_manager, "get_interface_statistics", return_value=mock_stats):
            # Start monitoring
            await linux_manager.start_monitoring("can0", update_interval=0.1)

            assert "can0" in linux_manager._monitoring_tasks

            # Let monitoring run briefly
            await asyncio.sleep(0.2)

            # Check that statistics were cached
            cached_stats = linux_manager.get_cached_statistics("can0")
            assert cached_stats is not None
            assert cached_stats.rx_packets == 100

            # Stop monitoring
            await linux_manager.stop_monitoring("can0")

            assert "can0" not in linux_manager._monitoring_tasks

    @pytest.mark.asyncio
    async def test_queue_optimization(
        self, linux_manager: LinuxSocketCANManager
    ) -> None:  # Reverted to original name
        """Test interface queue optimization."""
        mock_run_command = AsyncMock(return_value=("", ""))

        with patch.object(linux_manager, "_run_command", mock_run_command):
            high_priority_ids = [0x18E001, 0x18E002, 0x18E003]

            result = await linux_manager.optimize_interface_queue(
                "can0",
                high_priority_ids,
                queue_size=150,
            )

            assert result is True

            # Verify queue configuration command
            mock_run_command.assert_called_once_with(
                ["ip", "link", "set", "can0", "txqueuelen", "150"]
            )

    @pytest.mark.asyncio
    async def test_bus_health_check_healthy(
        self, linux_manager: LinuxSocketCANManager
    ) -> None:  # Reverted to original name
        """Test bus health check for healthy interface."""
        # Mock healthy interface info
        mock_interface = LinuxCANInterfaceInfo(
            name="can0",
            state=SocketCANState.UP,
            mtu=16,
            tx_queue_len=10,
            bitrate=250000,
            sample_point=0.875,
            tq=250,
            prop_seg=6,
            phase_seg1=7,
            phase_seg2=2,
            sjw=1,
            restart_ms=100,
            bus_error_count=5,
            tx_errors=2,
            rx_errors=1,
        )

        mock_stats = CANStatistics(
            interface_name="can0",
            rx_packets=1000,
            tx_packets=800,
            rx_errors=5,
            tx_errors=3,
            bus_load_percentage=45.0,
        )

        with (
            patch.object(linux_manager, "discover_can_interfaces", return_value=[mock_interface]),
            patch.object(linux_manager, "get_interface_statistics", return_value=mock_stats),
        ):

            health_report = await linux_manager.perform_bus_health_check("can0")

            assert health_report["interface"] == "can0"
            assert health_report["overall_health"] == "healthy"
            assert len(health_report["issues"]) == 0

    @pytest.mark.asyncio
    async def test_bus_health_check_critical(
        self, linux_manager: LinuxSocketCANManager
    ) -> None:  # Reverted to original name
        """Test bus health check for critical interface conditions."""
        # Mock unhealthy interface info
        mock_interface = LinuxCANInterfaceInfo(
            name="can0",
            state=SocketCANState.ERROR_PASSIVE,
            mtu=16,
            tx_queue_len=10,
            bitrate=250000,
            sample_point=0.875,
            tq=250,
            prop_seg=6,
            phase_seg1=7,
            phase_seg2=2,
            sjw=1,
            restart_ms=100,
            bus_error_count=75,  # High error count
            tx_errors=25,  # High TX errors
            rx_errors=30,  # High RX errors
        )

        mock_stats = CANStatistics(
            interface_name="can0",
            rx_packets=100,
            tx_packets=80,
            rx_errors=15,  # High error rate (15/180 = 8.3%)
            tx_errors=10,
            bus_load_percentage=85.0,  # High bus load
        )

        with (
            patch.object(linux_manager, "discover_can_interfaces", return_value=[mock_interface]),
            patch.object(linux_manager, "get_interface_statistics", return_value=mock_stats),
        ):

            health_report = await linux_manager.perform_bus_health_check("can0")

            assert health_report["interface"] == "can0"
            assert health_report["overall_health"] == "critical"
            assert len(health_report["issues"]) >= 5  # Should detect multiple issues

            # Check for specific issues
            issues_text = " ".join(health_report["issues"])
            assert "ERROR-PASSIVE" in issues_text
            assert "High bus error count" in issues_text
            assert "High TX errors" in issues_text
            assert "High RX errors" in issues_text
            assert "High error rate" in issues_text
            assert "High bus load" in issues_text


def _await_async_mocks(interface: EnhancedSocketCANInterface) -> None:
    """Helper function to properly await async mock coroutines."""
    for mock_attr in ["_message_reception_loop", "_heartbeat_loop"]:
        mock_obj = getattr(interface, mock_attr, None)
        if (
            mock_obj
            and hasattr(mock_obj, "return_value")
            and asyncio.iscoroutine(mock_obj.return_value)
        ):
            try:
                asyncio.run(mock_obj.return_value)
            except Exception:
                pass  # Ignore errors during cleanup


class TestEnhancedSocketCANInterface:
    """Test enhanced SocketCAN interface with Linux optimizations."""

    @pytest.fixture
    def error_handler(self) -> CANErrorHandler:
        """Create error handler for testing."""
        return CANErrorHandler()

    @pytest.fixture
    def linux_manager(
        self, error_handler: CANErrorHandler
    ) -> LinuxSocketCANManager:  # Reverted to original name
        """Create Linux manager for testing."""
        return LinuxSocketCANManager(error_handler)  # Reverted to original name

    @pytest.fixture
    def enhanced_config(self) -> InterfaceConfiguration:
        """Create enhanced interface configuration."""
        return InterfaceConfiguration(
            interface_type=CANInterfaceType.SOCKETCAN,
            channel="can0",
            bitrate=BusSpeed.SPEED_250K,
            fd_enabled=False,
        )

    @pytest.fixture
    def enhanced_interface(
        self,
        enhanced_config: InterfaceConfiguration,
        error_handler: CANErrorHandler,
        linux_manager: LinuxSocketCANManager,  # Reverted to original name
    ) -> EnhancedSocketCANInterface:
        """Create enhanced SocketCAN interface for testing."""
        return EnhancedSocketCANInterface(
            interface_id="enhanced_can0",
            config=enhanced_config,
            error_handler=error_handler,
            linux_manager=linux_manager,
        )

    @pytest.mark.asyncio
    async def test_enhanced_connection_with_optimization(
        self,
        enhanced_interface: EnhancedSocketCANInterface,
    ) -> None:
        """Test enhanced connection process with Linux optimizations."""
        mock_configure = AsyncMock(return_value=True)
        mock_start_monitoring = AsyncMock()
        mock_bus_instance = AsyncMock(spec=can.BusABC)  # Mock the BusABC interface
        mock_create_task = MagicMock(spec=asyncio.create_task)  # Mock asyncio.create_task

        with (
            patch.object(enhanced_interface.linux_manager, "configure_interface", mock_configure),
            patch.object(
                enhanced_interface.linux_manager, "start_monitoring", mock_start_monitoring
            ),
            patch(
                "can.interface.Bus", return_value=mock_bus_instance
            ),  # Mock the class to return our mock instance
            patch("asyncio.create_task", mock_create_task),  # Mock create_task
        ):
            # Test connection
            result = await enhanced_interface.connect()

            assert result is True

            # Verify Linux-specific configuration was called
            mock_configure.assert_called_once_with(
                "can0",
                250000,
                fd_enabled=False,
            )

            # Verify monitoring was started
            mock_start_monitoring.assert_called_once_with("can0")

            # Verify that the bus was created and shutdown was not called prematurely
            mock_bus_instance.shutdown.assert_not_called()

            # Verify that heartbeat and message reception tasks were attempted to be created
            # The exact number of calls depends on how many tasks are created in connect()
            assert mock_create_task.call_count >= 2

    @pytest.mark.asyncio
    async def test_enhanced_disconnection_cleanup(
        self,
        enhanced_interface: EnhancedSocketCANInterface,
    ) -> None:
        """Test enhanced disconnection with proper cleanup."""
        mock_stop_monitoring = AsyncMock()
        mock_bus_instance = AsyncMock(spec=can.BusABC)
        mock_bus_instance.shutdown = MagicMock()

        with (
            patch.object(enhanced_interface.linux_manager, "stop_monitoring", mock_stop_monitoring),
            patch.object(
                enhanced_interface, "connect", AsyncMock(return_value=True)
            ),  # Mock connect to set up _bus
            patch.object(
                enhanced_interface, "_bus", new=mock_bus_instance
            ),  # Ensure _bus is our mock
            patch(
                "asyncio.create_task"
            ),  # Mock create_task to prevent actual task creation during connect
        ):

            # First connect (with mocked bus and tasks)
            await enhanced_interface.connect()

            # Properly await async mocks before cleanup
            _await_async_mocks(enhanced_interface)

            # Then disconnect
            result = await enhanced_interface.disconnect()

            assert result is True

            # Verify monitoring was stopped
            mock_stop_monitoring.assert_called_once_with("can0")
            # Verify bus shutdown was called
            mock_bus_instance.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_agricultural_optimization(
        self,
        enhanced_interface: EnhancedSocketCANInterface,
    ) -> None:
        """Test agricultural-specific optimizations."""
        mock_optimize_queue = AsyncMock(return_value=True)

        with patch.object(
            enhanced_interface.linux_manager, "optimize_interface_queue", mock_optimize_queue
        ):
            result = await enhanced_interface.optimize_for_agriculture()

            assert result is True
            assert enhanced_interface._performance_optimized is True

            # Verify queue optimization was called with agricultural priorities
            mock_optimize_queue.assert_called_once()
            call_args = mock_optimize_queue.call_args
            assert call_args[0][0] == "can0"  # interface name
            assert len(call_args[0][1]) >= 5  # high priority IDs
            assert call_args[1]["queue_size"] == 200  # agricultural queue size

    @pytest.mark.asyncio
    async def test_health_status_reporting(
        self,
        enhanced_interface: EnhancedSocketCANInterface,
    ) -> None:
        """Test comprehensive health status reporting."""
        mock_health_report = {
            "interface": "can0",
            "overall_health": "healthy",
            "issues": [],
            "recommendations": [],
        }

        with patch.object(
            enhanced_interface.linux_manager,
            "perform_bus_health_check",
            return_value=mock_health_report,
        ):
            health_status = await enhanced_interface.get_health_status()

            assert health_status["interface"] == "can0"
            assert health_status["overall_health"] == "healthy"

    def test_performance_metrics_retrieval(
        self,
        enhanced_interface: EnhancedSocketCANInterface,
    ) -> None:
        """Test performance metrics retrieval."""
        mock_stats = CANStatistics(
            interface_name="can0",
            rx_packets=500,
            tx_packets=400,
            bus_load_percentage=35.0,
        )

        with patch.object(
            enhanced_interface.linux_manager, "get_cached_statistics", return_value=mock_stats
        ):
            metrics = enhanced_interface.get_performance_metrics()

            assert metrics is not None
            assert metrics.interface_name == "can0"
            assert metrics.rx_packets == 500
            assert metrics.bus_load_percentage == 35.0


class TestIntegrationScenarios:
    """Test real-world integration scenarios for Linux SocketCAN."""

    @pytest.mark.asyncio
    async def test_agricultural_field_network_setup(self) -> None:
        """Test setting up a complete agricultural field CAN network."""
        linux_manager = LinuxSocketCANManager()  # Reverted to original name

        # Mock multiple CAN interfaces discovery
        mock_interfaces = [
            LinuxCANInterfaceInfo(
                name="can0",
                state=SocketCANState.UP,
                mtu=16,
                tx_queue_len=10,
                bitrate=250000,
                sample_point=0.875,
                tq=250,
                prop_seg=6,
                phase_seg1=7,
                phase_seg2=2,
                sjw=1,
                restart_ms=100,
            ),
            LinuxCANInterfaceInfo(
                name="can1",
                state=SocketCANState.DOWN,
                mtu=16,
                tx_queue_len=10,
                bitrate=0,
                sample_point=0.0,
                tq=0,
                prop_seg=0,
                phase_seg1=0,
                phase_seg2=2,
                sjw=0,
                restart_ms=0,
            ),
        ]

        async def mock_start_monitoring(interface_name: str, update_interval: float = 1.0) -> None:
            linux_manager._monitoring_tasks[interface_name] = AsyncMock()

        with (
            patch.object(linux_manager, "discover_can_interfaces", return_value=mock_interfaces),
            patch.object(linux_manager, "configure_interface", return_value=True),
            patch.object(linux_manager, "start_monitoring", side_effect=mock_start_monitoring),
        ):

            # Discover available interfaces
            interfaces = await linux_manager.discover_can_interfaces()
            assert len(interfaces) == 2

            # Configure the down interface for agricultural use
            config_result = await linux_manager.configure_interface(
                "can1",
                bitrate=250000,  # ISOBUS standard
                sample_point=0.875,
                restart_ms=100,
            )
            assert config_result is True

            # Create agricultural filters for efficient message processing
            agricultural_filters = linux_manager.create_agricultural_filters()
            assert len(agricultural_filters) >= 8

            # Start monitoring both interfaces
            await linux_manager.start_monitoring("can0")
            await linux_manager.start_monitoring("can1")

            # Verify network readiness
            assert "can0" in linux_manager._monitoring_tasks
            assert "can1" in linux_manager._monitoring_tasks

    @pytest.mark.asyncio
    async def test_production_monitoring_and_alerting(self) -> None:
        """Test production monitoring with health checks and alerting."""
        linux_manager = LinuxSocketCANManager()  # Reverted to original name

        # Mock interface with escalating health issues
        critical_interface = LinuxCANInterfaceInfo(
            name="can0",
            state=SocketCANState.ERROR_WARNING,
            mtu=16,
            tx_queue_len=10,
            bitrate=250000,
            sample_point=0.875,
            tq=250,
            prop_seg=6,
            phase_seg1=7,
            phase_seg2=2,
            sjw=1,
            restart_ms=100,
            bus_error_count=60,  # Approaching critical threshold
            tx_errors=18,
            rx_errors=22,
        )

        critical_stats = CANStatistics(
            interface_name="can0",
            rx_packets=200,
            tx_packets=150,
            rx_errors=20,  # High error rate: 20/350 = 5.7%
            tx_errors=15,
            bus_load_percentage=82.0,  # High bus load
        )

        with (
            patch.object(
                linux_manager, "discover_can_interfaces", return_value=[critical_interface]
            ),
            patch.object(linux_manager, "get_interface_statistics", return_value=critical_stats),
        ):

            # Perform health check
            health_report = await linux_manager.perform_bus_health_check("can0")

            # Verify critical issues are detected
            assert health_report["overall_health"] in ["warning", "critical"]
            assert len(health_report["issues"]) >= 3

            # Check for specific critical conditions
            issues_text = " ".join(health_report["issues"])
            assert "error" in issues_text.lower()
            assert "load" in issues_text.lower()

            # Verify recommendations are provided
            if health_report["recommendations"]:
                recommendations_text = " ".join(health_report["recommendations"])
                assert (
                    "load balancing" in recommendations_text.lower()
                    or "filtering" in recommendations_text.lower()
                )

    @pytest.mark.asyncio
    async def test_high_throughput_filtering_optimization(self) -> None:
        """Test filtering optimization for high-throughput agricultural operations."""
        linux_manager = LinuxSocketCANManager()  # Reverted to original name

        # Create comprehensive filter set for precision agriculture
        precision_ag_filters = [
            # Core tractor telemetry
            (0x18F00400, 0x1FFFF00, True),  # EEC1 - Engine data
            (0x18FEF100, 0x1FFFF00, True),  # WVS - Vehicle speed
            (0x18FEF300, 0x1FFFF00, True),  # VP - GPS position
            # Implement control
            (0x18EA0000, 0x1FF00000, True),  # Tractor-Implement Management
            (0x18E80000, 0x1FF00000, True),  # Working Set Master
            # Safety systems
            (0x18E00100, 0x1FFFF00, True),  # Emergency stop
            (0x18E00200, 0x1FFFF00, True),  # Safety alerts
            (0x18E00300, 0x1FFFF00, True),  # Collision warnings
            # Field operations
            (0x18FE4700, 0x1FFFF00, True),  # Maintain Power
            (0x18FEF200, 0x1FFFF00, True),  # Fuel Economy
        ]

        filters = linux_manager.create_can_filters(precision_ag_filters)

        # Verify comprehensive filter coverage
        assert len(filters) == 10

        # Check safety-critical filters have correct priority
        emergency_filters = [f for f in filters if f.can_id == 0x18E00100]
        assert len(emergency_filters) == 1
        assert emergency_filters[0].extended is True

        # Verify agricultural standard filters
        agricultural_filters = linux_manager.create_agricultural_filters()
        assert len(agricultural_filters) >= len(filters)  # Should include all plus more

        # Test filter application would be efficient
        eec1_filters = [f for f in agricultural_filters if f.can_id == 0x18F00400]
        assert len(eec1_filters) == 1
        assert eec1_filters[0].can_mask == 0x1FFFF00  # Efficient mask for source address filtering
