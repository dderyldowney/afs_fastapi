"""
Test suite for message queue optimization with real-time and batch processing.

Tests sophisticated message queue management optimized for agricultural operations,
supporting both real-time safety-critical messaging and batch processing efficiency.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

import can
import pytest

from afs_fastapi.equipment.congestion_detection import (
    CongestionLevel,
    ThrottleAction,
    ThrottleDecision,
)
from afs_fastapi.equipment.message_queue_optimization import (
    BatchConfiguration,
    MessagePriority,
    MessageQueue,
    MessageQueueManager,
    OperationContext,
    ProcessingMode,
    QueuedMessage,
    QueueMetrics,
)


class TestQueuedMessage:
    """Test queued message data structure."""

    def test_queued_message_initialization(self) -> None:
        """Test queued message initialization."""
        message = can.Message(arbitration_id=0x18FF1234, data=b"\x01\x02\x03")

        queued_msg = QueuedMessage(
            message=message,
            priority=MessagePriority.HIGH,
            timestamp=datetime.now(),
            source_interface="can0",
        )

        assert queued_msg.message == message
        assert queued_msg.priority == MessagePriority.HIGH
        assert queued_msg.source_interface == "can0"
        assert queued_msg.retry_count == 0
        assert queued_msg.max_retries == 3
        assert queued_msg.batch_eligible is True
        assert queued_msg.safety_critical is False

    def test_message_expiration_check(self) -> None:
        """Test message expiration logic."""
        message = can.Message(arbitration_id=0x18FF1234, data=b"\x01\x02\x03")

        # Message with future deadline
        future_deadline = datetime.now() + timedelta(seconds=10)
        queued_msg = QueuedMessage(
            message=message,
            priority=MessagePriority.NORMAL,
            timestamp=datetime.now(),
            source_interface="can0",
            deadline=future_deadline,
        )
        assert queued_msg.is_expired() is False

        # Message with past deadline
        past_deadline = datetime.now() - timedelta(seconds=10)
        queued_msg.deadline = past_deadline
        assert queued_msg.is_expired() is True

    def test_safety_critical_detection(self) -> None:
        """Test safety critical message detection."""
        message = can.Message(arbitration_id=0x18FF1234, data=b"\x01\x02\x03")

        # Critical priority message
        critical_msg = QueuedMessage(
            message=message,
            priority=MessagePriority.CRITICAL,
            timestamp=datetime.now(),
            source_interface="can0",
        )
        assert critical_msg.is_safety_critical() is True

        # Explicitly marked safety critical
        safety_msg = QueuedMessage(
            message=message,
            priority=MessagePriority.NORMAL,
            timestamp=datetime.now(),
            source_interface="can0",
            safety_critical=True,
        )
        assert safety_msg.is_safety_critical() is True

    def test_retry_capability(self) -> None:
        """Test message retry logic."""
        message = can.Message(arbitration_id=0x18FF1234, data=b"\x01\x02\x03")

        queued_msg = QueuedMessage(
            message=message,
            priority=MessagePriority.NORMAL,
            timestamp=datetime.now(),
            source_interface="can0",
            max_retries=2,
        )

        assert queued_msg.can_retry() is True
        queued_msg.retry_count = 1
        assert queued_msg.can_retry() is True
        queued_msg.retry_count = 2
        assert queued_msg.can_retry() is False


class TestQueueMetrics:
    """Test queue metrics tracking."""

    def test_metrics_initialization(self) -> None:
        """Test metrics initialization."""
        metrics = QueueMetrics()

        assert metrics.total_messages == 0
        assert metrics.messages_processed == 0
        assert metrics.messages_dropped == 0
        assert metrics.average_latency_ms == 0.0
        assert metrics.throughput_messages_per_second == 0.0

    def test_latency_update(self) -> None:
        """Test latency metrics update."""
        metrics = QueueMetrics()

        # First latency update
        metrics.update_latency(10.0)
        assert metrics.average_latency_ms == 10.0
        assert metrics.peak_latency_ms == 10.0

        # Second latency update (exponential moving average)
        metrics.messages_processed = 1
        metrics.update_latency(20.0)
        assert metrics.peak_latency_ms == 20.0
        # Average should be between 10 and 20 due to exponential moving average
        assert 10.0 < metrics.average_latency_ms < 20.0


class TestMessageQueue:
    """Test message queue core functionality."""

    @pytest.fixture
    def queue(self) -> MessageQueue:
        """Create message queue for testing."""
        return MessageQueue(processing_mode=ProcessingMode.REAL_TIME)

    @pytest.fixture
    def batch_queue(self) -> MessageQueue:
        """Create batch processing queue for testing."""
        batch_config = BatchConfiguration(
            max_batch_size=10,
            max_batch_age_ms=50.0,
            min_batch_size=3,
        )
        return MessageQueue(processing_mode=ProcessingMode.BATCH, batch_config=batch_config)

    def test_queue_initialization(self, queue: MessageQueue) -> None:
        """Test queue initialization."""
        assert queue.processing_mode == ProcessingMode.REAL_TIME
        assert queue.max_queue_size == 10000
        assert not queue._processing_active
        assert len(queue._queues) == len(MessagePriority)

    def test_message_enqueuing(self, queue: MessageQueue) -> None:
        """Test message enqueuing with different priorities."""
        message = can.Message(arbitration_id=0x18FF1234, data=b"\x01\x02\x03")

        # Enqueue high priority message
        success = queue.enqueue_message(
            message=message,
            priority=MessagePriority.HIGH,
            source_interface="can0",
        )

        assert success is True
        assert queue.metrics.total_messages == 1
        assert len(queue._queues[MessagePriority.HIGH]) == 1

        # Enqueue critical priority message
        critical_message = can.Message(arbitration_id=0x18FF5678, data=b"\x04\x05\x06")
        success = queue.enqueue_message(
            message=critical_message,
            priority=MessagePriority.CRITICAL,
            source_interface="can0",
            safety_critical=True,
        )

        assert success is True
        assert queue.metrics.total_messages == 2
        assert len(queue._queues[MessagePriority.CRITICAL]) == 1

    def test_message_processor_registration(self, queue: MessageQueue) -> None:
        """Test message processor callback registration."""
        processed_messages = []

        def test_processor(message: QueuedMessage) -> None:
            processed_messages.append(message)

        queue.add_message_processor(test_processor)
        assert len(queue._message_processors) == 1

    def test_batch_processor_registration(self, queue: MessageQueue) -> None:
        """Test batch processor callback registration."""
        processed_batches = []

        def test_batch_processor(batch: list[QueuedMessage]) -> None:
            processed_batches.append(batch)

        queue.add_batch_processor(test_batch_processor)
        assert len(queue._batch_processors) == 1

    def test_operation_context_update(self, queue: MessageQueue) -> None:
        """Test operation context updates."""
        queue.set_operation_context(OperationContext.FIELD_WORK)
        assert queue._current_operation_context == OperationContext.FIELD_WORK

        queue.set_operation_context(OperationContext.TRANSPORT)
        assert queue._current_operation_context == OperationContext.TRANSPORT

    def test_congestion_level_update(self, queue: MessageQueue) -> None:
        """Test congestion level updates."""
        queue.update_congestion_level(CongestionLevel.HIGH)
        assert queue._congestion_level == CongestionLevel.HIGH

        queue.update_congestion_level(CongestionLevel.CRITICAL)
        assert queue._congestion_level == CongestionLevel.CRITICAL

    def test_throttle_decision_application(self, queue: MessageQueue) -> None:
        """Test applying traffic throttling decisions."""
        # Emergency throttle decision
        emergency_decision = ThrottleDecision(
            action=ThrottleAction.EMERGENCY_THROTTLE,
            severity_factor=0.2,
            affected_priorities=["HIGH"],
            emergency_mode=True,
        )

        queue.apply_throttle_decision(emergency_decision)
        assert queue.processing_mode == ProcessingMode.EMERGENCY

        # Recovery decision
        recovery_decision = ThrottleDecision(
            action=ThrottleAction.RESTORE_NORMAL,
            severity_factor=1.0,
            affected_priorities=[],
            recovery_mode=True,
        )

        queue.apply_throttle_decision(recovery_decision)
        assert queue.processing_mode == ProcessingMode.ADAPTIVE

    @pytest.mark.asyncio
    async def test_queue_processing_lifecycle(self, queue: MessageQueue) -> None:
        """Test queue processing start and stop."""
        assert not queue._processing_active

        await queue.start_processing()
        assert queue._processing_active
        assert queue._processing_task is not None

        await queue.stop_processing()
        assert not queue._processing_active

    @pytest.mark.asyncio
    async def test_real_time_message_processing(self, queue: MessageQueue) -> None:
        """Test real-time message processing."""
        processed_messages = []

        def test_processor(message: QueuedMessage) -> None:
            processed_messages.append(message)

        queue.add_message_processor(test_processor)
        await queue.start_processing()

        # Enqueue test messages
        message1 = can.Message(arbitration_id=0x18FF1234, data=b"\x01\x02\x03")
        message2 = can.Message(arbitration_id=0x18FF5678, data=b"\x04\x05\x06")

        queue.enqueue_message(message1, MessagePriority.HIGH, "can0")
        queue.enqueue_message(message2, MessagePriority.CRITICAL, "can0")

        # Allow processing time
        await asyncio.sleep(0.1)
        await queue.stop_processing()

        # Critical priority should be processed first
        assert len(processed_messages) == 2
        assert processed_messages[0].priority == MessagePriority.CRITICAL
        assert processed_messages[1].priority == MessagePriority.HIGH

    @pytest.mark.asyncio
    async def test_batch_processing(self, batch_queue: MessageQueue) -> None:
        """Test batch message processing."""
        processed_batches = []

        def test_batch_processor(batch: list[QueuedMessage]) -> None:
            processed_batches.append(batch)

        batch_queue.add_batch_processor(test_batch_processor)
        await batch_queue.start_processing()

        # Enqueue enough messages to trigger batch processing
        for i in range(5):
            message = can.Message(arbitration_id=0x18FF1000 + i, data=b"\x01\x02\x03")
            batch_queue.enqueue_message(message, MessagePriority.NORMAL, "can0")

        # Allow processing time
        await asyncio.sleep(0.1)
        await batch_queue.stop_processing()

        # Should have at least one batch processed
        assert len(processed_batches) >= 1
        assert len(processed_batches[0]) > 0

    def test_queue_capacity_management(self, queue: MessageQueue) -> None:
        """Test queue capacity and message dropping."""
        # Set small queue size for testing
        queue.max_queue_size = 5

        messages = []
        for i in range(10):
            message = can.Message(arbitration_id=0x18FF1000 + i, data=b"\x01\x02\x03")
            success = queue.enqueue_message(message, MessagePriority.BACKGROUND, "can0")
            messages.append((message, success))

        # First 5 should succeed, later ones might be dropped
        successful_enqueues = sum(1 for _, success in messages if success)
        assert successful_enqueues <= 5
        assert queue.metrics.messages_dropped > 0

    def test_agricultural_context_awareness(self, queue: MessageQueue) -> None:
        """Test agricultural operation context awareness."""
        # Field work context - should prefer real-time
        queue.set_operation_context(OperationContext.FIELD_WORK)
        queue.processing_mode = ProcessingMode.ADAPTIVE
        assert not queue._should_use_batch_processing()

        # Transport context - batching acceptable
        queue.set_operation_context(OperationContext.TRANSPORT)
        assert queue._should_use_batch_processing()

        # Emergency context - never batch
        queue.set_operation_context(OperationContext.EMERGENCY)
        assert not queue._should_use_batch_processing()

    def test_priority_based_message_dropping(self, queue: MessageQueue) -> None:
        """Test priority-based message dropping when queue is full."""
        queue.max_queue_size = 3

        # Fill queue with background messages
        for i in range(3):
            message = can.Message(arbitration_id=0x18FF1000 + i, data=b"\x01\x02\x03")
            queue.enqueue_message(message, MessagePriority.BACKGROUND, "can0")

        # Add high priority message - should drop background message
        high_priority_msg = can.Message(arbitration_id=0x18FF2000, data=b"\x04\x05\x06")
        success = queue.enqueue_message(high_priority_msg, MessagePriority.HIGH, "can0")

        assert success is True
        assert queue.metrics.messages_dropped > 0

    def test_queue_status_reporting(self, queue: MessageQueue) -> None:
        """Test comprehensive queue status reporting."""
        # Add some messages
        message = can.Message(arbitration_id=0x18FF1234, data=b"\x01\x02\x03")
        queue.enqueue_message(message, MessagePriority.HIGH, "can0")
        queue.enqueue_message(message, MessagePriority.NORMAL, "can0")

        status = queue.get_queue_status()

        assert "processing_mode" in status
        assert "operation_context" in status
        assert "queue_depths" in status
        assert "metrics" in status
        assert status["queue_depths"]["HIGH"] == 1
        assert status["queue_depths"]["NORMAL"] == 1


class TestBatchConfiguration:
    """Test batch processing configuration."""

    def test_batch_config_initialization(self) -> None:
        """Test batch configuration initialization."""
        config = BatchConfiguration()

        assert config.max_batch_size == 50
        assert config.max_batch_age_ms == 100.0
        assert config.min_batch_size == 5
        assert config.priority_batching_enabled is True
        assert config.context_aware_batching is True

    def test_custom_batch_config(self) -> None:
        """Test custom batch configuration."""
        config = BatchConfiguration(
            max_batch_size=25,
            max_batch_age_ms=50.0,
            min_batch_size=3,
            priority_batching_enabled=False,
        )

        assert config.max_batch_size == 25
        assert config.max_batch_age_ms == 50.0
        assert config.min_batch_size == 3
        assert config.priority_batching_enabled is False


class TestMessageQueueManager:
    """Test message queue manager for multiple queues."""

    @pytest.fixture
    def manager(self) -> MessageQueueManager:
        """Create message queue manager for testing."""
        return MessageQueueManager()

    def test_manager_initialization(self, manager: MessageQueueManager) -> None:
        """Test manager initialization."""
        assert len(manager._queues) == 0
        assert manager._default_queue is not None

    def test_queue_creation(self, manager: MessageQueueManager) -> None:
        """Test creating new queues."""
        queue = manager.create_queue("field_operations", ProcessingMode.REAL_TIME)

        assert "field_operations" in manager._queues
        assert queue.processing_mode == ProcessingMode.REAL_TIME

        # Test duplicate queue creation error
        with pytest.raises(ValueError, match="Queue field_operations already exists"):
            manager.create_queue("field_operations", ProcessingMode.BATCH)

    def test_queue_retrieval(self, manager: MessageQueueManager) -> None:
        """Test queue retrieval."""
        created_queue = manager.create_queue("test_queue", ProcessingMode.BATCH)
        retrieved_queue = manager.get_queue("test_queue")

        assert created_queue is retrieved_queue

        # Non-existent queue should return default
        default_queue = manager.get_queue("non_existent")
        assert default_queue is manager._default_queue

    @pytest.mark.asyncio
    async def test_bulk_queue_operations(self, manager: MessageQueueManager) -> None:
        """Test starting and stopping all queues."""
        manager.create_queue("queue1", ProcessingMode.REAL_TIME)
        manager.create_queue("queue2", ProcessingMode.BATCH)

        await manager.start_all_queues()

        # All queues should be processing
        for queue in manager._queues.values():
            assert queue._processing_active
        assert manager._default_queue._processing_active

        await manager.stop_all_queues()

        # All queues should be stopped
        for queue in manager._queues.values():
            assert not queue._processing_active
        assert not manager._default_queue._processing_active

    def test_system_status_reporting(self, manager: MessageQueueManager) -> None:
        """Test comprehensive system status reporting."""
        manager.create_queue("queue1", ProcessingMode.REAL_TIME)
        manager.create_queue("queue2", ProcessingMode.BATCH)

        status = manager.get_system_status()

        assert status["total_queues"] == 2
        assert "default_queue_status" in status
        assert "queues" in status
        assert "queue1" in status["queues"]
        assert "queue2" in status["queues"]


class TestIntegratedQueueOptimization:
    """Test integrated queue optimization scenarios."""

    @pytest.mark.asyncio
    async def test_field_operation_workflow(self) -> None:
        """Test queue behavior during field operations."""
        queue = MessageQueue(processing_mode=ProcessingMode.ADAPTIVE)
        processed_messages = []

        def test_processor(message: QueuedMessage) -> None:
            processed_messages.append(message)

        queue.add_message_processor(test_processor)
        queue.set_operation_context(OperationContext.FIELD_WORK)
        await queue.start_processing()

        # Enqueue mixed priority messages
        critical_msg = can.Message(
            arbitration_id=0x18FF0001, data=b"\xFF\xFF\xFF"
        )  # Emergency stop
        normal_msg = can.Message(arbitration_id=0x18FF0002, data=b"\x01\x02\x03")  # Position update

        queue.enqueue_message(normal_msg, MessagePriority.NORMAL, "can0")
        queue.enqueue_message(critical_msg, MessagePriority.CRITICAL, "can0", safety_critical=True)

        await asyncio.sleep(0.1)
        await queue.stop_processing()

        # Critical message should be processed first
        assert len(processed_messages) == 2
        assert processed_messages[0].priority == MessagePriority.CRITICAL
        assert processed_messages[0].safety_critical is True

    @pytest.mark.asyncio
    async def test_congestion_adaptive_behavior(self) -> None:
        """Test queue adaptation to network congestion."""
        queue = MessageQueue(processing_mode=ProcessingMode.ADAPTIVE)

        # Normal congestion - should process normally
        queue.update_congestion_level(CongestionLevel.NORMAL)
        assert queue.processing_mode == ProcessingMode.ADAPTIVE

        # High congestion - may switch to batch mode
        queue.update_congestion_level(CongestionLevel.HIGH)
        queue._adjust_processing_mode()

        # Critical congestion with throttle decision
        throttle_decision = ThrottleDecision(
            action=ThrottleAction.EMERGENCY_THROTTLE,
            severity_factor=0.3,
            affected_priorities=["HIGH"],
            emergency_mode=True,
        )

        queue.apply_throttle_decision(throttle_decision)
        assert queue.processing_mode == ProcessingMode.EMERGENCY

    @pytest.mark.asyncio
    async def test_transport_vs_field_processing(self) -> None:
        """Test different processing behavior for transport vs field operations."""
        field_queue = MessageQueue(processing_mode=ProcessingMode.ADAPTIVE)
        transport_queue = MessageQueue(processing_mode=ProcessingMode.ADAPTIVE)

        field_queue.set_operation_context(OperationContext.FIELD_WORK)
        transport_queue.set_operation_context(OperationContext.TRANSPORT)

        # Field work should prefer real-time processing
        assert not field_queue._should_use_batch_processing()

        # Transport should allow batch processing
        assert transport_queue._should_use_batch_processing()

    @pytest.mark.asyncio
    async def test_message_expiration_handling(self) -> None:
        """Test handling of expired messages."""
        queue = MessageQueue(processing_mode=ProcessingMode.REAL_TIME)
        processed_messages = []

        def test_processor(message: QueuedMessage) -> None:
            processed_messages.append(message)

        queue.add_message_processor(test_processor)
        await queue.start_processing()

        # Enqueue message with past deadline
        expired_msg = can.Message(arbitration_id=0x18FF1234, data=b"\x01\x02\x03")
        past_deadline = datetime.now() - timedelta(seconds=10)

        queue.enqueue_message(
            expired_msg,
            MessagePriority.NORMAL,
            "can0",
            deadline=past_deadline,
        )

        await asyncio.sleep(0.1)
        await queue.stop_processing()

        # Expired message should not be processed
        assert len(processed_messages) == 0
        assert queue.metrics.messages_expired > 0

    @pytest.mark.asyncio
    async def test_safety_critical_message_priority(self) -> None:
        """Test that safety-critical messages always get priority."""
        queue = MessageQueue(processing_mode=ProcessingMode.EMERGENCY)
        processed_messages = []

        def test_processor(message: QueuedMessage) -> None:
            processed_messages.append(message)

        queue.add_message_processor(test_processor)
        await queue.start_processing()

        # Enqueue mixed messages in emergency mode
        safety_msg = can.Message(arbitration_id=0x18FF0001, data=b"\xFF\xFF\xFF")
        normal_msg = can.Message(arbitration_id=0x18FF0002, data=b"\x01\x02\x03")
        background_msg = can.Message(arbitration_id=0x18FF0003, data=b"\x04\x05\x06")

        queue.enqueue_message(background_msg, MessagePriority.BACKGROUND, "can0")
        queue.enqueue_message(normal_msg, MessagePriority.NORMAL, "can0")
        queue.enqueue_message(safety_msg, MessagePriority.CRITICAL, "can0", safety_critical=True)

        await asyncio.sleep(0.1)
        await queue.stop_processing()

        # Only critical and high priority messages should be processed in emergency mode
        assert len(processed_messages) == 1
        assert processed_messages[0].priority == MessagePriority.CRITICAL
        assert queue.metrics.messages_dropped > 0  # Background and normal should be dropped
