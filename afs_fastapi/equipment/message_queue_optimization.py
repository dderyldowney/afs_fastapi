"""
Message queue optimization with real-time and batch processing for agricultural CAN networks.

This module provides sophisticated message queue management optimized for agricultural
operations, supporting both real-time safety-critical messaging and batch processing
for efficiency in multi-tractor coordination scenarios.

Implementation follows Test-First Development (TDD) RED-GREEN-REFACTOR cycle.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import can

from afs_fastapi.equipment.congestion_detection import CongestionLevel, ThrottleDecision

# Configure logging for message queue optimization
logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """Message priority levels for agricultural operations."""

    CRITICAL = 1  # Safety-critical (emergency stop, collisions)
    HIGH = 2  # Operational safety (GPS, engine status)
    NORMAL = 3  # Standard operations (work status, coordination)
    LOW = 4  # Non-critical (diagnostics, maintenance)
    BACKGROUND = 5  # Background telemetry and logging


class ProcessingMode(Enum):
    """Queue processing modes for different operational contexts."""

    REAL_TIME = "real_time"  # Immediate processing for time-critical operations
    BATCH = "batch"  # Batched processing for efficiency
    ADAPTIVE = "adaptive"  # Switch between real-time and batch based on conditions
    EMERGENCY = "emergency"  # Emergency mode with minimal processing


class OperationContext(Enum):
    """Agricultural operation contexts affecting queue behavior."""

    FIELD_WORK = "field_work"  # Active field operations (planting, harvesting)
    TRANSPORT = "transport"  # Transport between fields
    MAINTENANCE = "maintenance"  # Maintenance mode
    IDLE = "idle"  # Equipment idle/parked
    EMERGENCY = "emergency"  # Emergency situation


@dataclass
class QueuedMessage:
    """Container for queued CAN messages with metadata."""

    message: can.Message
    priority: MessagePriority
    timestamp: datetime
    source_interface: str
    operation_context: OperationContext | None = None
    retry_count: int = 0
    max_retries: int = 3
    deadline: datetime | None = None
    batch_eligible: bool = True
    safety_critical: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if message has exceeded its deadline."""
        if self.deadline is None:
            return False
        return datetime.now() > self.deadline

    def is_safety_critical(self) -> bool:
        """Check if message is safety critical."""
        return self.priority == MessagePriority.CRITICAL or self.safety_critical

    def can_retry(self) -> bool:
        """Check if message can be retried."""
        return self.retry_count < self.max_retries


@dataclass
class QueueMetrics:
    """Real-time metrics for queue performance monitoring."""

    total_messages: int = 0
    messages_processed: int = 0
    messages_dropped: int = 0
    messages_expired: int = 0
    average_latency_ms: float = 0.0
    peak_latency_ms: float = 0.0
    queue_depth_by_priority: dict[MessagePriority, int] = field(default_factory=dict)
    throughput_messages_per_second: float = 0.0
    batch_efficiency_percentage: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

    def update_latency(self, latency_ms: float) -> None:
        """Update latency metrics."""
        if self.messages_processed == 0:
            self.average_latency_ms = latency_ms
        else:
            # Exponential moving average
            alpha = 0.1
            self.average_latency_ms = (alpha * latency_ms) + ((1 - alpha) * self.average_latency_ms)

        self.peak_latency_ms = max(self.peak_latency_ms, latency_ms)
        self.last_updated = datetime.now()


@dataclass
class BatchConfiguration:
    """Configuration for batch processing behavior."""

    max_batch_size: int = 50
    max_batch_age_ms: float = 100.0  # Maximum time to hold messages in batch
    min_batch_size: int = 5  # Minimum size to trigger batch processing
    priority_batching_enabled: bool = True
    context_aware_batching: bool = True
    adaptive_batch_sizing: bool = True
    batch_compression_enabled: bool = False


class MessageQueue:
    """High-performance message queue with real-time and batch processing capabilities."""

    def __init__(
        self,
        processing_mode: ProcessingMode = ProcessingMode.ADAPTIVE,
        batch_config: BatchConfiguration | None = None,
        max_queue_size: int = 10000,
    ) -> None:
        """Initialize message queue.

        Parameters
        ----------
        processing_mode : ProcessingMode
            Initial processing mode
        batch_config : BatchConfiguration, optional
            Batch processing configuration
        max_queue_size : int
            Maximum queue size before dropping messages
        """
        self.processing_mode = processing_mode
        self.batch_config = batch_config or BatchConfiguration()
        self.max_queue_size = max_queue_size

        # Priority-based queues
        self._queues: dict[MessagePriority, deque[QueuedMessage]] = {
            priority: deque() for priority in MessagePriority
        }

        # Batch processing storage
        self._batch_buffer: deque[QueuedMessage] = deque()
        self._last_batch_process_time = datetime.now()

        # Processing callbacks
        self._message_processors: list[Callable[[QueuedMessage], None]] = []
        self._batch_processors: list[Callable[[list[QueuedMessage]], None]] = []

        # Queue metrics
        self.metrics = QueueMetrics()

        # Control flags
        self._processing_active = False
        self._processing_task: asyncio.Task | None = None

        # Context tracking
        self._current_operation_context = OperationContext.IDLE
        self._congestion_level = CongestionLevel.NORMAL

    async def start_processing(self) -> None:
        """Start queue processing."""
        if self._processing_active:
            return

        self._processing_active = True
        self._processing_task = asyncio.create_task(self._processing_loop())
        logger.info(f"Started message queue processing in {self.processing_mode.value} mode")

    async def stop_processing(self) -> None:
        """Stop queue processing."""
        self._processing_active = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped message queue processing")

    def enqueue_message(
        self,
        message: can.Message,
        priority: MessagePriority,
        source_interface: str,
        operation_context: OperationContext | None = None,
        deadline: datetime | None = None,
        safety_critical: bool = False,
    ) -> bool:
        """Enqueue message for processing.

        Parameters
        ----------
        message : can.Message
            CAN message to queue
        priority : MessagePriority
            Message priority level
        source_interface : str
            Source interface identifier
        operation_context : OperationContext, optional
            Agricultural operation context
        deadline : datetime, optional
            Message processing deadline
        safety_critical : bool
            Mark message as safety critical

        Returns
        -------
        bool
            True if message was successfully queued
        """
        # Check queue capacity
        total_messages = sum(len(queue) for queue in self._queues.values())
        if total_messages >= self.max_queue_size:
            # For critical and high priority messages, try to drop lower priority to make room
            if priority in [MessagePriority.CRITICAL, MessagePriority.HIGH]:
                if self._drop_low_priority_message():
                    self.metrics.messages_dropped += 1
                else:
                    logger.warning("Queue full, dropping incoming high priority message")
                    self.metrics.messages_dropped += 1
                    return False
            else:
                # For lower priority messages, just drop them when queue is full
                logger.warning("Queue full, dropping incoming low priority message")
                self.metrics.messages_dropped += 1
                return False

        # Create queued message
        queued_msg = QueuedMessage(
            message=message,
            priority=priority,
            timestamp=datetime.now(),
            source_interface=source_interface,
            operation_context=operation_context,
            deadline=deadline,
            safety_critical=safety_critical,
        )

        # Add to appropriate priority queue
        self._queues[priority].append(queued_msg)
        self.metrics.total_messages += 1

        # Update queue depth metrics
        self.metrics.queue_depth_by_priority[priority] = len(self._queues[priority])

        logger.debug(
            f"Enqueued message: ID={message.arbitration_id:08X}, "
            f"priority={priority.name}, context={operation_context}"
        )

        return True

    def add_message_processor(self, processor: Callable[[QueuedMessage], None]) -> None:
        """Add message processor callback.

        Parameters
        ----------
        processor : Callable[[QueuedMessage], None]
            Message processing function
        """
        self._message_processors.append(processor)

    def add_batch_processor(self, processor: Callable[[list[QueuedMessage]], None]) -> None:
        """Add batch processor callback.

        Parameters
        ----------
        processor : Callable[[list[QueuedMessage]], None]
            Batch processing function
        """
        self._batch_processors.append(processor)

    def set_operation_context(self, context: OperationContext) -> None:
        """Update current operation context.

        Parameters
        ----------
        context : OperationContext
            New operation context
        """
        if self._current_operation_context != context:
            logger.info(
                f"Operation context changed: {self._current_operation_context.value} -> {context.value}"
            )
            self._current_operation_context = context
            self._adjust_processing_mode()

    def update_congestion_level(self, level: CongestionLevel) -> None:
        """Update network congestion level.

        Parameters
        ----------
        level : CongestionLevel
            Current congestion level
        """
        if self._congestion_level != level:
            logger.info(
                f"Congestion level changed: {self._congestion_level.value} -> {level.value}"
            )
            self._congestion_level = level
            self._adjust_processing_mode()

    def apply_throttle_decision(self, decision: ThrottleDecision) -> None:
        """Apply traffic throttling decision to queue processing.

        Parameters
        ----------
        decision : ThrottleDecision
            Throttling decision from congestion management
        """
        if decision.emergency_mode:
            self.processing_mode = ProcessingMode.EMERGENCY
            logger.warning("Queue switched to emergency processing mode")
        elif decision.recovery_mode:
            self.processing_mode = ProcessingMode.ADAPTIVE
            logger.info("Queue restored to adaptive processing mode")

        # Adjust batch configuration based on throttling
        if decision.severity_factor < 0.5:
            # Aggressive throttling - increase batch sizes
            self.batch_config.max_batch_size = min(100, int(self.batch_config.max_batch_size * 1.5))
            self.batch_config.max_batch_age_ms *= 1.2
        elif decision.severity_factor > 0.8:
            # Light throttling - reduce batch sizes for responsiveness
            self.batch_config.max_batch_size = max(10, int(self.batch_config.max_batch_size * 0.8))
            self.batch_config.max_batch_age_ms *= 0.9

    async def _processing_loop(self) -> None:
        """Main message processing loop."""
        while self._processing_active:
            try:
                if self.processing_mode == ProcessingMode.REAL_TIME:
                    await self._process_real_time()
                elif self.processing_mode == ProcessingMode.BATCH:
                    await self._process_batch()
                elif self.processing_mode == ProcessingMode.ADAPTIVE:
                    await self._process_adaptive()
                elif self.processing_mode == ProcessingMode.EMERGENCY:
                    await self._process_emergency()

                # Update throughput metrics
                self._update_throughput_metrics()

                # Brief sleep to prevent CPU spinning
                await asyncio.sleep(0.001)  # 1ms

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Processing loop error: {e}")
                await asyncio.sleep(0.1)

    async def _process_real_time(self) -> None:
        """Real-time processing - immediate message handling."""
        # Process messages in priority order
        for priority in MessagePriority:
            queue = self._queues[priority]
            if queue:
                message = queue.popleft()
                await self._process_single_message(message)

    async def _process_batch(self) -> None:
        """Batch processing - collect and process in groups."""
        # Collect messages for batching
        self._collect_for_batch()

        # Process batch if conditions are met
        if self._should_process_batch():
            await self._process_current_batch()

    async def _process_adaptive(self) -> None:
        """Adaptive processing - switch based on conditions."""
        # Process critical messages immediately
        critical_queue = self._queues[MessagePriority.CRITICAL]
        while critical_queue:
            message = critical_queue.popleft()
            await self._process_single_message(message)

        # Process other messages based on conditions
        if self._should_use_batch_processing():
            await self._process_batch()
        else:
            await self._process_real_time()

    async def _process_emergency(self) -> None:
        """Emergency processing - critical messages only."""
        # Only process critical and high priority messages
        for priority in [MessagePriority.CRITICAL, MessagePriority.HIGH]:
            queue = self._queues[priority]
            while queue:
                message = queue.popleft()
                await self._process_single_message(message)

        # Drop lower priority messages
        for priority in [MessagePriority.NORMAL, MessagePriority.LOW, MessagePriority.BACKGROUND]:
            dropped_count = len(self._queues[priority])
            self._queues[priority].clear()
            self.metrics.messages_dropped += dropped_count

    async def _process_single_message(self, message: QueuedMessage) -> None:
        """Process individual message."""
        start_time = time.time()

        try:
            # Check if message has expired
            if message.is_expired():
                self.metrics.messages_expired += 1
                logger.warning(f"Message expired: ID={message.message.arbitration_id:08X}")
                return

            # Call message processors
            for processor in self._message_processors:
                try:
                    processor(message)
                except Exception as e:
                    logger.error(f"Message processor error: {e}")

            self.metrics.messages_processed += 1

            # Update latency metrics
            latency_ms = (time.time() - start_time) * 1000
            self.metrics.update_latency(latency_ms)

        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            # Retry if possible
            if message.can_retry():
                message.retry_count += 1
                self._queues[message.priority].append(message)

    def _collect_for_batch(self) -> None:
        """Collect messages for batch processing."""
        # Collect from all queues except critical
        for priority in [
            MessagePriority.HIGH,
            MessagePriority.NORMAL,
            MessagePriority.LOW,
            MessagePriority.BACKGROUND,
        ]:
            queue = self._queues[priority]
            while queue and len(self._batch_buffer) < self.batch_config.max_batch_size:
                message = queue.popleft()
                if message.batch_eligible and not message.is_expired():
                    self._batch_buffer.append(message)
                else:
                    # Process immediately if not batch eligible or expired
                    asyncio.create_task(self._process_single_message(message))

    def _should_process_batch(self) -> bool:
        """Determine if batch should be processed."""
        if len(self._batch_buffer) == 0:
            return False

        # Size threshold
        if len(self._batch_buffer) >= self.batch_config.max_batch_size:
            return True

        # Age threshold
        time_since_last_batch = datetime.now() - self._last_batch_process_time
        if time_since_last_batch.total_seconds() * 1000 >= self.batch_config.max_batch_age_ms:
            return True

        # Minimum size threshold with timeout
        if (
            len(self._batch_buffer) >= self.batch_config.min_batch_size
            and time_since_last_batch.total_seconds() * 1000
            >= self.batch_config.max_batch_age_ms * 0.5
        ):
            return True

        return False

    async def _process_current_batch(self) -> None:
        """Process current batch of messages."""
        if not self._batch_buffer:
            return

        batch = list(self._batch_buffer)
        self._batch_buffer.clear()
        self._last_batch_process_time = datetime.now()

        start_time = time.time()

        try:
            # Call batch processors
            for processor in self._batch_processors:
                try:
                    processor(batch)
                except Exception as e:
                    logger.error(f"Batch processor error: {e}")

            # Update metrics
            self.metrics.messages_processed += len(batch)
            batch_latency_ms = (time.time() - start_time) * 1000

            # Update batch efficiency
            if len(batch) > 0:
                self.metrics.batch_efficiency_percentage = (
                    len(batch) / self.batch_config.max_batch_size
                ) * 100

            logger.debug(f"Processed batch of {len(batch)} messages in {batch_latency_ms:.2f}ms")

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            # Fall back to individual processing
            for message in batch:
                await self._process_single_message(message)

    def _should_use_batch_processing(self) -> bool:
        """Determine if batch processing should be used."""
        # Emergency context - never batch
        if self._current_operation_context == OperationContext.EMERGENCY:
            return False

        # High congestion - prefer batching for efficiency
        if self._congestion_level in [CongestionLevel.HIGH, CongestionLevel.CRITICAL]:
            return True

        # Field work - prefer real-time for precision
        if self._current_operation_context == OperationContext.FIELD_WORK:
            return False

        # Transport or idle - batching is acceptable
        if self._current_operation_context in [OperationContext.TRANSPORT, OperationContext.IDLE]:
            return True

        # Default to real-time
        return False

    def _adjust_processing_mode(self) -> None:
        """Adjust processing mode based on current conditions."""
        if self.processing_mode != ProcessingMode.ADAPTIVE:
            return

        # Context-based adjustments
        if self._current_operation_context == OperationContext.EMERGENCY:
            self.processing_mode = ProcessingMode.EMERGENCY
        elif self._congestion_level == CongestionLevel.CRITICAL:
            self.processing_mode = ProcessingMode.BATCH
        elif self._current_operation_context == OperationContext.FIELD_WORK:
            self.processing_mode = ProcessingMode.REAL_TIME
        else:
            # Stay in adaptive mode
            pass

    def _drop_low_priority_message(self) -> bool:
        """Drop lowest priority message to make room."""
        # Try to drop from background first, then low, then normal
        for priority in [MessagePriority.BACKGROUND, MessagePriority.LOW, MessagePriority.NORMAL]:
            queue = self._queues[priority]
            if queue:
                dropped_msg = queue.popleft()
                logger.debug(
                    f"Dropped {priority.name} priority message: ID={dropped_msg.message.arbitration_id:08X}"
                )
                return True
        return False

    def _update_throughput_metrics(self) -> None:
        """Update throughput metrics."""
        current_time = datetime.now()
        time_diff = (current_time - self.metrics.last_updated).total_seconds()

        if time_diff >= 1.0:  # Update every second
            messages_this_period = self.metrics.messages_processed
            self.metrics.throughput_messages_per_second = (
                messages_this_period / time_diff if time_diff > 0 else 0
            )
            self.metrics.last_updated = current_time

    def get_queue_status(self) -> dict[str, Any]:
        """Get comprehensive queue status.

        Returns
        -------
        dict[str, Any]
            Queue status information
        """
        return {
            "processing_mode": self.processing_mode.value,
            "operation_context": self._current_operation_context.value,
            "congestion_level": self._congestion_level.value,
            "queue_depths": {priority.name: len(queue) for priority, queue in self._queues.items()},
            "batch_buffer_size": len(self._batch_buffer),
            "metrics": {
                "total_messages": self.metrics.total_messages,
                "messages_processed": self.metrics.messages_processed,
                "messages_dropped": self.metrics.messages_dropped,
                "messages_expired": self.metrics.messages_expired,
                "average_latency_ms": self.metrics.average_latency_ms,
                "peak_latency_ms": self.metrics.peak_latency_ms,
                "throughput_messages_per_second": self.metrics.throughput_messages_per_second,
                "batch_efficiency_percentage": self.metrics.batch_efficiency_percentage,
            },
            "processing_active": self._processing_active,
        }


class MessageQueueManager:
    """Manages multiple message queues for different operational contexts."""

    def __init__(self) -> None:
        """Initialize message queue manager."""
        self._queues: dict[str, MessageQueue] = {}
        self._default_queue = MessageQueue()
        self._global_metrics = QueueMetrics()

    def create_queue(
        self,
        queue_id: str,
        processing_mode: ProcessingMode = ProcessingMode.ADAPTIVE,
        batch_config: BatchConfiguration | None = None,
    ) -> MessageQueue:
        """Create new message queue.

        Parameters
        ----------
        queue_id : str
            Unique queue identifier
        processing_mode : ProcessingMode
            Queue processing mode
        batch_config : BatchConfiguration, optional
            Batch processing configuration

        Returns
        -------
        MessageQueue
            Created message queue
        """
        if queue_id in self._queues:
            raise ValueError(f"Queue {queue_id} already exists")

        queue = MessageQueue(processing_mode, batch_config)
        self._queues[queue_id] = queue
        logger.info(f"Created message queue: {queue_id} (mode: {processing_mode.value})")
        return queue

    def get_queue(self, queue_id: str) -> MessageQueue:
        """Get message queue by ID.

        Parameters
        ----------
        queue_id : str
            Queue identifier

        Returns
        -------
        MessageQueue
            Message queue instance
        """
        return self._queues.get(queue_id, self._default_queue)

    async def start_all_queues(self) -> None:
        """Start processing for all queues."""
        tasks = []
        for queue in self._queues.values():
            tasks.append(queue.start_processing())

        if tasks:
            await asyncio.gather(*tasks)

        await self._default_queue.start_processing()
        logger.info("Started all message queue processing")

    async def stop_all_queues(self) -> None:
        """Stop processing for all queues."""
        tasks = []
        for queue in self._queues.values():
            tasks.append(queue.stop_processing())

        if tasks:
            await asyncio.gather(*tasks)

        await self._default_queue.stop_processing()
        logger.info("Stopped all message queue processing")

    def get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status.

        Returns
        -------
        dict[str, Any]
            System status including all queues
        """
        return {
            "total_queues": len(self._queues),
            "default_queue_status": self._default_queue.get_queue_status(),
            "queues": {
                queue_id: queue.get_queue_status() for queue_id, queue in self._queues.items()
            },
        }
