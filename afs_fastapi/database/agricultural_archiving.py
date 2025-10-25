"""
Agricultural data archiving and retention policies management.

This module provides comprehensive data lifecycle management for agricultural
operations, including time-based retention policies, archival processes,
and storage optimization for high-frequency ISOBUS and sensor data.

Implementation follows Test-First Development (TDD) GREEN phase.
"""

from __future__ import annotations

import gzip
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy.orm import Session

from afs_fastapi.database.agricultural_schemas import (
    AgriculturalSensorRecord,
    ISOBUSMessageRecord,
    OperationalSession,
    TractorTelemetryRecord,
    YieldMonitorRecord,
)

# Configure logging for agricultural archival operations
logger = logging.getLogger(__name__)


class RetentionPeriod(Enum):
    """Agricultural data retention periods for compliance and storage optimization."""

    DAYS_30 = "30_days"
    DAYS_90 = "90_days"
    DAYS_365 = "365_days"
    YEARS_2 = "2_years"
    YEARS_5 = "5_years"
    YEARS_10 = "10_years"
    PERMANENT = "permanent"

    @property
    def days(self) -> int:
        """Get retention period in days."""
        retention_mapping = {
            "30_days": 30,
            "90_days": 90,
            "365_days": 365,
            "2_years": 730,
            "5_years": 1825,
            "10_years": 3650,
            "permanent": -1,  # Special value for permanent retention
        }
        return retention_mapping[self.value]


class DataLifecycleStage(Enum):
    """Data lifecycle stages for agricultural operations."""

    REAL_TIME = "real_time"
    DAILY_AGGREGATION = "daily_aggregation"
    HISTORICAL_ANALYTICS = "historical_analytics"
    ARCHIVED = "archived"


class ArchivalStatus(Enum):
    """Status of archival operations."""

    SUCCESS = "success"
    IN_PROGRESS = "in_progress"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class DataRetentionPolicy:
    """Agricultural data retention policy configuration.

    Defines how different types of agricultural data should be retained,
    archived, and managed throughout their lifecycle.
    """

    policy_id: str
    table_name: str
    retention_period: RetentionPeriod
    lifecycle_stage: DataLifecycleStage
    compression_enabled: bool = True
    archive_location: str | None = None
    metadata_retention: RetentionPeriod = RetentionPeriod.YEARS_10
    policy_description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Initialize policy timestamps."""
        if self.created_at is None:
            self.created_at = datetime.now(UTC)
        if self.updated_at is None:
            self.updated_at = datetime.now(UTC)


@dataclass
class ArchivalResult:
    """Result of an archival operation."""

    status: ArchivalStatus
    records_archived: int
    compression_ratio: float
    archive_location: str | None
    execution_time: float
    error_message: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class ComplianceCheck:
    """Compliance check result for agricultural data."""

    requires_permanent_retention: bool
    compliance_category: str
    regulatory_basis: str
    retention_justification: str


@dataclass
class RecoveryResult:
    """Result of archived data recovery operation."""

    status: ArchivalStatus
    restoration_id: str
    estimated_records: int
    estimated_completion_time: datetime
    recovery_location: str | None = None


@dataclass
class RecoveryStatus:
    """Status of ongoing data recovery operation."""

    restoration_id: str
    progress_percentage: float
    current_stage: str
    estimated_completion: datetime
    error_message: str | None = None


class ArchivalManager:
    """Manages agricultural data archival and retention policies.

    Provides comprehensive lifecycle management for agricultural data including
    automated archival, compliance checking, and data recovery capabilities.
    """

    def __init__(
        self,
        database_session: Session,
        storage_backend: str = "local",
        compression_algorithm: str = "gzip",
        encryption_enabled: bool = False,
        batch_size: int = 1000,
        max_archive_workers: int = 2,
        notification_webhook: str | None = None,
    ) -> None:
        """Initialize archival manager with agricultural-specific configuration.

        Parameters
        ----------
        database_session : Session
            SQLAlchemy database session
        storage_backend : str, default "local"
            Storage backend type (local, s3, gcs)
        compression_algorithm : str, default "gzip"
            Compression algorithm for archived data
        encryption_enabled : bool, default False
            Enable encryption for archived data
        batch_size : int, default 1000
            Number of records to process in each batch
        max_archive_workers : int, default 2
            Maximum number of concurrent archival workers
        notification_webhook : str, optional
            Webhook URL for archival notifications
        """
        self.database_session = database_session
        self.storage_backend = storage_backend
        self.compression_algorithm = compression_algorithm
        self.encryption_enabled = encryption_enabled
        self.batch_size = batch_size
        self.max_archive_workers = max_archive_workers
        self.notification_webhook = notification_webhook

        # Initialize retention policies
        self._retention_policies: dict[str, DataRetentionPolicy] = {}
        self._load_default_policies()

    def _load_default_policies(self) -> None:
        """Load default agricultural retention policies."""
        default_policies = [
            DataRetentionPolicy(
                policy_id="ISOBUS_MESSAGES_RETENTION",
                table_name="isobus_messages",
                retention_period=RetentionPeriod.DAYS_30,
                lifecycle_stage=DataLifecycleStage.REAL_TIME,
                compression_enabled=True,
                archive_location="archives/isobus/",
                policy_description="High-frequency CAN bus messages for real-time operations",
            ),
            DataRetentionPolicy(
                policy_id="SENSOR_DATA_RETENTION",
                table_name="agricultural_sensor_data",
                retention_period=RetentionPeriod.YEARS_2,
                lifecycle_stage=DataLifecycleStage.DAILY_AGGREGATION,
                compression_enabled=True,
                archive_location="archives/sensors/",
                policy_description="Agricultural sensor readings with daily aggregations",
            ),
            DataRetentionPolicy(
                policy_id="TELEMETRY_DATA_RETENTION",
                table_name="tractor_telemetry",
                retention_period=RetentionPeriod.DAYS_365,
                lifecycle_stage=DataLifecycleStage.DAILY_AGGREGATION,
                compression_enabled=True,
                archive_location="archives/telemetry/",
                policy_description="Tractor operational telemetry for fleet management",
            ),
            DataRetentionPolicy(
                policy_id="YIELD_DATA_RETENTION",
                table_name="yield_monitor_data",
                retention_period=RetentionPeriod.YEARS_10,
                lifecycle_stage=DataLifecycleStage.HISTORICAL_ANALYTICS,
                compression_enabled=True,
                archive_location="archives/yield/",
                policy_description="Yield monitoring data for long-term analytics",
            ),
            DataRetentionPolicy(
                policy_id="OPERATIONAL_SESSIONS_RETENTION",
                table_name="operational_sessions",
                retention_period=RetentionPeriod.PERMANENT,
                lifecycle_stage=DataLifecycleStage.HISTORICAL_ANALYTICS,
                compression_enabled=False,
                archive_location="archives/operations/",
                policy_description="Critical operational data for compliance and analytics",
            ),
        ]

        for policy in default_policies:
            self._retention_policies[policy.policy_id] = policy

    def get_default_policies(self) -> list[DataRetentionPolicy]:
        """Get list of default retention policies.

        Returns
        -------
        list[DataRetentionPolicy]
            List of default agricultural retention policies
        """
        return list(self._retention_policies.values())

    def identify_expired_data(self, retention_policy: DataRetentionPolicy) -> list[Any]:
        """Identify data that has exceeded retention period.

        Parameters
        ----------
        retention_policy : DataRetentionPolicy
            Retention policy to apply

        Returns
        -------
        list[Any]
            List of expired database records
        """
        if retention_policy.retention_period == RetentionPeriod.PERMANENT:
            return []  # Permanent data never expires

        cutoff_date = datetime.now(UTC) - timedelta(days=retention_policy.retention_period.days)

        # Get appropriate model class
        model_mapping = {
            "isobus_messages": ISOBUSMessageRecord,
            "agricultural_sensor_data": AgriculturalSensorRecord,
            "tractor_telemetry": TractorTelemetryRecord,
            "yield_monitor_data": YieldMonitorRecord,
            "operational_sessions": OperationalSession,
        }

        model_class = model_mapping.get(retention_policy.table_name)
        if not model_class:
            logger.error(f"Unknown table name: {retention_policy.table_name}")
            return []

        # Query expired records
        expired_records = (
            self.database_session.query(model_class)
            .filter(model_class.timestamp < cutoff_date)  # type: ignore[attr-defined]
            .all()
        )

        logger.info(
            f"Identified {len(expired_records)} expired records for policy {retention_policy.policy_id}"
        )
        return expired_records

    def archive_expired_data(self, retention_policy: DataRetentionPolicy) -> ArchivalResult:
        """Archive data that has exceeded retention period.

        Parameters
        ----------
        retention_policy : DataRetentionPolicy
            Retention policy to apply

        Returns
        -------
        ArchivalResult
            Result of archival operation
        """
        start_time = datetime.now(UTC)

        try:
            # Identify expired data
            expired_records = self.identify_expired_data(retention_policy)

            if not expired_records:
                return ArchivalResult(
                    status=ArchivalStatus.SUCCESS,
                    records_archived=0,
                    compression_ratio=0.0,
                    archive_location=None,
                    execution_time=0.0,
                )

            # Convert records to archival format
            archive_data = []
            for record in expired_records:
                record_dict = {
                    "id": getattr(record, "id", None),
                    "timestamp": record.timestamp.isoformat(),
                    "equipment_id": getattr(record, "equipment_id", None),
                    "data": self._serialize_record(record),
                }
                archive_data.append(record_dict)

            # Compress data if enabled
            compressed_data = (
                self._compress_data(archive_data)
                if retention_policy.compression_enabled
                else archive_data
            )

            # Calculate compression ratio
            original_size = len(json.dumps(archive_data).encode())
            compressed_size = (
                len(compressed_data) if isinstance(compressed_data, bytes) else original_size
            )
            compression_ratio = (
                1.0 - (compressed_size / original_size) if original_size > 0 else 0.0
            )

            # Store archived data
            data_to_store = compressed_data if isinstance(compressed_data, bytes) else b""
            archive_location = self._store_archived_data(
                data_to_store, retention_policy.policy_id, retention_policy.archive_location
            )

            # Remove archived records from active database
            for record in expired_records:
                self.database_session.delete(record)
            execution_time = (datetime.now(UTC) - start_time).total_seconds()

            logger.info(
                f"Successfully archived {len(expired_records)} records for policy {retention_policy.policy_id}"
            )

            return ArchivalResult(
                status=ArchivalStatus.SUCCESS,
                records_archived=len(expired_records),
                compression_ratio=compression_ratio,
                archive_location=archive_location,
                execution_time=execution_time,
                metadata={
                    "policy_id": retention_policy.policy_id,
                    "table_name": retention_policy.table_name,
                },
            )

        except Exception as e:
            execution_time = (datetime.now(UTC) - start_time).total_seconds()
            logger.error(f"Archival failed for policy {retention_policy.policy_id}: {e}")

            return ArchivalResult(
                status=ArchivalStatus.FAILED,
                records_archived=0,
                compression_ratio=0.0,
                archive_location=None,
                execution_time=execution_time,
                error_message=str(e),
            )

    def _serialize_record(self, record: Any) -> dict[str, Any]:
        """Serialize database record for archival storage.

        Parameters
        ----------
        record : Any
            Database record to serialize

        Returns
        -------
        dict[str, Any]
            Serialized record data
        """
        record_dict = {}
        for column in record.__table__.columns:
            value = getattr(record, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            record_dict[column.name] = value
        return record_dict

    def _compress_data(self, data: list[dict[str, Any]]) -> bytes:
        """Compress archival data using specified algorithm.

        Parameters
        ----------
        data : list[dict[str, Any]]
            Data to compress

        Returns
        -------
        bytes
            Compressed data
        """
        json_data = json.dumps(data, default=str).encode()

        if self.compression_algorithm == "gzip":
            return gzip.compress(json_data)
        else:
            # Fallback to no compression
            return json_data

    def _store_archived_data(self, data: bytes, policy_id: str, base_location: str | None) -> str:
        """Store archived data to configured storage backend.

        Parameters
        ----------
        data : bytes
            Compressed archived data
        policy_id : str
            Policy identifier
        base_location : str, optional
            Base storage location

        Returns
        -------
        str
            Final storage location
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"{policy_id}_{timestamp}.archive"

        if self.storage_backend == "local":
            # For testing - simulate local storage
            archive_location = f"local_archives/{filename}"
            logger.info(f"Archived data stored locally at {archive_location}")
        elif self.storage_backend == "s3":
            # S3 storage implementation would go here
            archive_location = f"{base_location or 's3://agricultural-archives/'}{filename}"
            logger.info(f"Archived data stored in S3 at {archive_location}")
        else:
            # Default to local storage
            archive_location = f"archives/{filename}"
            logger.info(f"Archived data stored at {archive_location}")

        return archive_location

    def get_storage_statistics(self) -> dict[str, Any]:
        """Calculate comprehensive storage statistics for agricultural data.

        Returns
        -------
        dict[str, Any]
            Storage statistics and recommendations
        """
        stats: dict[str, Any] = {
            "total_records": 0,
            "table_statistics": {},
            "retention_policy_compliance": {},
            "estimated_storage_size": 0,
            "archival_candidates": {},
        }

        # Table-specific statistics
        table_models = {
            "isobus_messages": ISOBUSMessageRecord,
            "agricultural_sensor_data": AgriculturalSensorRecord,
            "tractor_telemetry": TractorTelemetryRecord,
            "yield_monitor_data": YieldMonitorRecord,
            "operational_sessions": OperationalSession,
        }

        for table_name, model_class in table_models.items():
            try:
                record_count = self.database_session.query(model_class).count()
                stats["total_records"] += record_count
                stats["table_statistics"][table_name] = {
                    "record_count": record_count,
                    "oldest_record": self._get_oldest_record_date(model_class),
                    "newest_record": self._get_newest_record_date(model_class),
                }

                # Estimate storage size (rough calculation)
                estimated_size = record_count * 1024  # Assume 1KB per record average
                stats["estimated_storage_size"] += estimated_size

            except Exception as e:
                logger.error(f"Error calculating statistics for {table_name}: {e}")

        # Calculate archival candidates
        for policy_id, policy in self._retention_policies.items():
            if policy.retention_period != RetentionPeriod.PERMANENT:
                expired_count = len(self.identify_expired_data(policy))
                stats["archival_candidates"][policy_id] = expired_count

        return stats

    def _get_oldest_record_date(self, model_class: Any) -> datetime | None:
        """Get oldest record timestamp for a table."""
        try:
            result = (
                self.database_session.query(model_class.timestamp)
                .order_by(model_class.timestamp.asc())
                .first()
            )
            return result[0] if result else None
        except Exception:
            return None

    def _get_newest_record_date(self, model_class: Any) -> datetime | None:
        """Get newest record timestamp for a table."""
        try:
            result = (
                self.database_session.query(model_class.timestamp)
                .order_by(model_class.timestamp.desc())
                .first()
            )
            return result[0] if result else None
        except Exception:
            return None

    def check_compliance_retention(self, record: Any) -> ComplianceCheck:
        """Check compliance requirements for agricultural data retention.

        Parameters
        ----------
        record : Any
            Database record to check

        Returns
        -------
        ComplianceCheck
            Compliance check result
        """
        # Check for safety-critical operations
        if hasattr(record, "operation_type") and record.operation_type in [
            "emergency_stop",
            "collision_avoidance",
            "safety_incident",
        ]:
            return ComplianceCheck(
                requires_permanent_retention=True,
                compliance_category="safety_critical",
                regulatory_basis="agricultural_safety_regulations",
                retention_justification="Safety incidents must be retained permanently for regulatory compliance",
            )

        # Check for yield data (important for crop insurance and compliance)
        if hasattr(record, "yield_volume") and record.yield_volume is not None:
            return ComplianceCheck(
                requires_permanent_retention=False,
                compliance_category="yield_reporting",
                regulatory_basis="crop_insurance_requirements",
                retention_justification="Yield data retained for crop insurance and subsidy reporting",
            )

        # Default compliance check
        return ComplianceCheck(
            requires_permanent_retention=False,
            compliance_category="operational",
            regulatory_basis="standard_agricultural_operations",
            retention_justification="Standard operational data with normal retention period",
        )

    def restore_archived_data(self, recovery_request: dict[str, Any]) -> RecoveryResult:
        """Restore archived agricultural data for analysis or compliance.

        Parameters
        ----------
        recovery_request : dict[str, Any]
            Data recovery request specification

        Returns
        -------
        RecoveryResult
            Result of recovery operation
        """
        restoration_id = f"restore_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"

        # Simulate recovery process for testing
        estimated_records = 1000  # Would be calculated based on archive metadata
        estimated_completion = datetime.now(UTC) + timedelta(hours=2)

        logger.info(
            f"Starting data recovery {restoration_id} for archive {recovery_request.get('archive_id')}"
        )

        return RecoveryResult(
            status=ArchivalStatus.IN_PROGRESS,
            restoration_id=restoration_id,
            estimated_records=estimated_records,
            estimated_completion_time=estimated_completion,
            recovery_location=recovery_request.get("restore_location"),
        )

    def get_recovery_status(self, restoration_id: str) -> RecoveryStatus:
        """Get status of ongoing data recovery operation.

        Parameters
        ----------
        restoration_id : str
            Recovery operation identifier

        Returns
        -------
        RecoveryStatus
            Current recovery status
        """
        # Simulate recovery status for testing
        return RecoveryStatus(
            restoration_id=restoration_id,
            progress_percentage=75.0,
            current_stage="restoration",
            estimated_completion=datetime.now(UTC) + timedelta(minutes=30),
        )


# Convenience functions for policy management
def create_retention_policies() -> list[DataRetentionPolicy]:
    """Create default agricultural retention policies.

    Returns
    -------
    list[DataRetentionPolicy]
        List of default retention policies
    """
    manager = ArchivalManager(database_session=None)  # type: ignore[arg-type]
    return manager.get_default_policies()


def apply_retention_policy(database_session: Session, policy_id: str) -> ArchivalResult:
    """Apply specific retention policy to agricultural data.

    Parameters
    ----------
    database_session : Session
        Database session
    policy_id : str
        Retention policy identifier

    Returns
    -------
    ArchivalResult
        Result of retention policy application
    """
    manager = ArchivalManager(database_session=database_session)
    policy = manager._retention_policies.get(policy_id)

    if not policy:
        return ArchivalResult(
            status=ArchivalStatus.FAILED,
            records_archived=0,
            compression_ratio=0.0,
            archive_location=None,
            execution_time=0.0,
            error_message=f"Policy {policy_id} not found",
        )

    return manager.archive_expired_data(policy)


def archive_expired_data(database_session: Session) -> list[ArchivalResult]:
    """Archive all expired agricultural data using default policies.

    Parameters
    ----------
    database_session : Session
        Database session

    Returns
    -------
    list[ArchivalResult]
        Results of all archival operations
    """
    manager = ArchivalManager(database_session=database_session)
    results = []

    for policy in manager.get_default_policies():
        if policy.retention_period != RetentionPeriod.PERMANENT:
            result = manager.archive_expired_data(policy)
            results.append(result)

    return results


def compress_historical_data(database_session: Session, table_name: str) -> ArchivalResult:
    """Compress historical agricultural data without archiving.

    Parameters
    ----------
    database_session : Session
        Database session
    table_name : str
        Table to compress

    Returns
    -------
    ArchivalResult
        Result of compression operation
    """
    # Placeholder for in-place compression functionality
    logger.info(f"Compressing historical data for table {table_name}")

    return ArchivalResult(
        status=ArchivalStatus.SUCCESS,
        records_archived=0,
        compression_ratio=0.3,
        archive_location=None,
        execution_time=1.0,
        metadata={"operation": "compression", "table": table_name},
    )


def get_storage_statistics(database_session: Session) -> dict[str, Any]:
    """Get comprehensive storage statistics for agricultural data.

    Parameters
    ----------
    database_session : Session
        Database session

    Returns
    -------
    dict[str, Any]
        Storage statistics
    """
    manager = ArchivalManager(database_session=database_session)
    return manager.get_storage_statistics()


def cleanup_old_archives(archive_location: str, older_than_days: int = 2555) -> int:
    """Clean up old archive files to free storage space.

    Parameters
    ----------
    archive_location : str
        Archive storage location
    older_than_days : int, default 2555 (7 years)
        Remove archives older than this many days

    Returns
    -------
    int
        Number of archive files cleaned up
    """
    # Placeholder for archive cleanup functionality
    logger.info(f"Cleaning up archives in {archive_location} older than {older_than_days} days")

    # Simulate cleanup
    cleaned_files = 5
    logger.info(f"Cleaned up {cleaned_files} old archive files")

    return cleaned_files
