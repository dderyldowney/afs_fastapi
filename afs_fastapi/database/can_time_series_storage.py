"""
Database integration layer for CAN time-series data storage and management.

This module provides high-performance database operations for storing CAN messages
in time-series format, with optimizations for agricultural equipment data patterns
and analytical workloads.

Implementation follows Test-First Development (TDD) GREEN phase.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any

import can
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from afs_fastapi.core.can_frame_codec import DecodedPGN, DecodedSPN
from afs_fastapi.database.can_message_buffer import BufferedCANMessage
from afs_fastapi.database.can_time_series_schema import (
    AgriculturalMetrics,
    CANMessageDecoded,
    CANMessageRaw,
    CANNetworkHealth,
    TimeSeriesBase,
)

# Configure logging for time-series storage
logger = logging.getLogger(__name__)


class TimeSeriesStorageConfig:
    """Configuration for time-series database storage."""

    def __init__(
        self,
        database_url: str,
        max_connections: int = 20,
        min_connections: int = 5,
        connection_timeout: float = 30.0,
        enable_timescaledb: bool = True,
        enable_compression: bool = True,
        batch_size: int = 1000,
        max_batch_size: int = 5000,
        write_timeout: float = 60.0,
    ) -> None:
        """Initialize time-series storage configuration.

        Parameters
        ----------
        database_url : str
            PostgreSQL/TimescaleDB connection URL
        max_connections : int, default 20
            Maximum database connections
        min_connections : int, default 5
            Minimum database connections
        connection_timeout : float, default 30.0
            Connection timeout in seconds
        enable_timescaledb : bool, default True
            Enable TimescaleDB hypertables
        enable_compression : bool, default True
            Enable compression for older data
        batch_size : int, default 1000
            Preferred batch size for writes
        max_batch_size : int, default 5000
            Maximum batch size for writes
        write_timeout : float, default 60.0
            Write operation timeout in seconds
        """
        self.database_url = database_url
        self.max_connections = max_connections
        self.min_connections = min_connections
        self.connection_timeout = connection_timeout
        self.enable_timescaledb = enable_timescaledb
        self.enable_compression = enable_compression
        self.batch_size = batch_size
        self.max_batch_size = max_batch_size
        self.write_timeout = write_timeout


class CANTimeSeriesStorage:
    """High-performance time-series storage for CAN messages."""

    def __init__(self, config: TimeSeriesStorageConfig) -> None:
        """Initialize time-series storage.

        Parameters
        ----------
        config : TimeSeriesStorageConfig
            Storage configuration
        """
        self.config = config
        self._async_engine: AsyncEngine | None = None
        self._sync_engine: Engine | None = None
        self._async_session_factory: async_sessionmaker[AsyncSession] | None = None
        self._sync_session_factory: sessionmaker[Session] | None = None
        self._connection_pool = None
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize database connections and tables.

        Returns
        -------
        bool
            True if initialization successful
        """
        try:
            # Create async engine for high-performance operations
            self._async_engine = create_async_engine(
                self.config.database_url,
                pool_size=self.config.max_connections,
                max_overflow=0,
                pool_timeout=self.config.connection_timeout,
                echo=False,  # Set to True for SQL debugging
            )

            # Create sync engine for schema operations
            sync_url = self.config.database_url.replace("+asyncpg", "")
            self._sync_engine = create_engine(sync_url)

            # Create session factories
            self._async_session_factory = async_sessionmaker(
                self._async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            self._sync_session_factory = sessionmaker(
                self._sync_engine,
                expire_on_commit=False,
            )

            assert self._sync_engine is not None  # Assert for mypy
            # Initialize database schema
            await self._initialize_schema()

            # Setup TimescaleDB features
            if self.config.enable_timescaledb:
                await self._setup_timescaledb()  # type: ignore

            self._initialized = True
            logger.info("Time-series storage initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize time-series storage: {e}")
            return False

    async def shutdown(self) -> None:
        """Shutdown database connections."""
        if self._async_engine:
            await self._async_engine.dispose()
        if self._sync_engine:
            self._sync_engine.dispose()

        self._initialized = False
        logger.info("Time-series storage shut down")

    async def store_messages_batch(self, messages: list[BufferedCANMessage]) -> bool:
        """Store a batch of CAN messages to time-series tables.

        Parameters
        ----------
        messages : list[BufferedCANMessage]
            Batch of messages to store

        Returns
        -------
        bool
            True if storage was successful
        """
        if not self._initialized or not messages:
            return False

        try:
            async with self._get_async_session() as session:
                # Prepare raw message records
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
                        source_address=self._extract_source_address(msg.raw_message),  # type: ignore
                        pgn=self._extract_pgn(msg.raw_message),
                        priority=self._extract_priority(msg.raw_message),
                        retention_policy=msg.retention_policy,
                    )
                    raw_records.append(raw_record)

                    # Decoded message record (if available)
                    if msg.decoded_message:
                        decoded_record = CANMessageDecoded(
                            raw_message_id=0,  # Will be set after raw insert
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

                logger.debug(
                    f"Stored {len(raw_records)} raw and {len(decoded_records)} decoded messages"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to store message batch: {e}")
            return False

    async def compute_agricultural_metrics(
        self,
        start_time: datetime,
        end_time: datetime,
        time_window: str = "1hour",
    ) -> bool:
        """Compute and store agricultural metrics for a time period.

        Parameters
        ----------
        start_time : datetime
            Start of time period
        end_time : datetime
            End of time period
        time_window : str, default "1hour"
            Aggregation window (1min, 5min, 1hour, 1day)

        Returns
        -------
        bool
            True if computation was successful
        """
        try:
            async with self._get_async_session() as session:
                # Query for raw agricultural data
                query = text(
                    """
                    SELECT
                        source_address,
                        date_trunc(:window, timestamp) as window_start,
                        count(*) as message_count,
                        avg(CASE WHEN pgn = 61444 AND (data[3] << 8 | data[2]) != 65535
                            THEN (data[3] << 8 | data[2]) * 0.125 END) as avg_engine_rpm,
                        max(CASE WHEN pgn = 61444 AND (data[3] << 8 | data[2]) != 65535
                            THEN (data[3] << 8 | data[2]) * 0.125 END) as max_engine_rpm,
                        avg(CASE WHEN pgn = 65265 AND (data[2] << 8 | data[1]) != 65535
                            THEN (data[2] << 8 | data[1]) * 0.00390625 END) as avg_speed,
                        max(CASE WHEN pgn = 65265 AND (data[2] << 8 | data[1]) != 65535
                            THEN (data[2] << 8 | data[1]) * 0.00390625 END) as max_speed
                    FROM can_messages_raw
                    WHERE timestamp BETWEEN :start_time AND :end_time
                        AND pgn IN (61444, 65265, 65266, 65267)  -- Key agricultural PGNs
                    GROUP BY source_address, window_start
                    ORDER BY source_address, window_start
                """
                )

                result = await session.execute(
                    query,
                    {
                        "window": time_window,
                        "start_time": start_time,
                        "end_time": end_time,
                    },
                )

                metrics_records = []
                for row in result:
                    metric_record = AgriculturalMetrics(
                        timestamp=row.window_start,
                        time_window=time_window,
                        source_address=row.source_address,
                        equipment_type=self._map_address_to_equipment_type(row.source_address),
                        engine_rpm_avg=row.avg_engine_rpm,
                        engine_rpm_max=row.max_engine_rpm,
                        avg_speed=row.avg_speed,
                        max_speed=row.max_speed,
                        message_count=row.message_count,
                        data_quality_score=self._calculate_data_quality(row.message_count),  # type: ignore
                    )
                    metrics_records.append(metric_record)

                # Store computed metrics
                if metrics_records:
                    session.add_all(metrics_records)
                    await session.commit()

                logger.info(
                    f"Computed {len(metrics_records)} metric records for {time_window} window"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to compute agricultural metrics: {e}")
            return False

    async def update_network_health(self, interface_id: str, time_window: str = "5min") -> bool:
        """Update network health metrics for an interface.

        Parameters
        ----------
        interface_id : str
            CAN interface identifier
        time_window : str, default "5min"
            Health monitoring window

        Returns
        -------
        bool
            True if update was successful
        """
        try:
            async with self._get_async_session() as session:
                current_time = datetime.now(UTC)
                window_start = current_time.replace(
                    minute=(current_time.minute // 5) * 5, second=0, microsecond=0
                )

                # Query network statistics
                query = text(
                    """
                    SELECT
                        COUNT(*) as total_messages,
                        COUNT(DISTINCT source_address) as unique_sources,
                        COUNT(DISTINCT pgn) as unique_pgns,
                        SUM(CASE WHEN is_error_frame THEN 1 ELSE 0 END) as error_frames,
                        AVG(EXTRACT(EPOCH FROM (ingestion_time - timestamp))) as avg_latency
                    FROM can_messages_raw
                    WHERE interface_id = :interface_id
                        AND timestamp >= :window_start
                        AND timestamp < :window_end
                """
                )

                result = await session.execute(
                    query,
                    {
                        "interface_id": interface_id,
                        "window_start": window_start,
                        "window_end": window_start + timedelta(minutes=5),
                    },
                )

                row = result.first()
                if row:
                    # Calculate derived metrics
                    messages_per_second = row.total_messages / 300.0  # 5 minutes = 300 seconds
                    error_rate = (row.error_frames / max(row.total_messages, 1)) * 100
                    health_score = max(0.0, 1.0 - (error_rate / 100.0))

                    # Create health record
                    health_record = CANNetworkHealth(
                        timestamp=window_start,
                        time_window=time_window,
                        interface_id=interface_id,
                        total_messages=row.total_messages,
                        messages_per_second=messages_per_second,
                        unique_source_count=row.unique_sources,
                        unique_pgn_count=row.unique_pgns,
                        error_frames=row.error_frames,
                        error_rate=error_rate,
                        overall_health_score=health_score,
                        latency_avg=row.avg_latency,
                        device_count=row.unique_sources,
                    )

                    session.add(health_record)
                    await session.commit()

                    logger.debug(f"Updated network health for {interface_id}: {health_score:.2f}")
                    return True
                else:
                    logger.warning(
                        f"No network health data found for {interface_id} in the last 5 minutes."
                    )
                    return False

        except Exception as e:
            logger.error(f"Failed to update network health: {e}")
            return False

    async def query_metrics(
        self,
        start_time: datetime,
        end_time: datetime,
        equipment_types: list[str] | None = None,
        source_addresses: list[int] | None = None,
        time_window: str = "1hour",
    ) -> list[dict[str, Any]]:
        """Query agricultural metrics for analysis.

        Parameters
        ----------
        start_time : datetime
            Start of query period
        end_time : datetime
            End of query period
        equipment_types : list[str | None]
            Filter by equipment types
        source_addresses : list[int | None]
            Filter by source addresses
        time_window : str, default "1hour"
            Aggregation window

        Returns
        -------
        list[dict[str, Any]]
            Query results
        """
        try:
            async with self._get_async_session() as session:
                base_query = """
                    SELECT * FROM agricultural_metrics
                    WHERE timestamp BETWEEN :start_time AND :end_time
                        AND time_window = :time_window
                """

                params = {
                    "start_time": start_time,
                    "end_time": end_time,
                    "time_window": time_window,
                }

                if equipment_types:
                    base_query += " AND equipment_type = ANY(:equipment_types)"
                    params["equipment_types"] = equipment_types

                if source_addresses:
                    base_query += " AND source_address = ANY(:source_addresses)"
                    params["source_addresses"] = source_addresses

                base_query += " ORDER BY timestamp, source_address"

                result = await session.execute(text(base_query), params)
                return [dict(row._mapping) for row in result]

        except Exception as e:
            logger.error(f"Failed to query metrics: {e}")
            return []

    @asynccontextmanager
    async def _get_async_session(self) -> AsyncGenerator[AsyncSession, None]:  # type: ignore
        """Get an async database session.

        Yields
        ------
        AsyncSession
            Database session
        """
        assert self._async_session_factory is not None  # Assert for mypy
        async with self._async_session_factory() as session:
            try:
                yield session  # type: ignore
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    def _extract_pgn(self, message: can.Message) -> int | None:  # type: ignore
        """Extract PGN from CAN message."""
        if not message.is_extended_id:
            return None

        pdu_format = (message.arbitration_id >> 16) & 0xFF
        if pdu_format >= 240:
            pdu_specific = (message.arbitration_id >> 8) & 0xFF
            return (pdu_format << 8) | pdu_specific
        else:
            return pdu_format << 8

    async def _initialize_schema(self) -> None:
        """Initialize database schema and tables."""
        if self._sync_engine:
            assert self._sync_engine is not None  # Assert for mypy
            with self._sync_engine.begin() as conn:
                TimeSeriesBase.metadata.create_all(conn)

        logger.info("Database schema initialized")

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
        # Map source addresses to equipment types (simplified)
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

    def _map_address_to_equipment_type(self, source_address: int) -> str:
        """Map source address to equipment type."""
        address_ranges = {
            (0x80, 0x87): "tractor",
            (0x88, 0x8F): "harvester",
            (0x90, 0x97): "sprayer",
            (0x98, 0x9F): "tillage",
        }

        for (start, end), equipment_type in address_ranges.items():
            if start <= source_address <= end:
                return equipment_type

        return "unknown"

    def _calculate_data_quality(self, message_count: int) -> float:
        """Calculate data quality score based on message frequency."""
        # Expected messages per hour for normal operation
        expected_messages = 3600  # 1 per second
        ratio = min(message_count / expected_messages, 1.0)
        return ratio

    async def _setup_timescaledb(self) -> None:
        """Setup TimescaleDB specific features like hypertables and compression policies."""
        logger.info("Setting up TimescaleDB features (placeholder)")
        # Placeholder for actual TimescaleDB setup logic
        pass
