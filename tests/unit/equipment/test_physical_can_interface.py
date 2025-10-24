"""
Test suite for physical CAN interface integration layer.

Tests comprehensive CAN interface abstraction for real-world tractor connectivity
with fully async-aware mocking to prevent test hanging and ensure isolation.

Implementation follows Test-First Development (TDD) methodology.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import can
import pytest

from afs_fastapi.equipment.can_error_handling import CANErrorHandler
from afs_fastapi.equipment.physical_can_interface import (
    BusSpeed,
    CANInterfaceType,
    InterfaceConfiguration,
    InterfaceState,
    InterfaceStatus,
    J1939Address,
    PhysicalCANManager,
    SocketCANInterface,
    VirtualCANInterface,
)


class TestInterfaceConfiguration:
    """Test interface configuration data structure."""

    def test_configuration_initialization(self) -> None:
        """Test interface configuration initialization."""
        config = InterfaceConfiguration(
            interface_type=CANInterfaceType.SOCKETCAN,
            channel="can0",
            bitrate=BusSpeed.SPEED_250K,
        )

        assert config.interface_type == CANInterfaceType.SOCKETCAN
        assert config.channel == "can0"
        assert config.bitrate == BusSpeed.SPEED_250K
        assert config.fd_enabled is False
        assert config.extended_frames is True

    def test_configuration_with_can_fd(self) -> None:
        """Test configuration with CAN FD enabled."""
        config = InterfaceConfiguration(
            interface_type=CANInterfaceType.SOCKETCAN,
            channel="can0",
            bitrate=BusSpeed.SPEED_500K,
            fd_enabled=True,
            data_bitrate=2000000,
        )

        assert config.fd_enabled is True
        assert config.data_bitrate == 2000000


class TestInterfaceStatus:
    """Test interface status tracking."""

    def test_status_initialization(self) -> None:
        """Test interface status initialization."""
        status = InterfaceStatus(
            interface_id="test_can",
            state=InterfaceState.DISCONNECTED,
            last_heartbeat=datetime.now(),
        )

        assert status.interface_id == "test_can"
        assert status.state == InterfaceState.DISCONNECTED
        assert status.messages_sent == 0
        assert status.messages_received == 0
        assert status.errors_total == 0


class TestJ1939Address:
    """Test J1939/ISOBUS address structure."""

    def test_j1939_address_creation(self) -> None:
        """Test J1939 address structure."""
        address = J1939Address(
            source_address=0x42,
            parameter_group_number=0xF004,
            priority=6,
        )

        assert address.source_address == 0x42
        assert address.parameter_group_number == 0xF004
        assert address.priority == 6
        assert address.destination_address == 0xFF  # Broadcast default

    def test_j1939_address_with_destination(self) -> None:
        """Test J1939 address with specific destination."""
        address = J1939Address(
            source_address=0x42,
            parameter_group_number=0xF004,
            destination_address=0x21,
            priority=3,
        )

        assert address.destination_address == 0x21
        assert address.priority == 3


class TestPhysicalCANManager:
    """Test physical CAN manager with complete async isolation."""

    @pytest.fixture
    def mock_error_handler(self) -> MagicMock:
        """Create mocked error handler."""
        return MagicMock(spec=CANErrorHandler)

    @pytest.fixture
    def can_manager(self, mock_error_handler: MagicMock) -> PhysicalCANManager:
        """Create CAN manager with mocked dependencies."""
        return PhysicalCANManager(error_handler=mock_error_handler)

    @pytest.fixture
    def test_config(self) -> InterfaceConfiguration:
        """Create test configuration."""
        return InterfaceConfiguration(
            interface_type=CANInterfaceType.SOCKETCAN,
            channel="vcan0",
            bitrate=BusSpeed.SPEED_250K,
        )

    @pytest.mark.asyncio
    async def test_interface_creation(
        self,
        can_manager: PhysicalCANManager,
        test_config: InterfaceConfiguration,
    ) -> None:
        """Test interface creation and registration."""
        interface = await can_manager.create_interface("test_if1", test_config)

        assert interface.interface_id == "test_if1"
        assert "test_if1" in can_manager._interfaces
        assert can_manager.get_interface_status("test_if1") is not None

    @pytest.mark.asyncio
    async def test_virtual_interface_creation(
        self,
        can_manager: PhysicalCANManager,
        mock_error_handler: MagicMock,
    ) -> None:
        """Test virtual interface creation and registration."""
        virtual_config = InterfaceConfiguration(
            interface_type=CANInterfaceType.VIRTUAL,
            channel="virtual_can",
            bitrate=BusSpeed.SPEED_250K,
        )
        interface = await can_manager.create_interface("test_virtual_if", virtual_config)

        assert interface.interface_id == "test_virtual_if"
        assert "test_virtual_if" in can_manager._interfaces
        assert isinstance(interface, VirtualCANInterface)
        assert can_manager.get_interface_status("test_virtual_if") is not None

    @pytest.mark.asyncio
    async def test_duplicate_interface_creation_error(
        self,
        can_manager: PhysicalCANManager,
        test_config: InterfaceConfiguration,
    ) -> None:
        """Test error handling for duplicate interface creation."""
        await can_manager.create_interface("test_if1", test_config)

        with pytest.raises(ValueError, match="Interface test_if1 already exists"):
            await can_manager.create_interface("test_if1", test_config)

    @pytest.mark.asyncio
    async def test_unsupported_interface_type(
        self,
        can_manager: PhysicalCANManager,
    ) -> None:
        """Test error handling for unsupported interface types."""
        unsupported_config = InterfaceConfiguration(
            interface_type=CANInterfaceType.PCAN,
            channel="PCAN_USBBUS1",
            bitrate=BusSpeed.SPEED_250K,
        )

        with pytest.raises(
            NotImplementedError, match="Interface type CANInterfaceType.PCAN not implemented yet"
        ):
            await can_manager.create_interface("pcan_test", unsupported_config)

    @pytest.mark.asyncio
    async def test_interface_connection_management(
        self,
        can_manager: PhysicalCANManager,
        test_config: InterfaceConfiguration,
    ) -> None:
        """Test individual interface connection management."""
        await can_manager.create_interface("test_if1", test_config)

        with patch.object(SocketCANInterface, "connect", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = True

            # Test successful connection
            result = await can_manager.connect_interface("test_if1")
            assert result is True
            assert "test_if1" in can_manager._active_interfaces

            mock_connect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_interface_connection_failure(
        self,
        can_manager: PhysicalCANManager,
        test_config: InterfaceConfiguration,
    ) -> None:
        """Test interface connection failure handling."""
        await can_manager.create_interface("test_if1", test_config)

        with patch.object(SocketCANInterface, "connect", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = False

            result = await can_manager.connect_interface("test_if1")
            assert result is False
            assert "test_if1" not in can_manager._active_interfaces

    @pytest.mark.asyncio
    async def test_nonexistent_interface_connection(
        self,
        can_manager: PhysicalCANManager,
    ) -> None:
        """Test connection attempt on non-existent interface."""
        result = await can_manager.connect_interface("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_interface_disconnection_management(
        self,
        can_manager: PhysicalCANManager,
        test_config: InterfaceConfiguration,
    ) -> None:
        """Test individual interface disconnection management."""
        await can_manager.create_interface("test_if1", test_config)

        with (
            patch.object(SocketCANInterface, "connect", new_callable=AsyncMock, return_value=True),
            patch.object(
                SocketCANInterface, "disconnect", new_callable=AsyncMock
            ) as mock_disconnect,
        ):
            mock_disconnect.return_value = True

            # Connect first
            await can_manager.connect_interface("test_if1")
            assert "test_if1" in can_manager._active_interfaces

            # Test disconnection
            result = await can_manager.disconnect_interface("test_if1")
            assert result is True
            assert "test_if1" not in can_manager._active_interfaces

            mock_disconnect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_connect_all_interfaces(
        self,
        can_manager: PhysicalCANManager,
        test_config: InterfaceConfiguration,
    ) -> None:
        """Test connecting all configured interfaces."""
        await can_manager.create_interface("if1", test_config)
        await can_manager.create_interface("if2", test_config)

        with patch.object(SocketCANInterface, "connect", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = True

            results = await can_manager.connect_all()

            assert results == {"if1": True, "if2": True}
            assert mock_connect.call_count == 2
            assert len(can_manager._active_interfaces) == 2

    @pytest.mark.asyncio
    async def test_disconnect_all_interfaces(
        self,
        can_manager: PhysicalCANManager,
        test_config: InterfaceConfiguration,
    ) -> None:
        """Test disconnecting all active interfaces."""
        await can_manager.create_interface("if1", test_config)
        await can_manager.create_interface("if2", test_config)

        with (
            patch.object(SocketCANInterface, "connect", new_callable=AsyncMock, return_value=True),
            patch.object(
                SocketCANInterface, "disconnect", new_callable=AsyncMock
            ) as mock_disconnect,
        ):
            mock_disconnect.return_value = True

            # Connect all first
            await can_manager.connect_all()
            assert len(can_manager._active_interfaces) == 2

            # Disconnect all
            results = await can_manager.disconnect_all()

            assert results == {"if1": True, "if2": True}
            assert mock_disconnect.call_count == 2
            assert len(can_manager._active_interfaces) == 0

    @pytest.mark.asyncio
    async def test_message_broadcasting(
        self,
        can_manager: PhysicalCANManager,
        test_config: InterfaceConfiguration,
    ) -> None:
        """Test message broadcasting to all active interfaces."""
        await can_manager.create_interface("if1", test_config)
        await can_manager.create_interface("if2", test_config)

        test_message = can.Message(arbitration_id=0x123, data=b"\x01\x02\x03")

        with (
            patch.object(SocketCANInterface, "connect", new_callable=AsyncMock, return_value=True),
            patch.object(SocketCANInterface, "send_message", new_callable=AsyncMock) as mock_send,
        ):
            mock_send.return_value = True

            # Connect interfaces
            await can_manager.connect_all()

            # Broadcast message
            results = await can_manager.broadcast_message(test_message)

            assert results == {"if1": True, "if2": True}
            assert mock_send.call_count == 2

            # Verify each interface got the message
            for call in mock_send.call_args_list:
                assert call[0][0] == test_message

    @pytest.mark.asyncio
    async def test_broadcasting_to_no_active_interfaces(
        self,
        can_manager: PhysicalCANManager,
    ) -> None:
        """Test broadcasting when no interfaces are active."""
        test_message = can.Message(arbitration_id=0x123)
        results = await can_manager.broadcast_message(test_message)

        assert results == {}

    def test_global_callback_management(
        self,
        can_manager: PhysicalCANManager,
        test_config: InterfaceConfiguration,
    ) -> None:
        """Test global message callback management."""
        callback_calls = []

        def global_callback(message: can.Message, interface_id: str) -> None:
            callback_calls.append((message, interface_id))

        # Add global callback
        can_manager.add_global_callback(global_callback)

        # Create interface - should automatically get the global callback
        with patch.object(SocketCANInterface, "__init__", return_value=None):
            mock_interface = MagicMock()
            mock_interface.add_message_callback = MagicMock()

            with patch.object(can_manager, "_interfaces", {"test_if": mock_interface}):
                can_manager.add_global_callback(global_callback)

                # Verify callback was added to existing interfaces
                mock_interface.add_message_callback.assert_called_with(global_callback)

    def test_interface_status_retrieval(
        self,
        can_manager: PhysicalCANManager,
        test_config: InterfaceConfiguration,
    ) -> None:
        """Test interface status retrieval."""
        # Test non-existent interface
        status = can_manager.get_interface_status("nonexistent")
        assert status is None

        # Test existing interface
        with patch.object(SocketCANInterface, "__init__", return_value=None):
            mock_interface = MagicMock()
            mock_status = InterfaceStatus(
                interface_id="test_if",
                state=InterfaceState.CONNECTED,
                last_heartbeat=datetime.now(),
            )
            mock_interface.status = mock_status

            can_manager._interfaces["test_if"] = mock_interface

            status = can_manager.get_interface_status("test_if")
            assert status == mock_status

    def test_all_interface_status_retrieval(
        self,
        can_manager: PhysicalCANManager,
    ) -> None:
        """Test retrieving status of all interfaces."""
        # Create mock interfaces
        mock_if1 = MagicMock()
        mock_if2 = MagicMock()

        status1 = InterfaceStatus(
            interface_id="if1", state=InterfaceState.CONNECTED, last_heartbeat=datetime.now()
        )
        status2 = InterfaceStatus(
            interface_id="if2", state=InterfaceState.DISCONNECTED, last_heartbeat=datetime.now()
        )

        mock_if1.status = status1
        mock_if2.status = status2

        can_manager._interfaces = {"if1": mock_if1, "if2": mock_if2}

        all_status = can_manager.get_all_interface_status()

        assert len(all_status) == 2
        assert all_status["if1"] == status1
        assert all_status["if2"] == status2

    def test_j1939_message_creation(
        self,
        can_manager: PhysicalCANManager,
    ) -> None:
        """Test J1939 CAN message creation."""
        address = J1939Address(
            priority=6,
            parameter_group_number=0xF004,
            source_address=0x42,
            data_page=False,
            pdu_format=0xF0,
            pdu_specific=0x04,
        )

        test_data = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        message = can_manager.create_j1939_message(address, test_data)

        assert message.arbitration_id & 0x1C000000 == (6 << 26)  # Priority
        assert message.arbitration_id & 0xFF == 0x42  # Source address
        assert message.data == test_data
        assert message.is_extended_id is True

    def test_j1939_message_creation_with_timestamp(
        self,
        can_manager: PhysicalCANManager,
    ) -> None:
        """Test J1939 message creation with custom timestamp."""
        address = J1939Address(source_address=0x21, parameter_group_number=0xF004)
        test_data = b"\xAA\xBB\xCC\xDD"
        custom_timestamp = 1234567.89

        message = can_manager.create_j1939_message(address, test_data, custom_timestamp)

        assert message.timestamp == custom_timestamp
        assert message.data == test_data


class TestAsyncIntegrationScenarios:
    """Test complete integration scenarios with full async isolation."""

    @pytest.mark.asyncio
    async def test_complete_interface_lifecycle(self) -> None:
        """Test complete interface lifecycle from creation to cleanup."""
        mock_error_handler = MagicMock(spec=CANErrorHandler)
        manager = PhysicalCANManager(error_handler=mock_error_handler)

        config = InterfaceConfiguration(
            interface_type=CANInterfaceType.SOCKETCAN,
            channel="vcan0",
            bitrate=BusSpeed.SPEED_250K,
        )

        with (
            patch("can.interface.Bus", return_value=MagicMock()),
            patch("asyncio.create_task", return_value=MagicMock()),
        ):
            # Create interface
            interface = await manager.create_interface("lifecycle_test", config)
            assert interface.interface_id == "lifecycle_test"

            # Connect interface
            with (
                patch.object(
                    interface, "_heartbeat_loop", new_callable=AsyncMock
                ) as mock_heartbeat_loop,
                patch.object(
                    interface, "_message_reception_loop", new_callable=AsyncMock
                ) as mock_message_reception_loop,
            ):
                connect_result = await manager.connect_interface("lifecycle_test")
                assert connect_result is True
                await mock_heartbeat_loop()
                await mock_message_reception_loop()
            # Send message
            test_message = can.Message(arbitration_id=0x123, data=b"\x01\x02\x03")
            with patch("asyncio.to_thread", new_callable=AsyncMock):
                send_results = await manager.broadcast_message(test_message)
                assert send_results["lifecycle_test"] is True

            # Disconnect interface
            disconnect_result = await manager.disconnect_interface("lifecycle_test")
            assert disconnect_result is True

    @pytest.mark.asyncio
    async def test_agricultural_message_processing_workflow(self) -> None:
        """Test agricultural CAN message processing workflow."""
        mock_error_handler = MagicMock(spec=CANErrorHandler)
        manager = PhysicalCANManager(error_handler=mock_error_handler)

        config = InterfaceConfiguration(
            interface_type=CANInterfaceType.SOCKETCAN,
            channel="vcan0",
            bitrate=BusSpeed.SPEED_250K,
        )

        # Create agricultural equipment addresses
        engine_address = J1939Address(
            priority=6,
            parameter_group_number=0xF004,
            source_address=0x00,  # Engine Controller
            pdu_format=0xF0,
            pdu_specific=0x04,
        )

        gps_address = J1939Address(
            priority=6,
            parameter_group_number=0xFEF3,
            source_address=0x01,  # GPS Receiver
            pdu_format=0xFE,
            pdu_specific=0xF3,
        )

        with (
            patch("can.interface.Bus"),
            patch("can.BufferedReader"),
            patch("can.Notifier"),
            patch("asyncio.create_task", return_value=MagicMock()),
        ):
            # Create and connect interface
            interface = await manager.create_interface("agricultural_test", config)

            # Collect received messages
            received_messages = []

            def message_callback(message: can.Message, interface_id: str) -> None:
                received_messages.append((message, interface_id))

            manager.add_global_callback(message_callback)

            with (
                patch.object(
                    interface, "_heartbeat_loop", new_callable=AsyncMock
                ) as mock_heartbeat_loop,
                patch.object(
                    interface, "_message_reception_loop", new_callable=AsyncMock
                ) as mock_message_reception_loop,
            ):
                await manager.connect_interface("agricultural_test")
                await mock_heartbeat_loop()
                await mock_message_reception_loop()

            # Create and send agricultural messages
            engine_data = b"\x64\x32\x00\x00\xFF\xFF\xFF\xFF"  # RPM, torque, etc.
            gps_data = b"\x12\x34\x56\x78\x9A\xBC\xDE\xF0"  # Lat/lon data

            engine_message = manager.create_j1939_message(engine_address, engine_data)
            gps_message = manager.create_j1939_message(gps_address, gps_data)

            with patch("asyncio.to_thread", new_callable=AsyncMock):
                # Test agricultural message broadcasting
                engine_results = await manager.broadcast_message(engine_message)
                gps_results = await manager.broadcast_message(gps_message)

                assert engine_results["agricultural_test"] is True
                assert gps_results["agricultural_test"] is True

                # Verify J1939 message structure
                assert engine_message.arbitration_id & 0xFF == 0x00  # Source address
                assert gps_message.arbitration_id & 0xFF == 0x01  # Source address
                assert engine_message.is_extended_id is True
                assert gps_message.is_extended_id is True

    @pytest.mark.asyncio
    async def test_multi_interface_agricultural_network(self) -> None:
        """Test multi-interface agricultural network setup."""
        mock_error_handler = MagicMock(spec=CANErrorHandler)
        manager = PhysicalCANManager(error_handler=mock_error_handler)

        # Create configurations for different agricultural network segments
        tractor_config = InterfaceConfiguration(
            interface_type=CANInterfaceType.SOCKETCAN,
            channel="can0",  # Tractor CAN bus
            bitrate=BusSpeed.SPEED_250K,
        )

        implement_config = InterfaceConfiguration(
            interface_type=CANInterfaceType.SOCKETCAN,
            channel="can1",  # Implement CAN bus
            bitrate=BusSpeed.SPEED_250K,
        )

        with (
            patch("can.interface.Bus"),
            patch("can.BufferedReader"),
            patch("can.Notifier"),
            patch("asyncio.create_task", return_value=MagicMock()),
        ):
            # Create interfaces for different agricultural network segments
            tractor_interface = await manager.create_interface("tractor_bus", tractor_config)
            implement_interface = await manager.create_interface("implement_bus", implement_config)

            assert len(manager._interfaces) == 2

            # Connect all interfaces
            with (
                patch.object(
                    tractor_interface, "_heartbeat_loop", new_callable=AsyncMock
                ) as mock_tractor_heartbeat_loop,
                patch.object(
                    tractor_interface, "_message_reception_loop", new_callable=AsyncMock
                ) as mock_tractor_message_reception_loop,
                patch.object(
                    implement_interface, "_heartbeat_loop", new_callable=AsyncMock
                ) as mock_implement_heartbeat_loop,
                patch.object(
                    implement_interface, "_message_reception_loop", new_callable=AsyncMock
                ) as mock_implement_message_reception_loop,
            ):
                connect_results = await manager.connect_all()

                assert connect_results["tractor_bus"] is True
                assert connect_results["implement_bus"] is True
                assert len(manager._active_interfaces) == 2

                await mock_tractor_heartbeat_loop()
                await mock_tractor_message_reception_loop()
                await mock_implement_heartbeat_loop()
                await mock_implement_message_reception_loop()

                # Test cross-network message broadcasting
                coordination_message = can.Message(
                    arbitration_id=0x18EA0000,  # Tractor-Implement Management
                    data=b"\x01\x02\x03\x04\x05\x06\x07\x08",
                    is_extended_id=True,
                )

                with patch("asyncio.to_thread", new_callable=AsyncMock):
                    broadcast_results = await manager.broadcast_message(coordination_message)

                    assert broadcast_results["tractor_bus"] is True
                    assert broadcast_results["implement_bus"] is True

                # Cleanup - disconnect all
                disconnect_results = await manager.disconnect_all()
                assert all(disconnect_results.values())
                assert len(manager._active_interfaces) == 0

    @pytest.mark.asyncio
    async def test_error_recovery_scenarios(self) -> None:
        """Test error recovery and resilience scenarios."""
        mock_error_handler = MagicMock(spec=CANErrorHandler)
        manager = PhysicalCANManager(error_handler=mock_error_handler)

        config = InterfaceConfiguration(
            interface_type=CANInterfaceType.SOCKETCAN,
            channel="vcan0",
            bitrate=BusSpeed.SPEED_250K,
        )

        interface = await manager.create_interface("error_test", config)

        # Test connection failure and retry
        with patch("can.interface.Bus", side_effect=OSError("Bus not available")):
            connect_result = await manager.connect_interface("error_test")
            assert connect_result is False

        # Test successful connection after failure
        with (
            patch("can.interface.Bus") as mock_bus,
            patch("can.BufferedReader"),
            patch("can.Notifier"),
            patch("asyncio.create_task", return_value=MagicMock()),
            patch.object(
                interface, "_heartbeat_loop", new_callable=AsyncMock
            ) as mock_heartbeat_loop,
            patch.object(
                interface, "_message_reception_loop", new_callable=AsyncMock
            ) as mock_message_reception_loop,
        ):
            mock_bus.return_value = MagicMock()

            connect_result = await manager.connect_interface("error_test")
            assert connect_result is True
            await mock_heartbeat_loop()
            await mock_message_reception_loop()

            # Test message sending error recovery
            test_message = can.Message(arbitration_id=0x123)

            # First attempt fails
            with patch(
                "asyncio.to_thread", new_callable=AsyncMock, side_effect=can.CanError("Bus error")
            ):
                send_result = await interface.send_message(test_message)
                assert send_result is False
                assert interface.status.errors_total == 1

            # Second attempt succeeds
            with patch("asyncio.to_thread", new_callable=AsyncMock):
                send_result = await interface.send_message(test_message)
                assert send_result is True
                assert interface.status.messages_sent == 1
