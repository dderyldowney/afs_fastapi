"""High-performance CAN message buffering and batch processing for time-series storage.

This module provides memory-efficient buffering of CAN messages with configurable
batch processing for optimal database write performance in high-throughput
agricultural environments.

Implementation follows Test-First Development (TDD) GREEN phase.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum

import can

from afs_fastapi.core.can_frame_codec import CANFrameCodec, DecodedPGN
from afs_fastapi.database.can_time_series_schema import CANMessagePriority

# Configure logging for message buffer
logger = logging.getLogger(__name__)


class BufferStrategy(Enum):
    """Buffer management strategies for different use cases."""

    TIME_BASED = "time_based"  # Flush every N seconds
    SIZE_BASED = "size_based"  # Flush when buffer reaches N messages
    PRIORITY_BASED = "priority"  # Flush based on message priority
    ADAPTIVE = "adaptive"  # Adapt based on system load


class CompressionLevel(Enum):
    """Message compression levels for storage optimization."""

    NONE = 0  # No compression
    LOW = 1  # Basic compression
    MEDIUM = 2  # Balanced compression
    HIGH = 3  # Maximum compression


@dataclass
class BufferConfiguration:
    """Configuration for CAN message buffer behavior."""

    # Buffer size limits
    max_buffer_size: int = 10000  # Maximum messages in buffer
    max_memory_mb: int = 100  # Maximum memory usage (MB)

    # Flush timing
    flush_interval: float = 5.0  # Seconds between flushes
    max_flush_time: float = 30.0  # Maximum time before forced flush

    # Batch processing
    batch_size: int = 1000  # Messages per batch write
    max_batch_size: int = 5000  # Maximum batch size

    # Buffer strategy
    strategy: BufferStrategy = BufferStrategy.ADAPTIVE
    priority_weights: dict[CANMessagePriority, float] = field(
        default_factory=lambda: {
            CANMessagePriority.CRITICAL: 1.0,
            CANMessagePriority.HIGH: 0.8,
            CANMessagePriority.NORMAL: 0.6,
            CANMessagePriority.LOW: 0.4,
        }
    )

    # Performance tuning
    compression_level: CompressionLevel = CompressionLevel.LOW
    enable_deduplication: bool = True
    dedup_window_seconds: float = 1.0

    # Quality control
    enable_validation: bool = True
    drop_invalid_messages: bool = False
    max_decode_failures: int = 100  # Per flush cycle


@dataclass
class BufferedCANMessage:
    """Buffered CAN message with metadata."""

    # Original message
    raw_message: can.Message
    interface_id: str
    reception_time: datetime

    # Processing metadata
    buffer_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    priority: CANMessagePriority = CANMessagePriority.NORMAL
    processing_attempts: int = 0

    # Decoded data (cached)
    decoded_message: DecodedPGN | None = None
    decoding_error: str | None = None

    # Quality indicators
    is_valid: bool = True
    validation_errors: list[str] = field(default_factory=list)

    # Storage hints
    retention_policy: str = "standard"
    compression_hint: CompressionLevel = CompressionLevel.MEDIUM


@dataclass
class BufferStatistics:
    """Buffer performance and health statistics."""

    # Message counts
    total_received: int = 0
    total_buffered: int = 0
    total_flushed: int = 0
    total_dropped: int = 0

    # Buffer state
    current_buffer_size: int = 0
    current_memory_usage: float = 0.0  # MB
    buffer_utilization: float = 0.0  # Percentage

    # Performance metrics
    avg_flush_time: float = 0.0  # Seconds
    avg_batch_size: float = 0.0
    messages_per_second: float = 0.0

    # Quality metrics
    decode_success_rate: float = 0.0  # Percentage
    validation_pass_rate: float = 0.0  # Percentage
    deduplication_rate: float = 0.0  # Percentage

    # Timing
    last_flush_time: datetime | None = None
    uptime: timedelta = field(default_factory=lambda: timedelta())

    # Error tracking
    decode_failures: int = 0
    validation_failures: int = 0
    flush_failures: int = 0


class CANMessageBuffer:
    """High-performance CAN message buffer with adaptive batch processing."""

    def __init__(
        self,
        config: BufferConfiguration,
        codec: CANFrameCodec,
        flush_callback: Callable[[list[BufferedCANMessage]], bool],
    ) -> None:
        """Initialize CAN message buffer.

        Parameters
        ----------
        config : BufferConfiguration
            Buffer configuration
        codec : CANFrameCodec
            CAN frame codec for message decoding
        flush_callback : Callable[[list[BufferedCANMessage]], bool]
            Callback function for batch writes (returns success status)
        """
        self.config = config
        self.codec = codec
        self.flush_callback = flush_callback

        # Buffer storage
        self._buffer: deque[BufferedCANMessage] = deque()
        self._priority_buffers: dict[CANMessagePriority, deque[BufferedCANMessage]] = {
            priority: deque() for priority in CANMessagePriority
        }

        # Deduplication tracking
        self._message_hashes: dict[str, datetime] = {}
        self._dedup_cleanup_interval = 60.0  # seconds

        # Statistics and monitoring
        self.stats = BufferStatistics()
        self._start_time = datetime.now(UTC)
        self._last_stats_update = datetime.now(UTC)

        # Async processing
        self._flush_task: asyncio.Task | None = None
        self._stats_task: asyncio.Task | None = None
        self._running = False
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Start the buffer processing tasks."""
        if self._running:
            return

        self._running = True
        self._start_time = datetime.now(UTC)

        # Start background tasks
        self._flush_task = asyncio.create_task(self._flush_loop())
        self._stats_task = asyncio.create_task(self._stats_loop())

        logger.info(f"CAN message buffer started with strategy: {self.config.strategy.value}")

    async def stop(self) -> None:
        """Stop the buffer and flush remaining messages."""
        if not self._running:
            return

        self._running = False

        # Cancel background tasks
        if self._flush_task:
            self._flush_task.cancel()
        if self._stats_task:
            self._stats_task.cancel()

        # Final flush
        await self._flush_all_buffers()

        logger.info("CAN message buffer stopped")

    async def add_message(
        self,
        message: can.Message,
        interface_id: str,
        priority: CANMessagePriority | None = None,
    ) -> bool:
        """Add a CAN message to the buffer.

        Parameters
        ----------
        message : can.Message
            CAN message to buffer
        interface_id : str
            Interface that received the message
        priority : CANMessagePriority | None
            Message priority (auto-detected if None)

        Returns
        -------
        bool
            True if message was added successfully
        """
        try:
            async with self._lock:
                # Check buffer capacity
                if len(self._buffer) >= self.config.max_buffer_size:
                    if self.config.strategy == BufferStrategy.PRIORITY_BASED:
                        # Drop lowest priority message
                        if not await self._drop_lowest_priority():
                            self.stats.total_dropped += 1
                            return False
                    else:
                        self.stats.total_dropped += 1
                        return False

                # Create buffered message
                buffered_msg = BufferedCANMessage(
                    raw_message=message,
                    interface_id=interface_id,
                    reception_time=datetime.fromtimestamp(message.timestamp or time.time()),
                    priority=priority or self._detect_message_priority(message),
                )

                # Deduplication check
                if self.config.enable_deduplication:
                    msg_hash = self._calculate_message_hash(message)
                    if self._is_duplicate(msg_hash):
                        return True  # Silently drop duplicate

                # Validation
                if self.config.enable_validation:
                    if not await self._validate_message(buffered_msg):
                        if self.config.drop_invalid_messages:
                            self.stats.validation_failures += 1
                            return False

                # Decode message (async to avoid blocking)
                if buffered_msg.priority in [CANMessagePriority.CRITICAL, CANMessagePriority.HIGH]:
                    await self._decode_message(buffered_msg)

                # Add to appropriate buffer
                if self.config.strategy == BufferStrategy.PRIORITY_BASED:
                    self._priority_buffers[buffered_msg.priority].append(buffered_msg)
                else:
                    self._buffer.append(buffered_msg)

                # Update statistics
                self.stats.total_received += 1
                self.stats.total_buffered += 1
                self.stats.current_buffer_size = len(self._buffer) + sum(
                    len(pb) for pb in self._priority_buffers.values()
                )

                return True

        except Exception as e:
            logger.error(f"Failed to add message to buffer: {e}")
            return False

    async def force_flush(self) -> bool:
        """Force immediate flush of all buffered messages.

        Returns
        -------
        bool
            True if flush was successful
        """
        async with self._lock:
            return await self._flush_all_buffers()

    def get_statistics(self) -> BufferStatistics:
        """Get current buffer statistics.

        Returns
        -------
        BufferStatistics
            Current statistics
        """
        # Update real-time stats
        self.stats.current_buffer_size = len(self._buffer) + sum(
            len(pb) for pb in self._priority_buffers.values()
        )
        self.stats.uptime = datetime.now(UTC) - self._start_time
        self.stats.buffer_utilization = (
            self.stats.current_buffer_size / self.config.max_buffer_size * 100
        )

        return self.stats

    async def _flush_loop(self) -> None:
        """Background task for periodic buffer flushing."""
        while self._running:
            try:
                # Determine flush strategy
                should_flush = await self._should_flush()

                if should_flush:
                    async with self._lock:
                        await self._flush_all_buffers()

                # Adaptive sleep based on buffer load
                sleep_time = self._calculate_sleep_time()
                await asyncio.sleep(sleep_time)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Flush loop error: {e}")
                await asyncio.sleep(1.0)

    async def _should_flush(self) -> bool:
        """Determine if buffer should be flushed.

        Returns
        -------
        bool
            True if buffer should be flushed
        """
        current_time = datetime.now(UTC)
        time_since_last_flush = (
            current_time - (self.stats.last_flush_time or self._start_time)
        ).total_seconds()

        # Time-based flush
        if time_since_last_flush >= self.config.flush_interval:
            return True

        # Size-based flush
        if self.stats.current_buffer_size >= self.config.batch_size:
            return True

        # Priority-based flush (critical messages present)
        if (
            self.config.strategy == BufferStrategy.PRIORITY_BASED
            and len(self._priority_buffers[CANMessagePriority.CRITICAL]) > 0
        ):
            return True

        # Forced flush (maximum time exceeded)
        if time_since_last_flush >= self.config.max_flush_time:
            return True

        return False

    async def _flush_all_buffers(self) -> bool:
        """Flush all buffered messages to storage.

        Returns
        -------
        bool
            True if flush was successful
        """
        start_time = time.time()

        try:
            # Collect messages from all buffers
            messages_to_flush: list[BufferedCANMessage] = []

            if self.config.strategy == BufferStrategy.PRIORITY_BASED:
                # Flush by priority order
                for priority in CANMessagePriority:
                    buffer = self._priority_buffers[priority]
                    while buffer and len(messages_to_flush) < self.config.max_batch_size:
                        messages_to_flush.append(buffer.popleft())
            else:
                # Flush main buffer
                while self._buffer and len(messages_to_flush) < self.config.max_batch_size:
                    messages_to_flush.append(self._buffer.popleft())

            if not messages_to_flush:
                return True

            # Decode any remaining messages
            for msg in messages_to_flush:
                if msg.decoded_message is None and msg.decoding_error is None:
                    await self._decode_message(msg)

            # Call flush callback
            success = self.flush_callback(messages_to_flush)

            if success:
                self.stats.total_flushed += len(messages_to_flush)
                self.stats.last_flush_time = datetime.now(UTC)

                # Update performance metrics
                flush_time = time.time() - start_time
                self.stats.avg_flush_time = (self.stats.avg_flush_time * 0.9) + (flush_time * 0.1)
                self.stats.avg_batch_size = (self.stats.avg_batch_size * 0.9) + (
                    len(messages_to_flush) * 0.1
                )

                logger.debug(f"Flushed {len(messages_to_flush)} messages in {flush_time:.3f}s")
            else:
                # Return messages to buffer on failure
                if self.config.strategy == BufferStrategy.PRIORITY_BASED:
                    for msg in reversed(messages_to_flush):
                        self._priority_buffers[msg.priority].appendleft(msg)
                else:
                    self._buffer.extendleft(reversed(messages_to_flush))

                self.stats.flush_failures += 1
                logger.warning(f"Failed to flush {len(messages_to_flush)} messages")

            return success

        except Exception as e:
            logger.error(f"Buffer flush error: {e}")
            self.stats.flush_failures += 1
            return False

    async def _decode_message(self, buffered_msg: BufferedCANMessage) -> None:
        """Decode a buffered CAN message.

        Parameters
        ----------
        buffered_msg : BufferedCANMessage
            Message to decode
        """
        try:
            decoded = self.codec.decode_message(buffered_msg.raw_message)
            if decoded:
                buffered_msg.decoded_message = decoded
            else:
                buffered_msg.decoding_error = "Decoding returned None"
                self.stats.decode_failures += 1

        except Exception as e:
            buffered_msg.decoding_error = str(e)
            self.stats.decode_failures += 1

    async def _validate_message(self, buffered_msg: BufferedCANMessage) -> bool:
        """Validate a buffered CAN message.

        Parameters
        ----------
        buffered_msg : BufferedCANMessage
            Message to validate

        Returns
        -------
        bool
            True if message is valid
        """
        errors = []

        # Basic CAN message validation
        if buffered_msg.raw_message.dlc > 8:
            errors.append("DLC exceeds 8 bytes")

        if len(buffered_msg.raw_message.data) != buffered_msg.raw_message.dlc:
            errors.append("Data length doesn't match DLC")

        # Extended validation for ISOBUS
        if buffered_msg.raw_message.is_extended_id:
            if buffered_msg.raw_message.arbitration_id > 0x1FFFFFFF:
                errors.append("Invalid 29-bit CAN ID")
        else:
            if buffered_msg.raw_message.arbitration_id > 0x7FF:
                errors.append("Invalid 11-bit CAN ID")

        buffered_msg.validation_errors = errors
        buffered_msg.is_valid = len(errors) == 0

        if not buffered_msg.is_valid:
            self.stats.validation_failures += 1

        return buffered_msg.is_valid

    def _detect_message_priority(self, message: can.Message) -> CANMessagePriority:
        """Detect message priority from CAN ID.

        Parameters
        ----------
        message : can.Message
            CAN message

        Returns
        -------
        CANMessagePriority
            Detected priority level
        """
        if not message.is_extended_id:
            return CANMessagePriority.LOW

        # Extract J1939 priority
        j1939_priority = (message.arbitration_id >> 26) & 0x07

        # Extract PGN for content-based priority
        pdu_format = (message.arbitration_id >> 16) & 0xFF

        # Emergency and safety messages
        if pdu_format in [0xE0, 0xE1, 0xE2]:  # Emergency codes
            return CANMessagePriority.CRITICAL

        # Engine and transmission critical
        if pdu_format in [0xF0]:  # Engine/transmission data
            return CANMessagePriority.HIGH

        # Based on J1939 priority
        if j1939_priority <= 2:
            return CANMessagePriority.HIGH
        elif j1939_priority <= 4:
            return CANMessagePriority.NORMAL
        else:
            return CANMessagePriority.LOW

    def _calculate_message_hash(self, message: can.Message) -> str:
        """Calculate hash for message deduplication.

        Parameters
        ----------
        message : can.Message
            CAN message

        Returns
        -------
        str
            Message hash
        """
        # Simple hash based on ID and data
        data_hash = hash(bytes(message.data))
        return f"{message.arbitration_id:08X}_{data_hash:016X}"

    def _is_duplicate(self, msg_hash: str) -> bool:
        """Check if message is a duplicate.

        Parameters
        ----------
        msg_hash : str
            Message hash

        Returns
        -------
        bool
            True if message is duplicate
        """
        current_time = datetime.now(UTC)

        # Clean old hashes
        cutoff_time = current_time - timedelta(seconds=self.config.dedup_window_seconds)
        self._message_hashes = {h: t for h, t in self._message_hashes.items() if t > cutoff_time}

        # Check for duplicate
        if msg_hash in self._message_hashes:
            return True

        # Store hash
        self._message_hashes[msg_hash] = current_time
        return False

    async def _drop_lowest_priority(self) -> bool:
        """Drop the lowest priority message from buffer.

        Returns
        -------
        bool
            True if a message was dropped
        """
        # Find lowest priority buffer with messages
        for priority in reversed(list(CANMessagePriority)):
            buffer = self._priority_buffers[priority]
            if buffer:
                buffer.popleft()
                return True
        return False

    def _calculate_sleep_time(self) -> float:
        """Calculate adaptive sleep time for flush loop.

        Returns
        -------
        float
            Sleep time in seconds
        """
        utilization = self.stats.buffer_utilization / 100.0

        # Aggressive flushing when buffer is nearly full
        if utilization > 0.8:
            return 0.1
        elif utilization > 0.5:
            return 0.5
        else:
            return min(self.config.flush_interval / 2, 2.0)

    async def _stats_loop(self) -> None:
        """Background task for statistics updates."""
        while self._running:
            try:
                await self._update_performance_stats()
                await asyncio.sleep(5.0)  # Update every 5 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Stats loop error: {e}")
                await asyncio.sleep(1.0)

    async def _update_performance_stats(self) -> None:
        """Update performance statistics."""
        current_time = datetime.now(UTC)
        time_delta = (current_time - self._last_stats_update).total_seconds()

        if time_delta > 0:
            self.stats.messages_per_second = (
                self.stats.total_received / (current_time - self._start_time).total_seconds()
            )

        # Calculate success rates
        total_processed = self.stats.total_flushed + self.stats.decode_failures
        if total_processed > 0:
            self.stats.decode_success_rate = (
                (total_processed - self.stats.decode_failures) / total_processed * 100
            )

        total_validated = self.stats.total_buffered
        if total_validated > 0:
            self.stats.validation_pass_rate = (
                (total_validated - self.stats.validation_failures) / total_validated * 100
            )

        self._last_stats_update = current_time
