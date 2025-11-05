"""
Enhanced time-series storage with optimized connection pooling and performance.

This module provides improved database integration with advanced connection pooling,
TimescaleDB optimization, and performance monitoring specifically designed for
agricultural robotics high-frequency data operations.

Implementation follows Test-First Development (TDD) GREEN phase.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import Any

import can
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession

from afs_fastapi.core.can_frame_codec import DecodedPGN, DecodedSPN
from afs_fastapi.database.can_message_buffer import BufferedCANMessage
from afs_fastapi.database.can_time_series_schema import (
    CANMessageDecoded,
    CANMessageRaw,
    TimeSeriesBase,
)
from afs_fastapi.database.connection_pool import AgriculturalConnectionPool, PoolConfiguration

# Configure logging for enhanced time-series storage
logger = logging.getLogger(__name__)


class EnhancedTimeSeriesStorage:
    """High-performance time-series storage with advanced connection pooling and optimization.

    This enhanced version provides:
    - Unified connection pooling across all database operations
    - TimescaleDB integration for hypertable optimization
    - Performance monitoring and health checks
    - Automatic failover and recovery
    - Batch optimization for high-frequency agricultural data
    """

    def __init__(self, database_url: str, pool_config: PoolConfiguration | None = None) -> None:
        """Initialize enhanced time-series storage with connection pooling.

        Parameters
        ----------
        database_url : str
            PostgreSQL/TimescaleDB connection URL
        pool_config : Optional[PoolConfiguration], default None
            Connection pool configuration
        """
        self.database_url = database_url
        self.pool_config = pool_config or PoolConfiguration()

        # Initialize unified connection pool
        self.connection_pool: AgriculturalConnectionPool | None = None
        self._initialized = False

        # Performance tracking
        self._performance_metrics = {
            "total_writes": 0,
            "failed_writes": 0,
            "total_reads": 0,
            "failed_reads": 0,
            "batch_operations": 0,
            "avg_write_time": 0.0,
            "avg_read_time": 0.0,
        }

    async def initialize(self) -> bool:
        """Initialize enhanced time-series storage with connection pooling.

        Returns
        -------
        bool
            True if initialization successful
        """
        try:
            # Initialize connection pool
            self.connection_pool = AgriculturalConnectionPool(self.database_url, self.pool_config)

            if not await self.connection_pool.initialize():
                logger.error("Failed to initialize connection pool")
                return False

            # Initialize schema using sync session
            await self._initialize_schema()

            # Setup TimescaleDB features
            if self.pool_config.enable_hypertable:
                await self._setup_timescaledb()

            self._initialized = True
            logger.info("Enhanced time-series storage initialized successfully")

            # Start performance monitoring
            asyncio.create_task(self._performance_monitoring_task())

            return True

        except Exception as e:
            logger.error(f"Failed to initialize enhanced time-series storage: {e}")
            return False

    async def shutdown(self) -> None:
        """Shutdown enhanced time-series storage and connection pool."""
        if self.connection_pool:
            await self.connection_pool.shutdown()

        self._initialized = False
        logger.info("Enhanced time-series storage shut down")

    async def store_messages_batch_optimized(
        self, messages: list[BufferedCANMessage], use_batch_optimization: bool = True
    ) -> bool:
        """Store batch of CAN messages with advanced optimization.

        Parameters
        ----------
        messages : list[BufferedCANMessage]
            Batch of messages to store
        use_batch_optimization : bool, default True
            Enable batch optimization for large writes

        Returns
        -------
        bool
            True if storage was successful
        """
        if not self._initialized or not messages:
            return False

        start_time = time.time()
        self._performance_metrics["total_writes"] += 1

        try:
            if use_batch_optimization and len(messages) >= self.pool_config.batch_size:
                await self._store_optimized_batch(messages)
            else:
                await self._store_standard_batch(messages)

            self._update_write_performance(start_time, False)
            return True

        except Exception as e:
            self._performance_metrics["failed_writes"] += 1
            self._update_write_performance(start_time, True)
            logger.error(f"Failed to store message batch: {e}")
            return False

    async def _store_optimized_batch(self, messages: list[BufferedCANMessage]) -> None:
        """Store messages using batch optimization with connection pooling."""
        self._performance_metrics["batch_operations"] += 1

        # Sort messages by time and equipment for optimal batch processing
        sorted_messages = sorted(
            messages, key=lambda msg: (msg.reception_time, msg.raw_message.arbitration_id)
        )

        # Process in chunks if very large batch
        chunk_size = self.pool_config.max_batch_size
        for i in range(0, len(sorted_messages), chunk_size):
            chunk = sorted_messages[i : i + chunk_size]
            await self._process_batch_chunk(chunk)

    async def _process_batch_chunk(self, messages: list[BufferedCANMessage]) -> None:
        """Process a chunk of messages with optimized batch operations."""
        async with self.connection_pool.get_async_session() as session:
            # Prepare batch records
            raw_records = []
            decoded_records = []

            for msg in messages:
                # Raw message record
                raw_record = CANMessageRaw(
                    timestamp=msg.reception_time,
                    arbitration_id=msg.raw_message.arbitration_id,
                    data=bytes(msg.raw_message.data),
                    dlc=msg.raw_message.dlc,
                    is_extended_id=msg.raw_message.is_extended_id,
                    is_error_frame=msg.raw_message.is_error_frame,
                    is_remote_frame=msg.raw_message.is_remote_frame,
                    interface_id=msg.interface_id,
                    source_address=self._extract_source_address(msg.raw_message),
                    pgn=self._extract_pgn(msg.raw_message),
                    priority=self._extract_priority(msg.raw_message),
                    retention_policy="optimized",
                )
                raw_records.append(raw_record)

                # Decoded message record (if available)
                if msg.decoded_message:
                    decoded_record = CANMessageDecoded(
                        raw_message_id=0,  # Will be set after batch insert
                        timestamp=msg.reception_time,
                        pgn=msg.decoded_message.pgn,
                        pgn_name=msg.decoded_message.name,
                        source_address=msg.decoded_message.source_address,
                        destination_address=msg.decoded_message.destination_address,
                        spn_values=self._serialize_spn_values(msg.decoded_message.spn_values),
                        message_data={
                            "priority": msg.decoded_message.priority,
                            "data_length": msg.decoded_message.data_length,
                            "is_multi_frame": msg.decoded_message.is_multi_frame,
                            "frame_count": msg.decoded_message.frame_count,
                        },
                        decoding_success=True,
                        spn_count=len(msg.decoded_message.spn_values),
                        valid_spn_count=len(
                            [spn for spn in msg.decoded_message.spn_values if spn.is_valid]
                        ),
                        equipment_type=self._detect_equipment_type(msg.decoded_message),
                    )
                    decoded_records.append(decoded_record)

            # Execute optimized batch insert
            await self._execute_batch_insert(session, raw_records, decoded_records)

    async def _execute_batch_insert(
        self,
        session: AsyncSession,
        raw_records: list[CANMessageRaw],
        decoded_records: list[CANMessageDecoded],
    ) -> None:
        """Execute optimized batch insert with proper transaction handling."""
        try:
            # Bulk insert raw messages
            if raw_records:
                session.add_all(raw_records)
                await session.flush()  # Get IDs for decoded records

                # Update decoded records with raw message IDs
                for i, decoded_record in enumerate(decoded_records):
                    if i < len(raw_records):
                        decoded_record.raw_message_id = raw_records[i].id

            # Bulk insert decoded messages
            if decoded_records:
                session.add_all(decoded_records)

            # Commit transaction
            await session.commit()

        except Exception as e:
            await session.rollback()
            logger.error(f"Batch insert failed: {e}")
            raise

    async def _store_standard_batch(self, messages: list[BufferedCANMessage]) -> None:
        """Store messages using standard batch processing."""
        async with self.connection_pool.get_async_session() as session:
            # Prepare records
            raw_records = []
            decoded_records = []

            for msg in messages:
                # Raw message record
                raw_record = CANMessageRaw(
                    timestamp=msg.reception_time,
                    arbitration_id=msg.raw_message.arbitration_id,
                    data=bytes(msg.raw_message.data),
                    dlc=msg.raw_message.dlc,
                    is_extended_id=msg.raw_message.is_extended_id,
                    is_error_frame=msg.raw_message.is_error_frame,
                    is_remote_frame=msg.raw_message.is_remote_frame,
                    interface_id=msg.interface_id,
                    source_address=self._extract_source_address(msg.raw_message),
                    pgn=self._extract_pgn(msg.raw_message),
                    priority=self._extract_priority(msg.raw_message),
                    retention_policy="standard",
                )
                raw_records.append(raw_record)

                # Decoded message record (if available)
                if msg.decoded_message:
                    decoded_record = CANMessageDecoded(
                        raw_message_id=0,
                        timestamp=msg.reception_time,
                        pgn=msg.decoded_message.pgn,
                        pgn_name=msg.decoded_message.name,
                        source_address=msg.decoded_message.source_address,
                        destination_address=msg.decoded_message.destination_address,
                        spn_values=self._serialize_spn_values(msg.decoded_message.spn_values),
                        message_data={
                            "priority": msg.decoded_message.priority,
                            "data_length": msg.decoded_message.data_length,
                            "is_multi_frame": msg.decoded_message.is_multi_frame,
                            "frame_count": msg.decoded_message.frame_count,
                        },
                        decoding_success=True,
                        spn_count=len(msg.decoded_message.spn_values),
                        valid_spn_count=len(
                            [spn for spn in msg.decoded_message.spn_values if spn.is_valid]
                        ),
                        equipment_type=self._detect_equipment_type(msg.decoded_message),
                    )
                    decoded_records.append(decoded_record)

            # Standard batch insert
            if raw_records:
                session.add_all(raw_records)
                await session.flush()

                for i, decoded_record in enumerate(decoded_records):
                    if i < len(raw_records):
                        decoded_record.raw_message_id = raw_records[i].id

            if decoded_records:
                session.add_all(decoded_records)

            await session.commit()

    async def query_agricultural_metrics_optimized(
        self,
        start_time: datetime,
        end_time: datetime,
        equipment_types: list[str] | None = None,
        source_addresses: list[int] | None = None,
        time_window: str = "1hour",
        use_index_hints: bool = True,
    ) -> list[dict[str, Any]]:
        """Query agricultural metrics with optimization.

        Parameters
        ----------
        start_time : datetime
            Start of query period
        end_time : datetime
            End of query period
        equipment_types : Optional[list[str]]
            Filter by equipment types
        source_addresses : Optional[list[int]]
            Filter by source addresses
        time_window : str, default "1hour"
            Aggregation window
        use_index_hints : bool, default True
            Use index hints for better performance

        Returns
        -------
        list[dict[str, Any]]
            Query results
        """
        if not self._initialized:
            return []

        start_time = time.time()
        self._performance_metrics["total_reads"] += 1

        try:
            async with self.connection_pool.get_async_session() as session:
                # Build optimized query with index hints
                base_query = self._build_optimized_query(
                    equipment_types, source_addresses, time_window, use_index_hints
                )

                params = {
                    "start_time": start_time,
                    "end_time": end_time,
                    "time_window": time_window,
                }

                if equipment_types:
                    params["equipment_types"] = equipment_types

                if source_addresses:
                    params["source_addresses"] = source_addresses

                result = await session.execute(text(base_query), params)
                results = [dict(row._mapping) for row in result]

                self._update_read_performance(start_time, False, len(results))
                return results

        except Exception as e:
            self._performance_metrics["failed_reads"] += 1
            self._update_read_performance(start_time, True, 0)
            logger.error(f"Failed to query agricultural metrics: {e}")
            return []

    def _build_optimized_query(
        self,
        equipment_types: list[str] | None,
        source_addresses: list[int] | None,
        time_window: str,
        use_index_hints: bool,
    ) -> str:
        """Build optimized query with index hints."""
        base_query = """
            SELECT * FROM agricultural_metrics
            WHERE timestamp BETWEEN :start_time AND :end_time
                AND time_window = :time_window
        """

        if use_index_hints:
            base_query = """
                SELECT /*+ INDEX_SCAN(idx_metrics_equipment_time_window) */ * 
                FROM agricultural_metrics
                WHERE timestamp BETWEEN :start_time AND :end_time
                    AND time_window = :time_window
            """

        if equipment_types:
            base_query += " AND equipment_type = ANY(:equipment_types)"

        if source_addresses:
            base_query += " AND source_address = ANY(:source_addresses)"

        base_query += " ORDER BY timestamp, source_address"

        return base_query

    def _update_write_performance(self, start_time: float, is_error: bool) -> None:
        """Update write performance metrics."""
        write_time = time.time() - start_time
        self._performance_metrics["avg_write_time"] = (
            self._performance_metrics["avg_write_time"]
            * (self._performance_metrics["total_writes"] - 1)
            + write_time
        ) / self._performance_metrics["total_writes"]

    def _update_read_performance(self, start_time: float, is_error: bool, row_count: int) -> None:
        """Update read performance metrics."""
        read_time = time.time() - start_time
        self._performance_metrics["avg_read_time"] = (
            self._performance_metrics["avg_read_time"]
            * (self._performance_metrics["total_reads"] - 1)
            + read_time
        ) / self._performance_metrics["total_reads"]

    async def _performance_monitoring_task(self) -> None:
        """Background task for performance monitoring."""
        while self._initialized:
            try:
                # Execute health check
                health_status = await self.connection_pool.execute_health_check()
                logger.info(f"Database health status: {health_status}")

                # Log performance metrics
                metrics = self.get_performance_metrics()
                logger.debug(f"Current performance: {metrics}")

                # Wait for monitoring interval
                await asyncio.sleep(self.pool_config.health_check_interval)

            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(self.pool_config.health_check_interval)

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get comprehensive performance metrics."""
        return {
            **self._performance_metrics,
            "pool_status": self.connection_pool.get_pool_status() if self.connection_pool else {},
            "health_check": (
                asyncio.create_task(self.connection_pool.execute_health_check())
                if self.connection_pool
                else None
            ),
        }

    def _extract_pgn(self, message: can.Message) -> int | None:
        """Extract PGN from CAN message."""
        if not message.is_extended_id:
            return None

        pdu_format = (message.arbitration_id >> 16) & 0xFF
        if pdu_format >= 240:
            pdu_specific = (message.arbitration_id >> 8) & 0xFF
            return (pdu_format << 8) | pdu_specific
        else:
            return pdu_format << 8

    def _extract_source_address(self, message: can.Message) -> int | None:
        """Extract source address from CAN message."""
        if message.is_extended_id:
            return (message.arbitration_id >> 8) & 0xFF
        return None

    def _extract_priority(self, message: can.Message) -> int | None:
        """Extract priority from CAN message."""
        if message.is_extended_id:
            return (message.arbitration_id >> 26) & 0x07
        return None

    def _serialize_spn_values(self, spn_values: list[DecodedSPN]) -> dict[str, Any]:
        """Serialize SPN values for JSON storage."""
        result = {}
        for spn in spn_values:
            result[str(spn.spn)] = {
                "name": spn.name,
                "value": spn.value,
                "units": spn.units,
                "raw_value": spn.raw_value,
                "is_valid": spn.is_valid,
                "is_not_available": spn.is_not_available,
                "is_error": spn.is_error,
            }
        return result

    def _detect_equipment_type(self, decoded_msg: DecodedPGN) -> str | None:
        """Detect equipment type from decoded message."""
        # Map source addresses to equipment types
        address_ranges = {
            (0x80, 0x87): "tractor",
            (0x88, 0x8F): "harvester",
            (0x90, 0x97): "sprayer",
            (0x98, 0x9F): "tillage",
        }

        for (start, end), equipment_type in address_ranges.items():
            if start <= decoded_msg.source_address <= end:
                return equipment_type

        return "unknown"

    async def _initialize_schema(self) -> None:
        """Initialize database schema with connection pooling."""
        if self.connection_pool:
            # Convert async URL to sync URL for schema creation
            sync_url = self.database_url
            if "+aiosqlite" in sync_url:
                sync_url = sync_url.replace("+aiosqlite", "")
            elif "+asyncpg" in sync_url:
                sync_url = sync_url.replace("+asyncpg", "")

            sync_engine = create_engine(sync_url)

            with sync_engine.begin() as conn:
                TimeSeriesBase.metadata.create_all(conn)

            sync_engine.dispose()

        logger.info("Database schema initialized with connection pooling")

    async def _setup_timescaledb(self) -> None:
        """Setup TimescaleDB features with connection pooling."""
        # Skip TimescaleDB setup for SQLite (only available with PostgreSQL)
        if "sqlite" in self.database_url.lower():
            logger.info("Skipping TimescaleDB setup for SQLite database")
            return

        logger.info("Setting up TimescaleDB features with connection pooling")
        try:
            async with self.connection_pool.get_async_session() as session:
                # Enable TimescaleDB extension
                await session.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

                # Setup hypertables for time-series data
                await session.execute(
                    """
                    SELECT create_hypertable('can_messages_raw', 'timestamp', 
                                            if_not_exists => true, 
                                            chunk_time_interval => interval '1 day');
                """
                )

                await session.execute(
                    """
                    SELECT create_hypertable('can_messages_decoded', 'timestamp', 
                                            if_not_exists => true, 
                                            chunk_time_interval => interval '1 day');
                """
                )

                await session.execute(
                    """
                    SELECT create_hypertable('agricultural_metrics', 'timestamp', 
                                            if_not_exists => true, 
                                            chunk_time_interval => interval '1 week');
                """
                )

                # Setup compression policies
                await session.execute(
                    """
                    ALTER TABLE can_messages_raw SET (timescaledb.compress = true);
                    ALTER TABLE can_messages_decoded SET (timescaledb.compress = true);
                    ALTER TABLE agricultural_metrics SET (timescaledb.compress = true);
                """
                )

                await session.commit()
                logger.info("TimescaleDB features configured successfully")

        except Exception as e:
            logger.error(f"TimescaleDB setup failed: {e}")
            # Continue without TimescaleDB features
            pass
