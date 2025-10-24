"""
Agricultural database schemas for time-series and relational data.

This module provides SQLAlchemy models for agricultural operations data storage,
including time-series data for ISOBUS messages and relational data for equipment,
fields, and operational metadata.

Implementation follows Test-First Development (TDD) GREEN phase.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase):
    """Base model for type-safe SQLAlchemy 2.0 models."""

    pass


class JSONType(TypeDecorator):
    """Custom JSON type that handles serialization for SQLite compatibility."""

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
    """Equipment registry for ISOBUS-compatible agricultural machinery.

    Stores metadata for tractors, implements, and other agricultural equipment
    with ISOBUS address mapping for fleet coordination.
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
    """Agricultural field boundaries and metadata for operation planning.

    Stores field information including GPS boundaries, crop types, and soil
    characteristics for precision agriculture operations.
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
    """Time-series storage for ISOBUS messages with high-frequency capability.

    Stores raw ISOBUS communication messages for fleet coordination,
    safety monitoring, and communication analysis.
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
    """Time-series storage for agricultural sensor data with field mapping.

    Stores sensor readings from various agricultural monitoring systems
    including soil, crop, and environmental sensors.
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
    """Time-series storage for tractor operational telemetry data.

    Stores real-time tractor operational parameters for fleet monitoring,
    safety analysis, and performance optimization.
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
    """Time-series storage for yield monitoring data from harvest operations.

    Stores harvest yield information with GPS mapping for precision
    agriculture analytics and field performance assessment.
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
    """Operational session tracking for agricultural field operations.

    Tracks complete field operations from start to finish with performance
    metrics, resource consumption, and operational outcomes.
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


def get_database_engine(database_url: str = "sqlite:///agricultural_data.db") -> Any:
    """Create database engine with agricultural data optimizations.

    Parameters
    ----------
    database_url : str, default "sqlite:///agricultural_data.db"
        Database connection URL

    Returns
    -------
    sqlalchemy.engine.Engine
        Configured database engine for agricultural data
    """
    engine = create_engine(
        database_url,
        echo=False,  # Set to True for SQL debugging
        pool_pre_ping=True,  # Verify connections before use
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    )

    # SQLite-specific optimizations for time-series data
    if "sqlite" in database_url:

        @event.listens_for(engine, "connect")
        def configure_sqlite(dbapi_connection: Any, connection_record: Any) -> None:
            """Configure SQLite for time-series performance."""
            cursor = dbapi_connection.cursor()
            # Enable Write-Ahead Logging for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            # Increase cache size for better performance
            cursor.execute("PRAGMA cache_size=10000")
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def create_agricultural_tables(engine: Any) -> None:
    """Create all agricultural database tables with proper indexes.

    Parameters
    ----------
    engine : sqlalchemy.engine.Engine
        Database engine for table creation
    """
    # Create all tables defined in Base metadata
    Base.metadata.create_all(engine)

    # Additional index creation for time-series optimization
    with engine.connect() as connection:
        # PostgreSQL/TimescaleDB specific optimizations (if using PostgreSQL)
        if "postgresql" in str(engine.url):
            # Create time-series specific indexes for PostgreSQL
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_isobus_messages_time_bucket
                ON isobus_messages USING BTREE (date_trunc('minute', timestamp))
            """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_sensor_data_time_bucket
                ON agricultural_sensor_data USING BTREE (date_trunc('hour', timestamp))
            """
            )
            connection.commit()


def get_time_series_partition_info(
    table_name: str, start_date: datetime, end_date: datetime
) -> dict[str, Any]:
    """Get time-series partition information for large agricultural datasets.

    Parameters
    ----------
    table_name : str
        Name of the time-series table
    start_date : datetime
        Start date for partition analysis
    end_date : datetime
        End date for partition analysis

    Returns
    -------
    dict[str, Any]
        Partition information and recommendations
    """
    time_span = end_date - start_date
    days = time_span.days

    partition_strategy = {
        "table_name": table_name,
        "time_span_days": days,
        "recommended_partition": "daily" if days > 365 else "weekly" if days > 30 else "none",
        "estimated_records_per_day": {
            "isobus_messages": 86400,  # Assume 1 message per second
            "agricultural_sensor_data": 1440,  # Assume 1 reading per minute
            "tractor_telemetry": 360,  # Assume 1 reading per 4 minutes
            "yield_monitor_data": 3600,  # Assume 1 reading per second during harvest
        }.get(table_name, 1000),
    }

    return partition_strategy


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
