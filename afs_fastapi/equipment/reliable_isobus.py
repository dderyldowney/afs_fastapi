"""
Reliable ISOBUS messaging implementation with guaranteed delivery.

This module provides enhanced ISOBUS communication with delivery guarantees,
acknowledgment protocols, and retry mechanisms for agricultural robotics.

Implementation follows Test-First Development (TDD) GREEN phase.
"""

from __future__ import annotations

import heapq
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from afs_fastapi.equipment.farm_tractors import ISOBUSMessage

# Configure logging for agricultural ISOBUS operations
logger = logging.getLogger(__name__)


# Agricultural priority constants for safety-critical operations
class ISOBUSPriority:
    """ISOBUS message priority levels for agricultural operations."""

    EMERGENCY_STOP = 0  # Immediate safety response required
    COLLISION_AVOIDANCE = 1  # Obstacle detection and avoidance
    FIELD_COORDINATION = 2  # Multi-tractor field allocation
    IMPLEMENT_CONTROL = 3  # Tractor-implement communication
    STATUS_UPDATE = 4  # Routine operational status
    DIAGNOSTICS = 5  # Non-critical diagnostic information


@dataclass
class ReliableISOBUSMessage:
    """Enhanced ISOBUS message with guaranteed delivery tracking.

    Extends basic ISOBUS messages with reliability metadata for agricultural
    robotics scenarios where message loss could cause safety violations.
    """

    message_id: str
    base_message: ISOBUSMessage
    requires_ack: bool = True
    max_retries: int = 3
    retry_interval: float = 0.1
    timeout: float = 2.0
    priority: int = 0


class MessageDeliveryTracker:
    """Tracks message delivery status and coordinates retries.

    Manages the lifecycle of reliable messages from transmission through
    acknowledgment or timeout, implementing exponential backoff retry logic.
    """

    def __init__(self, max_pending_messages: int = 1000) -> None:
        """Initialize delivery tracking state with agricultural optimizations.

        Parameters
        ----------
        max_pending_messages : int, default 1000
            Maximum number of pending messages to prevent memory exhaustion
            during high-throughput agricultural operations.
        """
        self._pending_messages: dict[str, ReliableISOBUSMessage] = {}
        self._acknowledgments: set[str] = set()

        # Priority queue for efficient retry scheduling: (retry_time, priority, sequence, message_id)
        self._retry_queue: list[tuple[float, int, int, str]] = []
        self._sequence_counter = 0  # For stable priority queue ordering

        self._retry_counts: dict[str, int] = {}
        self._start_times: dict[str, float] = {}
        self._callbacks: dict[str, Callable[[str, str], None]] = {}

        # Agricultural operation constraints
        self._max_pending_messages = max_pending_messages
        self._last_cleanup_time = time.time()

    def track_message(
        self, message: ReliableISOBUSMessage, callback: Callable[[str, str], None] | None = None
    ) -> None:
        """Begin tracking a message for delivery confirmation.

        Parameters
        ----------
        message : ReliableISOBUSMessage
            Message to track for guaranteed delivery.
        callback : callable, optional
            Called when delivery is confirmed or fails.

        Raises
        ------
        ValueError
            If message tracking limits exceeded or invalid message provided.
        """
        # Validate message and enforce agricultural operation limits
        if not message.message_id:
            raise ValueError("Message must have a valid message_id")

        if len(self._pending_messages) >= self._max_pending_messages:
            logger.warning(
                f"Maximum pending messages ({self._max_pending_messages}) reached. "
                "Cleaning up expired messages."
            )
            self._cleanup_expired_messages()

            # Check again after cleanup
            if len(self._pending_messages) >= self._max_pending_messages:
                raise ValueError(
                    f"Cannot track message: maximum pending messages "
                    f"({self._max_pending_messages}) exceeded"
                )

        # Store message tracking data
        self._pending_messages[message.message_id] = message
        self._retry_counts[message.message_id] = 0
        self._start_times[message.message_id] = time.time()

        # Store callback if provided
        if callback:
            self._callbacks[message.message_id] = callback

        # Schedule first retry using priority queue if acknowledgment is required
        if message.requires_ack:
            retry_time = time.time() + message.retry_interval
            self._sequence_counter += 1

            # Use priority queue with agricultural priority levels
            heapq.heappush(
                self._retry_queue,
                (retry_time, message.priority, self._sequence_counter, message.message_id),
            )

            logger.debug(
                f"Tracking message {message.message_id} with priority {message.priority}, "
                f"first retry at {retry_time:.2f}"
            )

    def handle_acknowledgment(self, message_id: str) -> bool:
        """Process received acknowledgment with agricultural logging.

        Parameters
        ----------
        message_id : str
            Identifier of acknowledged message.

        Returns
        -------
        bool
            True if acknowledgment was for a pending message.
        """
        if not message_id:
            logger.warning("Received acknowledgment with empty message_id")
            return False

        if message_id in self._pending_messages:
            message = self._pending_messages[message_id]

            # Remove from pending and add to acknowledgments
            del self._pending_messages[message_id]
            self._acknowledgments.add(message_id)

            # Note: Priority queue cleanup happens naturally during process_retries()
            # as stale entries are filtered out when processed

            # Call delivery callback if present
            if message_id in self._callbacks:
                callback = self._callbacks.pop(message_id)
                try:
                    callback(message_id, "delivered")
                except Exception as e:
                    logger.error(f"Error in delivery callback for {message_id}: {e}")

            # Cleanup tracking data
            self._retry_counts.pop(message_id, None)
            self._start_times.pop(message_id, None)

            logger.debug(f"Acknowledged message {message_id} with priority {message.priority}")
            return True

        logger.debug(f"Received acknowledgment for unknown message: {message_id}")
        return False

    def process_retries(self) -> list[ReliableISOBUSMessage]:
        """Return messages that need to be retried using priority queue.

        Returns
        -------
        list[ReliableISOBUSMessage]
            Messages ready for retry transmission, ordered by agricultural priority.
        """
        current_time = time.time()
        retries = []
        temp_queue: list[tuple[float, int, int, str]] = []

        # Process all entries that are ready for retry
        while self._retry_queue:
            retry_time, priority, sequence, message_id = heapq.heappop(self._retry_queue)

            if retry_time <= current_time:
                # Check if message is still pending (not acknowledged)
                if message_id in self._pending_messages:
                    message = self._pending_messages[message_id]
                    retry_count = self._retry_counts.get(message_id, 0)

                    if retry_count < message.max_retries:
                        retries.append(message)

                        # Schedule next retry with exponential backoff
                        self._retry_counts[message_id] = retry_count + 1
                        next_interval = message.retry_interval * (2**retry_count)
                        next_retry_time = current_time + next_interval
                        self._sequence_counter += 1

                        # Re-queue for next retry
                        heapq.heappush(
                            temp_queue,
                            (next_retry_time, priority, self._sequence_counter, message_id),
                        )

                        logger.debug(
                            f"Retrying message {message_id} (attempt {retry_count + 1}, "
                            f"next retry at {next_retry_time:.2f})"
                        )
                    else:
                        # Max retries exceeded - call failure callback and cleanup
                        logger.warning(
                            f"Message {message_id} exceeded max retries ({message.max_retries})"
                        )

                        if message_id in self._callbacks:
                            callback = self._callbacks.pop(message_id)
                            try:
                                callback(message_id, "failed")
                            except Exception as e:
                                logger.error(f"Error in failure callback for {message_id}: {e}")

                        # Cleanup
                        del self._pending_messages[message_id]
                        self._retry_counts.pop(message_id, None)
                        self._start_times.pop(message_id, None)
                # else: Message was acknowledged, silently discard
            else:
                # Not yet time for retry - put back in queue
                heapq.heappush(temp_queue, (retry_time, priority, sequence, message_id))
                # Put back all remaining entries since they're time-ordered
                while self._retry_queue:
                    heapq.heappush(temp_queue, heapq.heappop(self._retry_queue))
                break

        # Restore the queue with unprocessed entries
        self._retry_queue = temp_queue

        # Periodic cleanup every 60 seconds
        if current_time - self._last_cleanup_time > 60:
            self._cleanup_expired_messages()
            self._last_cleanup_time = current_time

        return retries

    def cleanup_timed_out_messages(self) -> list[str]:
        """Remove and return messages that have timed out.

        Returns
        -------
        list[str]
            Message IDs that have exceeded their timeout period.
        """
        return self._cleanup_expired_messages()

    def _cleanup_expired_messages(self) -> list[str]:
        """Internal method to clean up expired messages.

        Returns
        -------
        list[str]
            Message IDs that were cleaned up.
        """
        current_time = time.time()
        timed_out = []

        # Check all pending messages for timeout
        for message_id, message in list(self._pending_messages.items()):
            start_time = self._start_times.get(message_id, current_time)
            if current_time - start_time > message.timeout:
                timed_out.append(message_id)

                logger.warning(
                    f"Message {message_id} timed out after {message.timeout}s "
                    f"(priority {message.priority})"
                )

                # Call failure callback if present
                if message_id in self._callbacks:
                    callback = self._callbacks.pop(message_id)
                    try:
                        callback(message_id, "timeout")
                    except Exception as e:
                        logger.error(f"Error in timeout callback for {message_id}: {e}")

                # Cleanup all tracking data
                del self._pending_messages[message_id]
                self._retry_counts.pop(message_id, None)
                self._start_times.pop(message_id, None)

        # Note: Priority queue cleanup happens naturally during process_retries()
        # as expired entries are filtered out when processed

        # Cleanup acknowledgments set periodically to prevent unbounded growth
        if len(self._acknowledgments) > 10000:
            # Keep only recent acknowledgments
            self._acknowledgments = set(list(self._acknowledgments)[-5000:])
            logger.info("Cleaned up old acknowledgments to prevent memory growth")

        if timed_out:
            logger.info(f"Cleaned up {len(timed_out)} timed out messages")

        return timed_out

    def get_stats(self) -> dict[str, int]:
        """Get delivery tracker statistics for agricultural monitoring.

        Returns
        -------
        dict[str, int]
            Statistics including pending messages, retry queue size, etc.
        """
        return {
            "pending_messages": len(self._pending_messages),
            "retry_queue_size": len(self._retry_queue),
            "acknowledgments_count": len(self._acknowledgments),
            "active_callbacks": len(self._callbacks),
        }


class ReliableISOBUSDevice:
    """Enhanced ISOBUS device with guaranteed delivery capabilities.

    Extends basic ISOBUS communication with reliability protocols for
    agricultural robotics scenarios requiring confirmed message delivery.
    """

    def __init__(self, device_address: int) -> None:
        """Initialize reliable ISOBUS device.

        Parameters
        ----------
        device_address : int
            ISOBUS address for this device (0x00-0xFF).
        """
        self.device_address = device_address
        self.delivery_tracker = MessageDeliveryTracker()
        self._outbound_queue: list[ReliableISOBUSMessage] = []
        self._inbound_queue: list[ReliableISOBUSMessage] = []
        self._received_message_ids: set[str] = set()

    def send_reliable_message(
        self,
        message: ISOBUSMessage,
        delivery_callback: Callable[[str, str], None] | None = None,
        requires_ack: bool = True,
        max_retries: int = 3,
        retry_interval: float = 0.1,
        timeout: float = 2.0,
        priority: int = 0,
    ) -> str:
        """Send message with delivery guarantee.

        Parameters
        ----------
        message : ISOBUSMessage
            Base ISOBUS message to send.
        delivery_callback : callable, optional
            Called when delivery is confirmed or fails.
        requires_ack : bool, default True
            Whether acknowledgment is required.
        max_retries : int, default 3
            Maximum retry attempts.
        retry_interval : float, default 0.1
            Initial retry interval in seconds.
        timeout : float, default 2.0
            Total timeout for delivery.
        priority : int, default 0
            Message priority (0 = highest).

        Returns
        -------
        str
            Unique message identifier for tracking.
        """
        message_id = str(uuid.uuid4())

        reliable_msg = ReliableISOBUSMessage(
            message_id=message_id,
            base_message=message,
            requires_ack=requires_ack,
            max_retries=max_retries,
            retry_interval=retry_interval,
            timeout=timeout,
            priority=priority,
        )

        # Add to outbound queue
        self._outbound_queue.append(reliable_msg)

        # Track for delivery if acknowledgment required
        if requires_ack:
            self.delivery_tracker.track_message(reliable_msg, delivery_callback)

        return message_id

    def receive_reliable_message(self, message: ReliableISOBUSMessage) -> bool:
        """Receive message and send acknowledgment if required.

        Parameters
        ----------
        message : ReliableISOBUSMessage
            Incoming reliable message.

        Returns
        -------
        bool
            True if acknowledgment was sent.
        """
        # Check for duplicate message
        if message.message_id in self._received_message_ids:
            # Duplicate - still send ack but don't reprocess
            if message.requires_ack:
                self._queue_acknowledgment(message.message_id, message.base_message.source_address)
                return True
            return False

        # New message - add to received set
        self._received_message_ids.add(message.message_id)
        self._inbound_queue.append(message)

        # Send acknowledgment if required
        if message.requires_ack:
            self._queue_acknowledgment(message.message_id, message.base_message.source_address)
            return True

        return False

    def _queue_acknowledgment(self, message_id: str, destination_address: int) -> None:
        """Queue acknowledgment message for transmission.

        Parameters
        ----------
        message_id : str
            ID of message to acknowledge.
        destination_address : int
            Address to send acknowledgment to.
        """
        from datetime import datetime

        ack_message = ISOBUSMessage(
            pgn=0xE800,  # ACK PGN
            source_address=self.device_address,
            destination_address=destination_address,
            data=message_id.encode(),
            timestamp=datetime.now(),
        )

        # Create reliable message for ack (no ack required for acks)
        ack_reliable = ReliableISOBUSMessage(
            message_id=f"ACK_{message_id}",
            base_message=ack_message,
            requires_ack=False,
        )

        self._outbound_queue.append(ack_reliable)

    def process_acknowledgment(self, ack_message: ISOBUSMessage) -> bool:
        """Process received acknowledgment message.

        Parameters
        ----------
        ack_message : ISOBUSMessage
            Acknowledgment message received.

        Returns
        -------
        bool
            True if acknowledgment was processed successfully.
        """
        if ack_message.pgn != 0xE800:
            return False

        try:
            message_id = ack_message.data.decode()
            return self.delivery_tracker.handle_acknowledgment(message_id)
        except UnicodeDecodeError:
            return False

    async def start(self) -> None:
        """Start the ISOBUS device for fleet coordination."""
        logger.info(f"Starting ISOBUS device at address {self.device_address}")
        # Initialize device state for agricultural operations

    async def stop(self) -> None:
        """Stop the ISOBUS device gracefully."""
        logger.info(f"Stopping ISOBUS device at address {self.device_address}")
        # Clean up device state

    async def broadcast_message(self, message: dict[str, Any]) -> None:
        """Broadcast message to fleet via ISOBUS.

        Parameters
        ----------
        message : dict
            Message data to broadcast to fleet
        """
        from datetime import datetime

        # Convert message dict to ISOBUS format
        isobus_msg = ISOBUSMessage(
            pgn=0xE000,  # Fleet coordination PGN
            source_address=self.device_address,
            destination_address=0xFF,  # Broadcast
            data=str(message).encode(),
            timestamp=datetime.now(),
        )

        # Send as reliable message
        self.send_reliable_message(
            isobus_msg,
            priority=ISOBUSPriority.FIELD_COORDINATION,
            requires_ack=False,  # Broadcast doesn't require individual acks
        )

    async def broadcast_priority_message(self, message: dict[str, Any]) -> None:
        """Broadcast high-priority message to fleet via ISOBUS.

        Parameters
        ----------
        message : dict
            High-priority message data (e.g., emergency stop)
        """
        from datetime import datetime

        # Convert message dict to ISOBUS format
        isobus_msg = ISOBUSMessage(
            pgn=0xE001,  # Emergency broadcast PGN
            source_address=self.device_address,
            destination_address=0xFF,  # Broadcast
            data=str(message).encode(),
            timestamp=datetime.now(),
        )

        # Send as high-priority reliable message
        self.send_reliable_message(
            isobus_msg,
            priority=ISOBUSPriority.EMERGENCY_STOP,
            requires_ack=True,  # Emergency messages require acknowledgment
            max_retries=5,  # More retries for safety-critical messages
            timeout=5.0,  # Longer timeout for emergency messages
        )

    async def send_message(self, target_address: int, message: dict[str, Any]) -> None:
        """Send message to specific ISOBUS address.

        Parameters
        ----------
        target_address : int
            Destination ISOBUS address
        message : dict
            Message data to send
        """
        from datetime import datetime

        # Convert message dict to ISOBUS format
        isobus_msg = ISOBUSMessage(
            pgn=0xE002,  # Direct message PGN
            source_address=self.device_address,
            destination_address=target_address,
            data=str(message).encode(),
            timestamp=datetime.now(),
        )

        # Send as reliable message with acknowledgment
        self.send_reliable_message(
            isobus_msg, priority=ISOBUSPriority.FIELD_COORDINATION, requires_ack=True
        )
