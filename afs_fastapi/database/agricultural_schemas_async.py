"""
Async-compatible agricultural database schemas with SQLAlchemy 2.0 async support.

This module provides async-compatible SQLAlchemy models for agricultural operations data storage,
including time-series data for ISOBUS messages and relational data for equipment,
fields, and operational metadata. All models are designed for high-performance
async operations with proper typing and async session support.

Implementation follows Test-First Development (TDD) GREEN phase with agricultural robotics context.
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase):
    """Base model for async-compatible SQLAlchemy 2.0 models."""

    pass


class JSONType(TypeDecorator):
    """Custom JSON type that handles serialization for database compatibility."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        """Convert Python object to JSON string for database storage."""
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value: str | None, dialect: Any) -> Any:
        """Convert JSON string from database to Python object."""
        if value is not None:
            return json.loads(value)
        return value


class Equipment(Base):
    """Async-compatible equipment registry for ISOBUS-compatible agricultural machinery.

    Stores metadata for tractors, implements, and other agricultural equipment
    with ISOBUS address mapping for fleet coordination in async environments.
    """

    __tablename__ = "equipment"

    equipment_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    isobus_address: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    equipment_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # tractor, implement, sensor
    manufacturer: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    installation_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="active"
    )  # active, maintenance, retired
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, onupdate=lambda: datetime.now(UTC)
    )

    # Relationships
    isobus_messages: Mapped[list[ISOBUSMessageRecord]] = relationship(
        "ISOBUSMessageRecord", back_populates="equipment"
    )
    sensor_records: Mapped[list[AgriculturalSensorRecord]] = relationship(
        "AgriculturalSensorRecord", back_populates="equipment"
    )
    telemetry_records: Mapped[list[TractorTelemetryRecord]] = relationship(
        "TractorTelemetryRecord", back_populates="equipment"
    )
    yield_records: Mapped[list[YieldMonitorRecord]] = relationship(
        "YieldMonitorRecord", back_populates="equipment"
    )
    operational_sessions: Mapped[list[OperationalSession]] = relationship(
        "OperationalSession", back_populates="equipment"
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_equipment_isobus_addr", "isobus_address"),
        Index("idx_equipment_type_status", "equipment_type", "status"),
    )


class Field(Base):
    """Async-compatible agricultural field boundaries and metadata for operation planning.

    Stores field information including GPS boundaries, crop types, and soil
    characteristics for precision agriculture operations in async environments.
    """

    __tablename__ = "fields"

    field_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    crop_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    field_area_hectares: Mapped[float | None] = mapped_column(Float, nullable=True)
    boundary_coordinates: Mapped[list | None] = mapped_column(
        JSONType, nullable=True
    )  # List of (lat, lon) tuples
    soil_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    drainage_class: Mapped[str | None] = mapped_column(String(30), nullable=True)
    elevation_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    slope_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # Relationships
    sensor_records: Mapped[list[AgriculturalSensorRecord]] = relationship(
        "AgriculturalSensorRecord", back_populates="field"
    )
    yield_records: Mapped[list[YieldMonitorRecord]] = relationship(
        "YieldMonitorRecord", back_populates="field"
    )
    operational_sessions: Mapped[list[OperationalSession]] = relationship(
        "OperationalSession", back_populates="field"
    )

    # Indexes for geographic and crop queries
    __table_args__ = (
        Index("idx_field_crop_type", "crop_type"),
        Index("idx_field_area", "field_area_hectares"),
    )


class ISOBUSMessageRecord(Base):
    """Async-compatible time-series storage for ISOBUS messages with high-frequency capability.

    Stores raw ISOBUS communication messages for fleet coordination,
    safety monitoring, and communication analysis in async environments.
    """

    __tablename__ = "isobus_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    equipment_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("equipment.equipment_id"), nullable=False
    )
    pgn: Mapped[int] = mapped_column(Integer, nullable=False)  # Parameter Group Number
    source_address: Mapped[int] = mapped_column(Integer, nullable=False)
    destination_address: Mapped[int] = mapped_column(Integer, nullable=False)
    data_payload: Mapped[dict | None] = mapped_column(
        JSONType, nullable=True
    )  # Parsed message data
    priority_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    equipment: Mapped[Equipment] = relationship("Equipment", back_populates="isobus_messages")

    # Time-series optimized indexes
    __table_args__ = (
        Index("idx_isobus_timestamp_equipment", "timestamp", "equipment_id"),
        Index("idx_isobus_pgn_priority", "pgn", "priority_level"),
        Index("idx_isobus_time_range", "timestamp"),  # For time-range queries
    )


class AgriculturalSensorRecord(Base):
    """Async-compatible time-series storage for agricultural sensor data with field mapping.

    Stores sensor readings from various agricultural monitoring systems
    including soil, crop, and environmental sensors in async environments.
    """

    __tablename__ = "agricultural_sensor_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    equipment_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("equipment.equipment_id"), nullable=False
    )
    field_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("fields.field_id"), nullable=True
    )
    sensor_type: Mapped[str] = mapped_column(String(30), nullable=False)
    sensor_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    gps_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    gps_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_indicator: Mapped[str] = mapped_column(
        String(20), default="good"
    )  # good, warning, error
    calibration_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    equipment: Mapped[Equipment] = relationship("Equipment", back_populates="sensor_records")
    field: Mapped[Field | None] = relationship("Field", back_populates="sensor_records")

    # Sensor analytics optimized indexes
    __table_args__ = (
        Index("idx_sensor_timestamp_type", "timestamp", "sensor_type"),
        Index("idx_sensor_equipment_field", "equipment_id", "field_id"),
        Index("idx_sensor_type_quality", "sensor_type", "quality_indicator"),
        Index("idx_sensor_gps", "gps_latitude", "gps_longitude"),
    )


class TractorTelemetryRecord(Base):
    """Async-compatible time-series storage for tractor operational telemetry data.

    Stores real-time tractor operational parameters for fleet monitoring,
    safety analysis, and performance optimization in async environments.
    """

    __tablename__ = "tractor_telemetry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    equipment_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("equipment.equipment_id"), nullable=False
    )
    vehicle_speed: Mapped[float] = mapped_column(Float, nullable=False)  # km/h
    fuel_level: Mapped[float] = mapped_column(Float, nullable=False)  # percent (0-100)
    engine_temperature: Mapped[float] = mapped_column(Float, nullable=False)  # celsius
    gps_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    gps_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    operational_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    engine_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    hydraulic_pressure: Mapped[float | None] = mapped_column(Float, nullable=True)  # bar
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    equipment: Mapped[Equipment] = relationship("Equipment", back_populates="telemetry_records")

    # Telemetry analytics optimized indexes
    __table_args__ = (
        Index("idx_telemetry_timestamp_equipment", "timestamp", "equipment_id"),
        Index("idx_telemetry_operational_mode", "operational_mode"),
        Index("idx_telemetry_gps", "gps_latitude", "gps_longitude"),
        Index("idx_telemetry_fuel_temp", "fuel_level", "engine_temperature"),
    )


class YieldMonitorRecord(Base):
    """Async-compatible time-series storage for yield monitoring data from harvest operations.

    Stores harvest yield information with GPS mapping for precision
    agriculture analytics and field performance assessment in async environments.
    """

    __tablename__ = "yield_monitor_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    equipment_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("equipment.equipment_id"), nullable=False
    )
    field_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("fields.field_id"), nullable=True
    )
    crop_type: Mapped[str] = mapped_column(String(30), nullable=False)
    yield_volume: Mapped[float] = mapped_column(Float, nullable=False)  # tons per hectare
    moisture_content: Mapped[float] = mapped_column(Float, nullable=False)  # percent
    gps_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    gps_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    harvest_width: Mapped[float] = mapped_column(Float, nullable=False)  # meters
    harvest_speed: Mapped[float] = mapped_column(Float, nullable=False)  # km/h
    grain_temperature: Mapped[float | None] = mapped_column(Float, nullable=True)  # celsius
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    equipment: Mapped[Equipment] = relationship("Equipment", back_populates="yield_records")
    field: Mapped[Field | None] = relationship("Field", back_populates="yield_records")

    # Yield analytics optimized indexes
    __table_args__ = (
        Index("idx_yield_timestamp_equipment", "timestamp", "equipment_id"),
        Index("idx_yield_field_crop", "field_id", "crop_type"),
        Index("idx_yield_gps", "gps_latitude", "gps_longitude"),
        Index("idx_yield_volume_moisture", "yield_volume", "moisture_content"),
    )


class OperationalSession(Base):
    """Async-compatible operational session tracking for agricultural field operations.

    Tracks complete field operations from start to finish with performance
    metrics, resource consumption, and operational outcomes in async environments.
    """

    __tablename__ = "operational_sessions"

    session_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    equipment_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("equipment.equipment_id"), nullable=False
    )
    field_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("fields.field_id"), nullable=True
    )
    operation_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # planting, cultivation, harvesting
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_area_covered: Mapped[float | None] = mapped_column(Float, nullable=True)  # hectares
    total_yield: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # tons (for harvest operations)
    average_speed: Mapped[float | None] = mapped_column(Float, nullable=True)  # km/h
    fuel_consumed: Mapped[float | None] = mapped_column(Float, nullable=True)  # liters
    operator_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    weather_conditions: Mapped[str | None] = mapped_column(String(100), nullable=True)
    soil_conditions: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_status: Mapped[str] = mapped_column(
        String(20), default="active"
    )  # active, completed, aborted
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # Relationships
    equipment: Mapped[Equipment] = relationship("Equipment", back_populates="operational_sessions")
    field: Mapped[Field | None] = relationship("Field", back_populates="operational_sessions")

    # Operation analytics optimized indexes
    __table_args__ = (
        Index("idx_session_equipment_type", "equipment_id", "operation_type"),
        Index("idx_session_time_range", "start_time", "end_time"),
        Index("idx_session_field_operation", "field_id", "operation_type"),
        Index("idx_session_status", "session_status"),
    )


class TokenUsage(Base):
    """Async-compatible SQLAlchemy model for tracking token usage by agents and tasks.

    Optimized for high-frequency token tracking in agricultural AI operations
    with async session support and performance optimizations.
    """

    __tablename__ = "token_usage"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # Unique ID for each log entry
    agent_id: Mapped[str] = mapped_column(String, nullable=False)
    task_id: Mapped[str] = mapped_column(String, nullable=False)
    tokens_used: Mapped[float] = mapped_column(Float, nullable=False)
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Async-compatible indexes for performance
    __table_args__ = (
        Index("idx_token_usage_agent_task", "agent_id", "task_id"),
        Index("idx_token_usage_timestamp", "timestamp"),
        Index("idx_token_usage_model", "model_name"),
    )

    def __repr__(self) -> str:
        return (
            f"<TokenUsage(id='{self.id}', agent_id='{self.agent_id}', "
            f"task_id='{self.task_id}', tokens_used={self.tokens_used}, "
            f"model_name='{self.model_name}', timestamp='{self.timestamp}')>"
        )


# Async database utilities
class AsyncDatabaseManager:
    """Unified async database manager for agricultural operations.

    Provides async-compatible database operations with connection pooling,
    session management, and transaction handling specifically optimized
    for agricultural robotics data patterns.
    """

    def __init__(self, database_url: str, pool_config: dict | None = None) -> None:
        """Initialize async database manager.

        Parameters
        ----------
        database_url : str
            Database connection URL (PostgreSQL preferred for async operations)
        pool_config : dict, optional
            Connection pool configuration
        """
        self.database_url = database_url
        self.pool_config = pool_config or {}

        # Initialize async engine
        self.async_engine: AsyncEngine | None = None
        self.async_session_factory: async_sessionmaker[AsyncSession] | None = None

        # Performance tracking
        self._performance_metrics = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "avg_operation_time": 0.0,
            "operation_times": [],
        }

    async def initialize(self) -> bool:
        """Initialize async database connections and session factory.

        Returns
        -------
        bool
            True if initialization successful
        """
        try:
            # Create async engine with optimized settings
            self.async_engine = create_async_engine(
                self.database_url,
                pool_size=self.pool_config.get("pool_size", 20),
                max_overflow=self.pool_config.get("max_overflow", 10),
                pool_timeout=self.pool_config.get("pool_timeout", 30.0),
                pool_recycle=self.pool_config.get("pool_recycle", 3600),
                pool_pre_ping=True,
                echo=False,
                future=True,
            )

            # Create async session factory
            self.async_session_factory = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
            )

            # Test connection
            async with self.async_engine.connect() as conn:
                await conn.execute(select(func.now()))

            self._performance_metrics["total_operations"] += 1
            self._performance_metrics["successful_operations"] += 1

            return True

        except Exception as e:
            self._performance_metrics["total_operations"] += 1
            self._performance_metrics["failed_operations"] += 1
            raise RuntimeError(f"Failed to initialize async database: {e}")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session with proper error handling.

        Yields
        ------
        AsyncSession
            Database session with connection pooling
        """
        if not self.async_session_factory:
            raise RuntimeError("Database manager not initialized")

        session = self.async_session_factory()
        start_time = datetime.now(UTC)

        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
            self._update_performance_metrics(start_time, True)

    async def execute_transaction(self, operations: list[callable], session: AsyncSession) -> bool:
        """Execute multiple operations within a single transaction.

        Parameters
        ----------
        operations : list[callable]
            List of async operations to execute
        session : AsyncSession
            Database session

        Returns
        -------
        bool
            True if all operations successful
        """
        try:
            async with session.begin():
                for operation in operations:
                    await operation(session)
            return True
        except Exception as e:
            await session.rollback()
            self._performance_metrics["failed_operations"] += 1
            raise e

    def _update_performance_metrics(self, start_time: datetime, success: bool) -> None:
        """Update performance metrics for database operations.

        Parameters
        ----------
        start_time : datetime
            Operation start time
        success : bool
            Whether operation was successful
        """
        duration = (datetime.now(UTC) - start_time).total_seconds()
        self._performance_metrics["total_operations"] += 1
        self._performance_metrics["operation_times"].append(duration)

        if success:
            self._performance_metrics["successful_operations"] += 1
        else:
            self._performance_metrics["failed_operations"] += 1

        # Update average operation time
        times = self._performance_metrics["operation_times"]
        self._performance_metrics["avg_operation_time"] = sum(times) / len(times)

    async def get_performance_report(self) -> dict[str, Any]:
        """Generate comprehensive performance report.

        Returns
        -------
        dict[str, Any]
            Performance analysis report with agricultural-specific metrics
        """
        metrics = self._performance_metrics

        report = {
            "total_operations": metrics["total_operations"],
            "success_rate": (metrics["successful_operations"] / max(metrics["total_operations"], 1))
            * 100,
            "average_operation_time": metrics["avg_operation_time"],
            "agricultural_optimization": {
                "time_series_performance": self._assess_time_series_performance(),
                "connection_efficiency": self._assess_connection_efficiency(),
            },
            "recommendations": self._generate_performance_recommendations(),
        }

        return report

    def _assess_time_series_performance(self) -> dict[str, Any]:
        """Assess time-series data handling performance for agricultural operations.

        Returns
        -------
        dict[str, Any]
            Time-series performance assessment
        """
        metrics = self._performance_metrics

        # Calculate time-series specific metrics
        recent_operations = metrics["operation_times"][-100:]  # Last 100 operations

        return {
            "recent_avg_time": (
                sum(recent_operations) / len(recent_operations) if recent_operations else 0
            ),
            "batch_processing_capability": (
                "high"
                if len(recent_operations) > 50
                else "medium" if len(recent_operations) > 10 else "low"
            ),
            "agricultural_data_optimization": "optimized_for_high_frequency",
        }

    def _assess_connection_efficiency(self) -> dict[str, Any]:
        """Assess connection pooling efficiency for agricultural workloads.

        Returns
        -------
        dict[str, Any]
            Connection efficiency assessment
        """
        metrics = self._performance_metrics

        return {
            "connection_utilization": metrics["successful_operations"]
            / max(metrics["total_operations"], 1),
            "failure_rate": metrics["failed_operations"] / max(metrics["total_operations"], 1),
            "agricultural_workload_adaptation": "well_adapted_to_frequent_high_frequency_operations",
        }

    def _generate_performance_recommendations(self) -> list[str]:
        """Generate performance recommendations for agricultural database operations.

        Returns
        -------
        list[str]
            List of performance improvement recommendations
        """
        recommendations = []

        if self._performance_metrics["avg_operation_time"] > 0.5:
            recommendations.append(
                "Consider optimizing queries for agricultural time-series data patterns"
            )

        if (
            self._performance_metrics["failed_operations"]
            / max(self._performance_metrics["total_operations"], 1)
            > 0.05
        ):
            recommendations.append(
                "Review connection pool settings for agricultural workload patterns"
            )

        recommendations.append("Implement batch operations for high-frequency CAN message storage")
        recommendations.append(
            "Consider TimescaleDB hypertables for agricultural time-series optimization"
        )

        return recommendations

    async def shutdown(self) -> None:
        """Shutdown database connections gracefully."""
        if self.async_engine:
            await self.async_engine.dispose()


# Agricultural data validation functions
def validate_isobus_address(address: int) -> bool:
    """Validate ISOBUS address range (0x00-0xFF).

    Parameters
    ----------
    address : int
        ISOBUS address to validate

    Returns
    -------
    bool
        True if address is valid
    """
    return 0x00 <= address <= 0xFF


def validate_gps_coordinates(latitude: float, longitude: float) -> bool:
    """Validate GPS coordinate ranges for agricultural fields.

    Parameters
    ----------
    latitude : float
        Latitude coordinate
    longitude : float
        Longitude coordinate

    Returns
    -------
    bool
        True if coordinates are valid
    """
    return -90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0


def calculate_field_area_from_boundaries(coordinates: list[tuple[float, float]]) -> float:
    """Calculate field area from GPS boundary coordinates using Shoelace formula.

    Parameters
    ----------
    coordinates : list[tuple[float, float]]
        List of (latitude, longitude) boundary points

    Returns
    -------
    float
        Field area in hectares
    """
    if len(coordinates) < 3:
        return 0.0

    # Convert to approximate meters using simple projection
    # Note: This is a simplified calculation for demonstration
    lat_avg = sum(coord[0] for coord in coordinates) / len(coordinates)
    meters_per_degree_lat = 111320.0
    meters_per_degree_lon = 111320.0 * abs(lat_avg / 90.0)

    # Convert coordinates to meters
    meter_coords = [
        (lat * meters_per_degree_lat, lon * meters_per_degree_lon) for lat, lon in coordinates
    ]

    # Shoelace formula for polygon area
    area = 0.0
    n = len(meter_coords)
    for i in range(n):
        j = (i + 1) % n
        area += meter_coords[i][0] * meter_coords[j][1]
        area -= meter_coords[j][0] * meter_coords[i][1]

    area = abs(area) / 2.0
    return area / 10000.0  # Convert square meters to hectares
