from __future__ import annotations

"""
Agricultural database module for time-series and relational data management.

This module provides database schemas, models, and utilities for storing
and managing agricultural data including ISOBUS messages, sensor readings,
equipment metadata, operational analytics, and comprehensive data archiving.
"""

from .agricultural_archiving import (
    ArchivalManager,
    ArchivalResult,
    ArchivalStatus,
    ComplianceCheck,
    DataLifecycleStage,
    DataRetentionPolicy,
    RecoveryResult,
    RecoveryStatus,
    RetentionPeriod,
    apply_retention_policy,
    archive_expired_data,
    cleanup_old_archives,
    compress_historical_data,
    create_retention_policies,
    get_storage_statistics,
)
from .agricultural_schemas import (
    AgriculturalSensorRecord,
    Base,
    Equipment,
    Field,
    ISOBUSMessageRecord,
    OperationalSession,
    TractorTelemetryRecord,
    YieldMonitorRecord,
    calculate_field_area_from_boundaries,
    create_agricultural_tables,
    get_database_engine,
    validate_gps_coordinates,
    validate_isobus_address,
)

__all__ = [
    # Database schemas
    "Base",
    "Equipment",
    "Field",
    "ISOBUSMessageRecord",
    "AgriculturalSensorRecord",
    "TractorTelemetryRecord",
    "YieldMonitorRecord",
    "OperationalSession",
    "get_database_engine",
    "create_agricultural_tables",
    "validate_isobus_address",
    "validate_gps_coordinates",
    "calculate_field_area_from_boundaries",
    # Data archiving and retention
    "DataRetentionPolicy",
    "ArchivalManager",
    "DataLifecycleStage",
    "RetentionPeriod",
    "ArchivalStatus",
    "ArchivalResult",
    "ComplianceCheck",
    "RecoveryResult",
    "RecoveryStatus",
    "create_retention_policies",
    "apply_retention_policy",
    "archive_expired_data",
    "compress_historical_data",
    "get_storage_statistics",
    "cleanup_old_archives",
]
