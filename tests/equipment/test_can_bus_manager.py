"""
Test suite for production CAN bus connection manager.

Tests enterprise-level CAN bus management including connection pooling,
message routing, failover mechanisms, and comprehensive monitoring for
agricultural fleet operations.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import can
import pytest

from afs_fastapi.core.can_frame_codec import CANFrameCodec, DecodedPGN
from afs_fastapi.equipment.can_bus_manager import (
    CANBusConnectionManager,
    ConnectionPool,
    ConnectionPoolConfig,
    ManagerState,
    MessagePriority,
    MessageRouter,
    RoutingRule,
)
from afs_fastapi.equipment.can_error_handling import CANErrorHandler
from afs_fastapi.equipment.physical_can_interface import (
    BusSpeed,
    CANInterfaceType,
    InterfaceConfiguration,
    InterfaceState,
    PhysicalCANManager,
)


class TestMessageRouter:
    """Test message routing functionality."""

    @pytest.fixture
    def codec(self) -> CANFrameCodec:
        """Create CAN frame codec."""
        return CANFrameCodec()

    @pytest.fixture
    def router(self, codec: CANFrameCodec) -> MessageRouter:
        """Create message router."""
        return MessageRouter(codec)

    def test_router_initialization(self, router: MessageRouter) -> None:
        """Test message router initialization."""
        assert len(router.routing_rules) == 0
        assert len(router.message_stats) == 0
        assert len(router.route_cache) == 0

    def test_add_routing_rule(self, router: MessageRouter) -> None:
        """Test adding routing rules."""
        rule = RoutingRule(
            name="Test Rule",
            pgn_filters=[0xF004],
            source_filters=[0x00],
            destination_filters=[],
            priority=MessagePriority.HIGH,
            target_interfaces=["can0", "can1"],
        )

        router.add_routing_rule(rule)

        assert len(router.routing_rules) == 1
        assert router.routing_rules[0].name == "Test Rule"

    def test_remove_routing_rule(self, router: MessageRouter) -> None:
        """Test removing routing rules."""
        rule = RoutingRule(
            name="Test Rule",
            pgn_filters=[0xF004],
            source_filters=[],
            destination_filters=[],
            priority=MessagePriority.NORMAL,
            target_interfaces=["can0"],
        )

        router.add_routing_rule(rule)
        assert len(router.routing_rules) == 1

        success = router.remove_routing_rule("Test Rule")
        assert success is True
        assert len(router.routing_rules) == 0

        # Test removing non-existent rule
        success = router.remove_routing_rule("Non-existent")
        assert success is False

    def test_route_engine_message(self, router: MessageRouter) -> None:
        """Test routing engine telemetry message."""
        # Add rule for engine messages
        engine_rule = RoutingRule(
            name="Engine Telemetry",
            pgn_filters=[0xF004],  # EEC1
            source_filters=[0x00],  # Engine ECU
            destination_filters=[],
            priority=MessagePriority.HIGH,
            target_interfaces=["can0", "can1"],
        )
        router.add_routing_rule(engine_rule)

        # Create EEC1 message
        message = can.Message(
            arbitration_id=0x18F00400,  # EEC1 from engine ECU
            data=b"\x00\x64\xC8\x40\x38\x00\x00\x00",
            is_extended_id=True,
        )

        available_interfaces = ["can0", "can1", "can2"]
        target_interfaces, priority = router.route_message(message, available_interfaces)

        assert target_interfaces == ["can0", "can1"]
        assert priority == MessagePriority.HIGH

    def test_route_unknown_message(self, router: MessageRouter) -> None:
        """Test routing unknown message type."""
        # Unknown message should use all available interfaces
        message = can.Message(
            arbitration_id=0x18DEAD25,  # Unknown message
            data=b"\x01\x02\x03\x04",
            is_extended_id=True,
        )

        available_interfaces = ["can0", "can1"]
        target_interfaces, priority = router.route_message(message, available_interfaces)

        assert target_interfaces == available_interfaces
        assert priority == MessagePriority.LOW

    def test_route_caching(self, router: MessageRouter) -> None:
        """Test route caching functionality."""
        rule = RoutingRule(
            name="GPS Rule",
            pgn_filters=[0xFEF3],  # Vehicle Position
            source_filters=[],
            destination_filters=[],
            priority=MessagePriority.NORMAL,
            target_interfaces=["can0"],
        )
        router.add_routing_rule(rule)

        # Create GPS message
        message = can.Message(
            arbitration_id=0x18FEF325,  # VP from GPS receiver
            data=b"\x00\x00\x00\x00\x00\x00\x00\x00",
            is_extended_id=True,
        )

        available_interfaces = ["can0", "can1"]

        # First call should populate cache
        target_interfaces1, _ = router.route_message(message, available_interfaces)
        assert 0xFEF3 in router.route_cache

        # Second call should use cache
        target_interfaces2, _ = router.route_message(message, available_interfaces)
        assert target_interfaces1 == target_interfaces2

    def test_get_routing_statistics(self, router: MessageRouter) -> None:
        """Test routing statistics collection."""
        # Add some rules
        rule1 = RoutingRule(
            name="Rule 1",
            pgn_filters=[0xF004],
            source_filters=[],
            destination_filters=[],
            priority=MessagePriority.HIGH,
            target_interfaces=["can0"],
        )
        rule2 = RoutingRule(
            name="Rule 2",
            pgn_filters=[0xFEF1],
            source_filters=[],
            destination_filters=[],
            priority=MessagePriority.NORMAL,
            target_interfaces=["can1"],
            enabled=False,
        )

        router.add_routing_rule(rule1)
        router.add_routing_rule(rule2)

        stats = router.get_routing_statistics()

        assert stats["total_rules"] == 2
        assert stats["active_rules"] == 1  # rule2 is disabled
        assert "message_stats" in stats
        assert "cache_size" in stats


class TestConnectionPool:
    """Test connection pool management."""

    @pytest.fixture
    def pool_config(self) -> ConnectionPoolConfig:
        """Create connection pool configuration."""
        return ConnectionPoolConfig(
            primary_interfaces=["can0", "can1"],
            backup_interfaces=["can2"],
            health_check_interval=1.0,
            auto_recovery=True,
        )

    @pytest.fixture
    def physical_manager(self) -> PhysicalCANManager:
        """Create mock physical manager."""
        manager = MagicMock(spec=PhysicalCANManager)
        manager.connect_interface = AsyncMock()
        manager.disconnect_all = AsyncMock()
        manager.get_interface_status = MagicMock()
        return manager

    @pytest.fixture
    def error_handler(self) -> CANErrorHandler:
        """Create error handler."""
        return CANErrorHandler()

    @pytest.fixture
    def connection_pool(
        self,
        pool_config: ConnectionPoolConfig,
        physical_manager: PhysicalCANManager,
        error_handler: CANErrorHandler,
    ) -> ConnectionPool:
        """Create connection pool."""
        return ConnectionPool(pool_config, physical_manager, error_handler)

    @pytest.mark.asyncio
    async def test_pool_initialization_success(
        self,
        connection_pool: ConnectionPool,
        physical_manager: PhysicalCANManager,
    ) -> None:
        """Test successful connection pool initialization."""
        # Mock successful connections
        with patch.object(
            physical_manager, "connect_interface", new_callable=AsyncMock
        ) as mock_connect:
            mock_connect.return_value = True
            success = await connection_pool.initialize()

            assert success is True
            assert len(connection_pool.primary_connections) == 2
            assert len(connection_pool.backup_connections) == 1
            assert all(connection_pool.primary_connections.values())

    @pytest.mark.asyncio
    async def test_pool_initialization_failure(
        self,
        connection_pool: ConnectionPool,
        physical_manager: PhysicalCANManager,
    ) -> None:
        """Test connection pool initialization with failures."""
        # Mock connection failures
        with patch.object(
            physical_manager, "connect_interface", new_callable=AsyncMock
        ) as mock_connect:
            mock_connect.return_value = False
            success = await connection_pool.initialize()

            assert success is True  # Should still succeed even with connection failures
            assert not any(connection_pool.primary_connections.values())

    def test_get_active_interfaces(
        self,
        connection_pool: ConnectionPool,
    ) -> None:
        """Test getting active interfaces."""
        # Set up mock state
        connection_pool.primary_connections = {"can0": True, "can1": False}
        connection_pool.backup_connections = {"can2": True}
        connection_pool.connection_health = {"can0": 0.8, "can1": 0.2, "can2": 0.9}

        active = connection_pool.get_active_interfaces()

        # Only can0 should be active (connected and healthy)
        assert "can0" in active
        assert "can1" not in active
        assert len(active) == 1

    def test_get_best_interface(
        self,
        connection_pool: ConnectionPool,
    ) -> None:
        """Test getting best available interface."""
        # Set up mock state
        connection_pool.primary_connections = {"can0": True, "can1": True}
        connection_pool.backup_connections = {}
        connection_pool.connection_health = {"can0": 0.8, "can1": 0.9}

        best = connection_pool.get_best_interface()
        assert best == "can1"  # Higher health score

        # Test with exclusions
        best_excluded = connection_pool.get_best_interface(exclude=["can1"])
        assert best_excluded == "can0"

    def test_health_score_calculation(
        self,
        connection_pool: ConnectionPool,
    ) -> None:
        """Test health score calculation."""
        # Mock healthy status
        healthy_status = MagicMock()
        healthy_status.state = InterfaceState.CONNECTED
        healthy_status.errors_total = 5
        healthy_status.messages_sent = 1000
        healthy_status.messages_received = 1500
        healthy_status.bus_load_percentage = 45.0
        healthy_status.last_heartbeat = datetime.now()

        score = connection_pool._calculate_health_score(healthy_status)
        assert 0.8 <= score <= 1.0

        # Mock unhealthy status
        unhealthy_status = MagicMock()
        unhealthy_status.state = InterfaceState.ERROR
        unhealthy_status.errors_total = 200
        unhealthy_status.messages_sent = 100
        unhealthy_status.messages_received = 100
        unhealthy_status.bus_load_percentage = 95.0
        unhealthy_status.last_heartbeat = datetime.now() - timedelta(minutes=2)

        score = connection_pool._calculate_health_score(unhealthy_status)
        assert score < 0.5

    @pytest.mark.asyncio
    async def test_pool_shutdown(
        self,
        connection_pool: ConnectionPool,
        physical_manager: PhysicalCANManager,
    ) -> None:
        """Test connection pool shutdown."""
        # Initialize first
        with patch.object(
            physical_manager, "connect_interface", new_callable=AsyncMock
        ) as mock_connect:
            with patch.object(
                physical_manager, "disconnect_all", new_callable=AsyncMock
            ) as mock_disconnect:
                mock_connect.return_value = True
                await connection_pool.initialize()

                # Shutdown
                await connection_pool.shutdown()

                # Verify disconnect was called
                mock_disconnect.assert_called_once()


class TestCANBusConnectionManager:
    """Test complete CAN bus connection manager."""

    @pytest.fixture
    def pool_config(self) -> ConnectionPoolConfig:
        """Create pool configuration."""
        return ConnectionPoolConfig(
            primary_interfaces=["can0"],
            backup_interfaces=["can1"],
            health_check_interval=0.1,  # Fast for testing
            auto_recovery=True,
        )

    @pytest.fixture
    def can_manager(self, pool_config: ConnectionPoolConfig) -> CANBusConnectionManager:
        """Create CAN bus manager."""
        return CANBusConnectionManager(pool_config)

    @pytest.mark.asyncio
    async def test_manager_initialization(self, can_manager: CANBusConnectionManager) -> None:
        """Test manager initialization."""
        assert can_manager._state == ManagerState.INITIALIZING

        # Mock the connection pool initialization
        with patch.object(can_manager.connection_pool, "initialize", return_value=True):
            success = await can_manager.initialize()

        assert success is True
        assert can_manager._state == ManagerState.RUNNING

    @pytest.mark.asyncio
    async def test_manager_initialization_failure(
        self, can_manager: CANBusConnectionManager
    ) -> None:
        """Test manager initialization failure."""
        # Mock connection pool failure
        with patch.object(can_manager.connection_pool, "initialize", return_value=False):
            success = await can_manager.initialize()

        assert success is False
        assert can_manager._state == ManagerState.ERROR

    def test_message_callback_management(self, can_manager: CANBusConnectionManager) -> None:
        """Test message callback registration and removal."""
        callback_calls = []

        def test_callback(decoded: DecodedPGN, interface_id: str) -> None:
            callback_calls.append((decoded, interface_id))

        # Add callback
        can_manager.add_message_callback(test_callback)
        assert len(can_manager._message_callbacks) == 1

        # Remove callback
        can_manager.remove_message_callback(test_callback)
        assert len(can_manager._message_callbacks) == 0

    def test_incoming_message_handling(self, can_manager: CANBusConnectionManager) -> None:
        """Test handling of incoming CAN messages."""
        message = can.Message(
            arbitration_id=0x18F00400,
            data=b"\x00\x64\xC8\x40\x38\x00\x00\x00",
            is_extended_id=True,
        )

        # Should queue message
        initial_count = can_manager._statistics.total_messages_processed
        can_manager._handle_incoming_message(message, "can0")

        assert can_manager._statistics.total_messages_processed == initial_count + 1

    def test_incoming_message_queue_full(self, can_manager: CANBusConnectionManager) -> None:
        """Test handling when message queue is full."""
        # Fill the queue
        message = can.Message(arbitration_id=0x123, data=b"\x01\x02", is_extended_id=True)

        # Fill queue to capacity
        for _ in range(1000):  # Queue maxsize is 1000
            can_manager._handle_incoming_message(message, "can0")

        # This should trigger queue full handling
        initial_dropped = can_manager._statistics.messages_dropped
        can_manager._handle_incoming_message(message, "can0")

        assert can_manager._statistics.messages_dropped > initial_dropped

    @pytest.mark.asyncio
    async def test_send_message_auto_routing(self, can_manager: CANBusConnectionManager) -> None:
        """Test sending message with automatic routing."""
        message = can.Message(
            arbitration_id=0x18F00400,  # EEC1
            data=b"\x00\x64\xC8\x40\x38\x00\x00\x00",
            is_extended_id=True,
        )

        # Mock active interfaces and interface objects
        mock_interface = MagicMock()
        mock_interface.send_message = AsyncMock(return_value=True)

        with (
            patch.object(
                can_manager.connection_pool, "get_active_interfaces", return_value=["can0"]
            ),
            patch.object(can_manager.physical_manager, "_interfaces", {"can0": mock_interface}),
        ):

            results = await can_manager.send_message(message)

            # Type assertion for MyPy - new API returns dict
            assert isinstance(results, dict)
            assert "can0" in results
            assert results["can0"] is True
            mock_interface.send_message.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_message_specific_interfaces(
        self, can_manager: CANBusConnectionManager
    ) -> None:
        """Test sending message to specific interfaces."""
        message = can.Message(arbitration_id=0x123, data=b"\x01\x02", is_extended_id=True)

        # Mock interface
        mock_interface = MagicMock()
        mock_interface.send_message = AsyncMock(return_value=True)

        with patch.object(can_manager.physical_manager, "_interfaces", {"can0": mock_interface}):
            results = await can_manager.send_message(message, ["can0"])

            # Type assertion for MyPy - new API returns dict
            assert isinstance(results, dict)
            assert results["can0"] is True

    def test_manager_status(self, can_manager: CANBusConnectionManager) -> None:
        """Test getting manager status."""
        status = can_manager.get_manager_status()

        assert "state" in status
        assert "uptime" in status
        assert "statistics" in status
        assert "connection_pool" in status
        assert "routing" in status

        # Check statistics structure
        stats = status["statistics"]
        assert "total_messages" in stats
        assert "messages_routed" in stats
        assert "active_interfaces" in stats

    @pytest.mark.asyncio
    async def test_create_interface(self, can_manager: CANBusConnectionManager) -> None:
        """Test creating new CAN interface."""
        config = InterfaceConfiguration(
            interface_type=CANInterfaceType.SOCKETCAN,
            channel="vcan0",
            bitrate=BusSpeed.SPEED_250K,
        )

        # Mock successful creation
        mock_interface = MagicMock()
        with patch.object(
            can_manager.physical_manager, "create_interface", return_value=mock_interface
        ):
            success = await can_manager.create_interface("test_interface", config)

        assert success is True

    def test_state_transitions(self, can_manager: CANBusConnectionManager) -> None:
        """Test manager state transitions."""
        # Initially should be INITIALIZING
        assert can_manager._state == ManagerState.INITIALIZING

        # Mock different scenarios and check state updates
        can_manager.connection_pool.primary_connections = {}
        can_manager.connection_pool.backup_connections = {}
        can_manager.connection_pool.connection_health = {}
        can_manager._check_overall_health()
        assert can_manager._state == ManagerState.ERROR

        # Simulate failover scenario: primary down, backup available
        can_manager.connection_pool.primary_connections = {"can0": False}
        can_manager.connection_pool.backup_connections = {"can1": True}
        can_manager.connection_pool.connection_health = {"can0": 0.0, "can1": 0.8}
        can_manager.pool_config.auto_recovery = True
        can_manager._check_overall_health()
        assert can_manager._state == ManagerState.FAILOVER

    def test_default_routing_rules(self, can_manager: CANBusConnectionManager) -> None:
        """Test default routing rules setup."""
        can_manager._setup_default_routing_rules()

        # Should have at least 3 default rules
        assert len(can_manager.message_router.routing_rules) >= 3

        # Check for emergency rule
        emergency_rules = [
            r for r in can_manager.message_router.routing_rules if "Emergency" in r.name
        ]
        assert len(emergency_rules) >= 1

        # Check for engine rule
        engine_rules = [r for r in can_manager.message_router.routing_rules if "Engine" in r.name]
        assert len(engine_rules) >= 1

    @pytest.mark.asyncio
    async def test_manager_shutdown(self, can_manager: CANBusConnectionManager) -> None:
        """Test manager shutdown process."""
        # Initialize first
        with patch.object(can_manager.connection_pool, "initialize", return_value=True):
            await can_manager.initialize()

        assert can_manager._state == ManagerState.RUNNING

        # Mock connection pool shutdown
        with patch.object(can_manager.connection_pool, "shutdown") as mock_shutdown:
            await can_manager.shutdown()

        assert can_manager._state == ManagerState.STOPPED
        mock_shutdown.assert_called_once()


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    @pytest.mark.asyncio
    async def test_agricultural_fleet_communication_setup(self) -> None:
        """Test setting up complete agricultural fleet communication."""
        # Configuration for multi-tractor field operations
        pool_config = ConnectionPoolConfig(
            primary_interfaces=["field_network", "implement_network"],
            backup_interfaces=["diagnostic_network"],
            health_check_interval=1.0,
            auto_recovery=True,
            load_balancing=True,
        )

        manager = CANBusConnectionManager(pool_config)

        # Mock successful initialization
        with patch.object(manager.connection_pool, "initialize", return_value=True):
            success = await manager.initialize()

        assert success is True
        assert manager._state == ManagerState.RUNNING

        # Test routing for different message types
        engine_message = can.Message(
            arbitration_id=0x18F00400,  # EEC1 - Engine data
            data=b"\x00\x64\xC8\x40\x38\x00\x00\x00",
            is_extended_id=True,
        )

        emergency_message = can.Message(
            arbitration_id=0x18E00125,  # Emergency stop
            data=b"\xFF\xFF\xFF\xFF\x00\x00\x00\x00",
            is_extended_id=True,
        )

        # Mock interfaces for message sending
        mock_interface = MagicMock()
        mock_interface.send_message = AsyncMock(return_value=True)

        with (
            patch.object(
                manager.physical_manager,
                "_interfaces",
                {
                    "field_network": mock_interface,
                    "implement_network": mock_interface,
                },
            ),
            patch.object(
                manager.connection_pool,
                "get_active_interfaces",
                return_value=["field_network", "implement_network"],
            ),
        ):

            # Send engine message - should route to appropriate interfaces
            engine_results = await manager.send_message(engine_message)
            # Type assertion for MyPy - new API returns dict
            assert isinstance(engine_results, dict)
            assert len(engine_results) > 0

            # Send emergency message - should route to all interfaces
            emergency_results = await manager.send_message(emergency_message)
            # Type assertion for MyPy - new API returns dict
            assert isinstance(emergency_results, dict)
            assert len(emergency_results) > 0

        await manager.shutdown()

    @pytest.mark.asyncio
    async def test_failover_during_field_operations(self) -> None:
        """Test failover mechanisms during active field operations."""
        pool_config = ConnectionPoolConfig(
            primary_interfaces=["primary_can"],
            backup_interfaces=["backup_can"],
            health_check_interval=0.1,
            failover_timeout=1.0,
            auto_recovery=True,
        )

        manager = CANBusConnectionManager(pool_config)

        # Mock initialization
        with patch.object(manager.connection_pool, "initialize", return_value=True):
            await manager.initialize()

        # Simulate primary interface failure
        manager.connection_pool.primary_connections["primary_can"] = False
        manager.connection_pool.connection_health["primary_can"] = 0.0

        # Activate backup
        manager.connection_pool.backup_connections["backup_can"] = True
        manager.connection_pool.connection_health["backup_can"] = 1.0

        # Check state transition
        manager._check_overall_health()
        assert manager._state == ManagerState.FAILOVER

        # Verify backup interface is used
        active_interfaces = manager.get_active_interfaces()
        assert "backup_can" in active_interfaces
        assert "primary_can" not in active_interfaces

        await manager.shutdown()

    @pytest.mark.asyncio
    async def test_high_throughput_message_processing(self) -> None:
        """Test high-throughput message processing capabilities."""
        pool_config = ConnectionPoolConfig(
            primary_interfaces=["high_speed_can"],
            backup_interfaces=[],
            health_check_interval=1.0,
        )

        manager = CANBusConnectionManager(pool_config)

        # Mock initialization
        with patch.object(manager.connection_pool, "initialize", return_value=True):
            await manager.initialize()

        # Setup message callback to track processed messages
        processed_messages = []

        def message_callback(decoded: DecodedPGN, interface_id: str) -> None:
            processed_messages.append(decoded.pgn)

        manager.add_message_callback(message_callback)

        # Simulate high-frequency messages
        test_messages = [
            (0x18F00400, b"\x00\x64\xC8\x40\x38\x00\x00\x00"),  # EEC1 - 50ms
            (0x18FEF10B, b"\x80\x19\x00\x00\x00\x00\x00\x00"),  # WVS - 100ms
            (0x18FEF325, b"\x00\x00\x00\x00\x00\x00\x00\x00"),  # VP - 1000ms
        ]

        # Send rapid burst of messages
        for _ in range(100):  # Simulate 100 messages rapidly
            for arb_id, data in test_messages:
                message = can.Message(
                    arbitration_id=arb_id,
                    data=data,
                    is_extended_id=True,
                )
                manager._handle_incoming_message(message, "high_speed_can")

        # Allow some processing time
        await asyncio.sleep(0.1)

        # Verify message throughput statistics
        assert manager._statistics.total_messages_processed >= 300

        await manager.shutdown()

    def test_routing_rule_priority_handling(self) -> None:
        """Test routing rule priority and conflict resolution."""
        codec = CANFrameCodec()
        router = MessageRouter(codec)

        # Add conflicting rules with different priorities
        high_priority_rule = RoutingRule(
            name="High Priority Engine",
            pgn_filters=[0xF004],  # EEC1
            source_filters=[],
            destination_filters=[],
            priority=MessagePriority.CRITICAL,
            target_interfaces=["critical_can"],
        )

        normal_priority_rule = RoutingRule(
            name="Normal Engine",
            pgn_filters=[0xF004],  # Same PGN
            source_filters=[],
            destination_filters=[],
            priority=MessagePriority.NORMAL,
            target_interfaces=["normal_can"],
        )

        router.add_routing_rule(normal_priority_rule)
        router.add_routing_rule(high_priority_rule)

        # Create EEC1 message
        message = can.Message(
            arbitration_id=0x18F00400,
            data=b"\x00\x64\xC8\x40\x38\x00\x00\x00",
            is_extended_id=True,
        )

        available_interfaces = ["critical_can", "normal_can"]
        target_interfaces, priority = router.route_message(message, available_interfaces)

        # Should use highest priority rule
        assert priority == MessagePriority.CRITICAL
        assert "critical_can" in target_interfaces
