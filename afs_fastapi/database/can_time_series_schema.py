"""
Time-series database schema for CAN message storage and analysis.

This module defines the database schema optimized for high-throughput CAN message
storage, providing efficient indexing for time-based queries and agricultural
equipment analytics.

Implementation follows Test-First Development (TDD) GREEN phase.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from enum import Enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TEXT, TypeDecorator


class TimeSeriesBase(DeclarativeBase):
    """Base class for all time-series SQLAlchemy models using SQLAlchemy 2.0 API."""

    pass


class SQLiteJSON(TypeDecorator):
    """SQLite-compatible JSON type decorator.

    Uses TEXT storage for SQLite and JSONB for PostgreSQL.
    """

    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return self.impl


class CANMessagePriority(Enum):
    """CAN message priority levels for storage optimization."""

    CRITICAL = 0  # Emergency, safety - always store
    HIGH = 1  # Engine, transmission - store frequently
    NORMAL = 2  # Standard telemetry - store normally
    LOW = 3  # Diagnostics - store less frequently


class CANMessageRaw(TimeSeriesBase):  # type: ignore
    """Raw CAN message storage for complete message history.

    Optimized for high-throughput write operations with minimal processing.
    """

    __tablename__ = "can_messages_raw"

    # Primary key and timestamp
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # CAN message components
    arbitration_id = Column(Integer, nullable=False, index=True)
    data = Column(LargeBinary(8), nullable=False)  # CAN data (max 8 bytes)
    dlc = Column(Integer, nullable=False)  # Data Length Code
    is_extended_id = Column(Boolean, nullable=False, default=True)
    is_error_frame = Column(Boolean, nullable=False, default=False)
    is_remote_frame = Column(Boolean, nullable=False, default=False)

    # Source information
    interface_id = Column(String(50), nullable=False, index=True)
    source_address = Column(Integer, nullable=True, index=True)  # Extracted from CAN ID

    # Message classification
    pgn = Column(Integer, nullable=True, index=True)  # Parameter Group Number
    priority = Column(Integer, nullable=True)  # Message priority (0-7)

    # Storage metadata
    ingestion_time = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    retention_policy = Column(String(20), nullable=False, default="standard")

    # Indexes for time-series queries
    __table_args__ = (
        Index("idx_can_raw_timestamp_pgn", "timestamp", "pgn"),
        Index("idx_can_raw_interface_time", "interface_id", "timestamp"),
        Index("idx_can_raw_source_time", "source_address", "timestamp"),
        Index("idx_can_raw_arbitration_time", "arbitration_id", "timestamp"),
    )


class CANMessageDecoded(TimeSeriesBase):  # type: ignore
    """Decoded CAN message storage with parsed SPN values.

    Stores human-readable values for analytics and monitoring.
    """

    __tablename__ = "can_messages_decoded"

    # Primary key and references
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    raw_message_id = Column(BigInteger, nullable=False, index=True)

    # Timestamp information
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    ingestion_time = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    # Message identification
    pgn = Column(Integer, nullable=False, index=True)
    pgn_name = Column(String(100), nullable=False)
    source_address = Column(Integer, nullable=False, index=True)
    destination_address = Column(Integer, nullable=True)

    # Decoded data (JSON for flexible SPN storage)
    spn_values = Column(SQLiteJSON, nullable=False)  # {spn_number: {value, units, is_valid}}
    message_data = Column(SQLiteJSON, nullable=True)  # Additional message metadata

    # Data quality indicators
    decoding_success = Column(Boolean, nullable=False, default=True)
    spn_count = Column(Integer, nullable=False, default=0)
    valid_spn_count = Column(Integer, nullable=False, default=0)

    # Agricultural context
    equipment_type = Column(String(50), nullable=True, index=True)  # tractor, harvester, etc.
    operation_context = Column(String(100), nullable=True)  # field_work, transport, etc.

    # Indexes for analytical queries
    __table_args__ = (
        Index("idx_can_decoded_timestamp_pgn", "timestamp", "pgn"),
        Index("idx_can_decoded_equipment_time", "equipment_type", "timestamp"),
        Index("idx_can_decoded_source_pgn_time", "source_address", "pgn", "timestamp"),
    )


class AgriculturalMetrics(TimeSeriesBase):  # type: ignore
    """Aggregated agricultural metrics derived from CAN data.

    Pre-computed metrics for dashboard and analytics performance.
    """

    __tablename__ = "agricultural_metrics"

    # Primary key and time window
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    time_window = Column(String(20), nullable=False)  # 1min, 5min, 1hour, 1day

    # Equipment identification
    source_address = Column(Integer, nullable=False, index=True)
    equipment_type = Column(String(50), nullable=False, index=True)
    equipment_id = Column(String(100), nullable=True)

    # Engine metrics
    engine_rpm_avg = Column(Float, nullable=True)
    engine_rpm_max = Column(Float, nullable=True)
    engine_load_avg = Column(Float, nullable=True)
    fuel_consumption_total = Column(Float, nullable=True)  # liters
    fuel_rate_avg = Column(Float, nullable=True)  # L/h

    # Position and movement
    distance_traveled = Column(Float, nullable=True)  # meters
    avg_speed = Column(Float, nullable=True)  # km/h
    max_speed = Column(Float, nullable=True)  # km/h
    working_time = Column(Float, nullable=True)  # hours
    idle_time = Column(Float, nullable=True)  # hours

    # Field operation metrics
    area_covered = Column(Float, nullable=True)  # hectares
    field_efficiency = Column(Float, nullable=True)  # percentage
    operation_type = Column(String(100), nullable=True)

    # Quality indicators
    message_count = Column(Integer, nullable=False, default=0)
    data_quality_score = Column(Float, nullable=True)  # 0-1
    uptime_percentage = Column(Float, nullable=True)

    # Computed timestamp
    computation_time = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    # Indexes for dashboard queries
    __table_args__ = (
        Index("idx_metrics_equipment_time_window", "equipment_type", "timestamp", "time_window"),
        Index("idx_metrics_source_time_window", "source_address", "timestamp", "time_window"),
        UniqueConstraint(
            "timestamp", "time_window", "source_address", name="uq_metrics_time_source"
        ),
    )


class CANNetworkHealth(TimeSeriesBase):  # type: ignore
    """CAN network health monitoring and diagnostics.

    Tracks network performance, error rates, and system health.
    """

    __tablename__ = "can_network_health"

    # Primary key and timestamp
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    time_window = Column(String(20), nullable=False)  # monitoring interval

    # Network identification
    interface_id = Column(String(50), nullable=False, index=True)
    network_name = Column(String(100), nullable=True)

    # Message statistics
    total_messages = Column(BigInteger, nullable=False, default=0)
    messages_per_second = Column(Float, nullable=False, default=0.0)
    unique_source_count = Column(Integer, nullable=False, default=0)
    unique_pgn_count = Column(Integer, nullable=False, default=0)

    # Error statistics
    error_frames = Column(Integer, nullable=False, default=0)
    malformed_messages = Column(Integer, nullable=False, default=0)
    decoding_failures = Column(Integer, nullable=False, default=0)
    error_rate = Column(Float, nullable=False, default=0.0)  # percentage

    # Bus utilization
    bus_load_percentage = Column(Float, nullable=True)
    peak_utilization = Column(Float, nullable=True)
    bandwidth_utilization = Column(Float, nullable=True)  # bps

    # Network topology
    active_devices = Column(SQLiteJSON, nullable=True)  # {address: {last_seen, message_count}}
    device_count = Column(Integer, nullable=False, default=0)
    new_devices = Column(SQLiteJSON, nullable=True)  # devices seen for first time
    offline_devices = Column(SQLiteJSON, nullable=True)  # devices not seen recently

    # Health indicators
    overall_health_score = Column(Float, nullable=False, default=1.0)  # 0-1
    latency_avg = Column(Float, nullable=True)  # ms
    latency_max = Column(Float, nullable=True)  # ms

    # Alert status
    active_alerts = Column(SQLiteJSON, nullable=True)  # current system alerts
    alert_count = Column(Integer, nullable=False, default=0)

    # Indexes for monitoring queries
    __table_args__ = (
        Index("idx_network_health_interface_time", "interface_id", "timestamp"),
        Index("idx_network_health_time_window", "timestamp", "time_window"),
    )


class EquipmentSession(TimeSeriesBase):  # type: ignore
    """Equipment operation sessions for work tracking.

    Tracks discrete work sessions and equipment utilization.
    """

    __tablename__ = "equipment_sessions"

    # Primary key and identification
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, unique=True, index=True)

    # Equipment information
    source_address = Column(Integer, nullable=False, index=True)
    equipment_type = Column(String(50), nullable=False, index=True)
    equipment_id = Column(String(100), nullable=True)
    operator_id = Column(String(100), nullable=True)

    # Session timing
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Float, nullable=True)  # hours

    # Operation details
    operation_type = Column(String(100), nullable=True)  # planting, harvesting, etc.
    field_id = Column(String(100), nullable=True, index=True)
    crop_type = Column(String(50), nullable=True)
    weather_conditions = Column(SQLiteJSON, nullable=True)

    # Performance summary
    total_fuel_consumed = Column(Float, nullable=True)  # liters
    total_distance = Column(Float, nullable=True)  # meters
    total_area_covered = Column(Float, nullable=True)  # hectares
    avg_working_speed = Column(Float, nullable=True)  # km/h
    efficiency_score = Column(Float, nullable=True)  # 0-1

    # Data quality
    message_count = Column(Integer, nullable=False, default=0)
    data_completeness = Column(Float, nullable=True)  # 0-1

    # GPS boundaries (for field mapping)
    start_location = Column(SQLiteJSON, nullable=True)  # {lat, lon, altitude}
    end_location = Column(SQLiteJSON, nullable=True)
    work_area_bounds = Column(SQLiteJSON, nullable=True)  # polygon coordinates

    # Session status
    is_active = Column(Boolean, nullable=False, default=True)
    completion_status = Column(String(50), nullable=True)  # completed, interrupted, error

    # Indexes for session queries
    __table_args__ = (
        Index("idx_session_equipment_start", "equipment_type", "start_time"),
        Index("idx_session_field_time", "field_id", "start_time"),
        Index("idx_session_active", "is_active", "start_time"),
    )


# Time-series partitioning configuration
PARTITION_STRATEGIES: dict[str, dict[str, str]] = {
    "can_messages_raw": {
        "type": "time_range",
        "interval": "1 day",
        "retention": "30 days",
        "compression": "lz4",
    },
    "can_messages_decoded": {
        "type": "time_range",
        "interval": "1 day",
        "retention": "90 days",
        "compression": "lz4",
    },
    "agricultural_metrics": {
        "type": "time_range",
        "interval": "1 week",
        "retention": "2 years",
        "compression": "lz4",
    },
    "can_network_health": {
        "type": "time_range",
        "interval": "1 week",
        "retention": "6 months",
        "compression": "lz4",
    },
    "equipment_sessions": {
        "type": "time_range",
        "interval": "1 month",
        "retention": "5 years",
        "compression": "lz4",
    },
}

# Index optimization for time-series queries
HYPERTABLE_CONFIG: dict[str, str | bool | int] = {
    "chunk_time_interval": "1 day",
    "create_default_indexes": True,
    "if_not_exists": True,
    "partitioning_column": "timestamp",
    "number_partitions": 4,
}

# Retention policies for automatic data cleanup
RETENTION_POLICIES: dict[str, timedelta] = {
    "critical_data": timedelta(days=365),  # Safety, emergency data
    "operational_data": timedelta(days=90),  # Standard operations
    "diagnostic_data": timedelta(days=30),  # Troubleshooting data
    "test_data": timedelta(days=7),  # Development/testing
}

# Aggregation schedules for metrics computation
AGGREGATION_SCHEDULES: dict[str, dict[str, str]] = {
    "1min": {"source": "raw", "schedule": "continuous"},
    "5min": {"source": "1min", "schedule": "every 1 minute"},
    "1hour": {"source": "5min", "schedule": "every 5 minutes"},
    "1day": {"source": "1hour", "schedule": "every 1 hour"},
    "1week": {"source": "1day", "schedule": "every 6 hours"},
}
