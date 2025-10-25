"""
Data retention and archival policies for CAN time-series data management.

This module implements automated data lifecycle management including retention
policies, archival strategies, and storage optimization for long-term agricultural
data analysis and compliance requirements.

Implementation follows Test-First Development (TDD) GREEN phase.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, TypedDict, cast

import pandas as pd
from sqlalchemy import text

from afs_fastapi.database.can_time_series_storage import CANTimeSeriesStorage

# Configure logging for data retention
logger = logging.getLogger(__name__)


class RetentionStats(TypedDict):
    total_archived: int
    total_deleted: int
    total_compressed: int
    last_cleanup: datetime | None
    archive_size_mb: float
    cleanup_duration: float


class CleanupResult(TypedDict):
    start_time: datetime
    rules_processed: int
    records_archived: int
    records_deleted: int
    errors: list[str]
    end_time: datetime | None
    duration_seconds: float | None


class DeletionImpact(TypedDict):
    records: int
    table_size: int


class ImpactResult(TypedDict):
    estimated_deletions: dict[str, DeletionImpact]
    estimated_archives: dict[str, Any]
    total_size_affected: int


class RetentionPolicy(Enum):
    """Data retention policy types."""

    CRITICAL = "critical"  # Safety, emergency data - long retention
    OPERATIONAL = "operational"  # Standard operations - medium retention
    DIAGNOSTIC = "diagnostic"  # Troubleshooting data - short retention
    EXPERIMENTAL = "experimental"  # Development/testing - very short retention


class ArchivalStrategy(Enum):
    """Data archival strategies."""

    NONE = "none"  # No archival, just delete
    LOCAL_STORAGE = "local"  # Archive to local storage
    CLOUD_STORAGE = "cloud"  # Archive to cloud storage (S3, GCS, etc.)
    COMPRESSED = "compressed"  # Compress and archive locally
    TAPE_STORAGE = "tape"  # Archive to tape storage


class CompressionFormat(Enum):
    """Supported compression formats for archival."""

    PARQUET = "parquet"  # Columnar format, excellent compression
    GZIP_CSV = "gzip_csv"  # Compressed CSV
    ZSTD = "zstd"  # Fast compression
    LZMA = "lzma"  # High compression ratio


@dataclass
class RetentionRule:
    """Data retention rule configuration."""

    name: str
    policy: RetentionPolicy
    retention_period: timedelta
    archival_strategy: ArchivalStrategy
    compression_format: CompressionFormat = CompressionFormat.PARQUET

    # Table-specific settings
    table_pattern: str = "*"
    where_clause: str | None = None

    # Archival settings
    archive_path: str | None = None
    archive_after: timedelta | None = None  # Archive before deletion

    # Performance settings
    batch_size: int = 10000
    parallel_workers: int = 2

    # Metadata
    description: str = ""
    enabled: bool = True


class CANDataRetentionManager:
    """Automated data retention and archival management for CAN time-series data."""

    def __init__(
        self,
        storage: CANTimeSeriesStorage,
        base_archive_path: str = "/var/lib/afs_fastapi/archives",
    ) -> None:
        """Initialize data retention manager.

        Parameters
        ----------
        storage : CANTimeSeriesStorage
            Time-series storage instance
        base_archive_path : str, default "/var/lib/afs_fastapi/archives"
            Base path for local archives
        """
        self.storage = storage
        self.base_archive_path = Path(base_archive_path)

        # Default retention rules
        self.retention_rules: list[RetentionRule] = self._create_default_rules()

        # Background tasks
        self._cleanup_task: asyncio.Task | None = None
        self._running = False

        # Statistics
        self.stats: RetentionStats = {
            "total_archived": 0,
            "total_deleted": 0,
            "total_compressed": 0,
            "last_cleanup": None,
            "archive_size_mb": 0.0,
            "cleanup_duration": 0.0,
        }

    def _create_default_rules(self) -> list[RetentionRule]:
        """Create default retention rules for agricultural data."""
        return [
            # Critical safety data - keep for 5 years
            RetentionRule(
                name="critical_safety_data",
                policy=RetentionPolicy.CRITICAL,
                retention_period=timedelta(days=1825),  # 5 years
                archival_strategy=ArchivalStrategy.COMPRESSED,
                archive_after=timedelta(days=365),  # Archive after 1 year
                table_pattern="can_messages_*",
                where_clause="priority <= 2 OR pgn IN (57344, 57345, 57346)",  # Emergency PGNs
                description="Critical safety and emergency data",
            ),
            # Operational data - keep for 2 years
            RetentionRule(
                name="operational_data",
                policy=RetentionPolicy.OPERATIONAL,
                retention_period=timedelta(days=730),  # 2 years
                archival_strategy=ArchivalStrategy.COMPRESSED,
                archive_after=timedelta(days=90),  # Archive after 3 months
                table_pattern="can_messages_*",
                where_clause="retention_policy = 'operational'",
                description="Standard operational data",
            ),
            # Raw message data - keep for 30 days
            RetentionRule(
                name="raw_messages_cleanup",
                policy=RetentionPolicy.DIAGNOSTIC,
                retention_period=timedelta(days=30),
                archival_strategy=ArchivalStrategy.COMPRESSED,
                archive_after=timedelta(days=7),  # Archive after 1 week
                table_pattern="can_messages_raw",
                where_clause="retention_policy = 'standard'",
                description="Standard raw CAN messages",
            ),
            # Decoded messages - keep for 90 days
            RetentionRule(
                name="decoded_messages_cleanup",
                policy=RetentionPolicy.OPERATIONAL,
                retention_period=timedelta(days=90),
                archival_strategy=ArchivalStrategy.COMPRESSED,
                archive_after=timedelta(days=30),
                table_pattern="can_messages_decoded",
                description="Decoded CAN messages",
            ),
            # Network health data - keep for 180 days
            RetentionRule(
                name="network_health_cleanup",
                policy=RetentionPolicy.DIAGNOSTIC,
                retention_period=timedelta(days=180),
                archival_strategy=ArchivalStrategy.LOCAL_STORAGE,
                table_pattern="can_network_health",
                description="Network health monitoring data",
            ),
            # Agricultural metrics - keep for 5 years (compressed)
            RetentionRule(
                name="metrics_long_term",
                policy=RetentionPolicy.CRITICAL,
                retention_period=timedelta(days=1825),  # 5 years
                archival_strategy=ArchivalStrategy.COMPRESSED,
                archive_after=timedelta(days=180),  # Archive after 6 months
                table_pattern="agricultural_metrics",
                description="Long-term agricultural performance metrics",
            ),
            # Equipment sessions - keep for 3 years
            RetentionRule(
                name="equipment_sessions_cleanup",
                policy=RetentionPolicy.OPERATIONAL,
                retention_period=timedelta(days=1095),  # 3 years
                archival_strategy=ArchivalStrategy.COMPRESSED,
                archive_after=timedelta(days=365),  # Archive after 1 year
                table_pattern="equipment_sessions",
                description="Equipment operation sessions",
            ),
            # Test data - keep for 7 days
            RetentionRule(
                name="test_data_cleanup",
                policy=RetentionPolicy.EXPERIMENTAL,
                retention_period=timedelta(days=7),
                archival_strategy=ArchivalStrategy.NONE,
                table_pattern="*",
                where_clause="retention_policy = 'test_data'",
                description="Development and testing data",
            ),
        ]

    async def start(self, cleanup_interval: float = 3600.0) -> None:
        """Start automated data retention management.

        Parameters
        ----------
        cleanup_interval : float, default 3600.0
            Cleanup interval in seconds (default: 1 hour)
        """
        if self._running:
            return

        self._running = True

        # Ensure archive directory exists
        self.base_archive_path.mkdir(parents=True, exist_ok=True)

        # Start background cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop(cleanup_interval))

        logger.info(f"Data retention manager started (cleanup every {cleanup_interval}s)")

    async def stop(self) -> None:
        """Stop data retention management."""
        if not self._running:
            return

        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("Data retention manager stopped")

    async def run_cleanup_cycle(self) -> CleanupResult:
        """Execute a complete data cleanup cycle.

        Returns
        -------
        CleanupResult
        """
        start_time = datetime.now(UTC)
        results: CleanupResult = {
            "start_time": start_time,
            "rules_processed": 0,
            "records_archived": 0,
            "records_deleted": 0,
            "errors": [],
            "end_time": None,
            "duration_seconds": None,
        }

        try:
            logger.info("Starting data cleanup cycle")

            for rule in self.retention_rules:
                if not rule.enabled:
                    continue

                try:
                    rule_results = await self._process_retention_rule(rule)
                    results["rules_processed"] += 1
                    results["records_archived"] += rule_results.get("archived", 0)
                    results["records_deleted"] += rule_results.get("deleted", 0)

                    logger.info(
                        f"Processed rule '{rule.name}': "
                        f"archived={rule_results.get('archived', 0)}, "
                        f"deleted={rule_results.get('deleted', 0)}"
                    )

                except Exception as e:
                    error_msg = f"Failed to process rule '{rule.name}': {e}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)

            # Update statistics
            end_time = datetime.now(UTC)
            duration = (end_time - start_time).total_seconds()

            self.stats["total_archived"] += results["records_archived"]
            self.stats["total_deleted"] += results["records_deleted"]
            self.stats["last_cleanup"] = end_time
            self.stats["cleanup_duration"] = duration

            results["end_time"] = end_time
            results["duration_seconds"] = duration

            logger.info(
                f"Cleanup cycle completed in {duration:.2f}s: "
                f"archived={results['records_archived']}, "
                f"deleted={results['records_deleted']}"
            )

        except Exception as e:
            logger.error(f"Cleanup cycle failed: {e}")
            results["errors"].append(str(e))

        return results

    async def _process_retention_rule(self, rule: RetentionRule) -> dict[str, int]:
        """Process a single retention rule.

        Parameters
        ----------
        rule : RetentionRule
            Retention rule to process

        Returns
        -------
        dict[str, int]
            Processing results (archived, deleted counts)
        """
        results = {"archived": 0, "deleted": 0}

        # Get tables matching the pattern
        tables = await self._get_matching_tables(rule.table_pattern)

        for table in tables:
            # Calculate cutoff dates
            current_time = datetime.now(UTC)
            deletion_cutoff = current_time - rule.retention_period
            archive_cutoff = None

            if rule.archive_after:
                archive_cutoff = current_time - rule.archive_after

            # Archive data if needed
            if (
                rule.archival_strategy != ArchivalStrategy.NONE
                and archive_cutoff
                and archive_cutoff > deletion_cutoff
            ):

                archived_count = await self._archive_table_data(
                    table, rule, archive_cutoff, deletion_cutoff
                )
                results["archived"] += archived_count

            # Delete old data
            deleted_count = await self._delete_old_data(table, rule, deletion_cutoff)
            results["deleted"] += deleted_count

        return results

    async def _get_matching_tables(self, pattern: str) -> list[str]:
        """Get database tables matching a pattern.

        Parameters
        ----------
        pattern : str
            Table name pattern (* for wildcard)

        Returns
        -------
        list[str]
            Matching table names
        """
        async with self.storage._get_async_session() as session:
            if pattern == "*":
                # Get all time-series tables
                query = text(
                    """
                    SELECT tablename FROM pg_tables
                    WHERE schemaname = 'public'
                    AND tablename LIKE 'can_%'
                    OR tablename LIKE 'agricultural_%'
                    OR tablename LIKE 'equipment_%'
                """
                )
            else:
                # Convert pattern to SQL LIKE pattern
                sql_pattern = pattern.replace("*", "%")
                query = text(
                    """
                    SELECT tablename FROM pg_tables
                    WHERE schemaname = 'public'
                    AND tablename LIKE :pattern
                """
                )

            result = await session.execute(
                query, {"pattern": sql_pattern} if pattern != "*" else {}
            )
            return [row[0] for row in result]

    async def _archive_table_data(
        self,
        table: str,
        rule: RetentionRule,
        archive_cutoff: datetime,
        deletion_cutoff: datetime,
    ) -> int:
        """Archive data from a table.

        Parameters
        ----------
        table : str
            Table name
        rule : RetentionRule
            Retention rule
        archive_cutoff : datetime
            Archive data older than this
        deletion_cutoff : datetime
            Delete data older than this (don't archive)

        Returns
        -------
        int
            Number of records archived
        """
        try:
            async with self.storage._get_async_session() as session:
                # Build query for data to archive
                base_query = f"""
                    SELECT * FROM {table}
                    WHERE timestamp < :archive_cutoff
                    AND timestamp >= :deletion_cutoff
                """

                if rule.where_clause:
                    base_query += f" AND ({rule.where_clause})"

                base_query += " ORDER BY timestamp"

                # Execute query in batches
                total_archived = 0
                offset = 0

                while True:
                    query = text(base_query + f" LIMIT {rule.batch_size} OFFSET {offset}")
                    result = await session.execute(
                        query,
                        {
                            "archive_cutoff": archive_cutoff,
                            "deletion_cutoff": deletion_cutoff,
                        },
                    )

                    rows = result.fetchall()
                    if not rows:
                        break

                    # Convert to DataFrame for efficient archival
                    df = pd.DataFrame([dict(row._mapping) for row in rows])

                    # Archive the batch
                    archive_success = await self._archive_dataframe(df, table, rule, archive_cutoff)

                    if archive_success:
                        total_archived += len(df)
                        offset += rule.batch_size
                    else:
                        logger.error(f"Failed to archive batch for table {table}")
                        break

                return total_archived

        except Exception as e:
            logger.error(f"Failed to archive data from {table}: {e}")
            return 0

    async def _archive_dataframe(
        self,
        df: pd.DataFrame,
        table: str,
        rule: RetentionRule,
        archive_date: datetime,
    ) -> bool:
        """Archive a DataFrame to storage.

        Parameters
        ----------
        df : pd.DataFrame
            Data to archive
        table : str
            Source table name
        rule : RetentionRule
            Retention rule
        archive_date : datetime
            Archive date for file naming

        Returns
        -------
        bool
            True if archival was successful
        """
        try:
            # Create archive directory structure
            archive_dir = (
                self.base_archive_path / rule.policy.value / table / archive_date.strftime("%Y/%m")
            )
            archive_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename
            filename = f"{table}_{archive_date.strftime('%Y%m%d_%H%M%S')}"

            if rule.compression_format == CompressionFormat.PARQUET:
                filepath = archive_dir / f"{filename}.parquet"
                df.to_parquet(filepath, compression="snappy", index=False)

            elif rule.compression_format == CompressionFormat.GZIP_CSV:
                filepath = archive_dir / f"{filename}.csv.gz"
                df.to_csv(filepath, compression="gzip", index=False)

            elif rule.compression_format == CompressionFormat.ZSTD:
                filepath = archive_dir / f"{filename}.csv.zst"
                df.to_csv(filepath, compression="zstd", index=False)

            elif rule.compression_format == CompressionFormat.LZMA:
                filepath = archive_dir / f"{filename}.csv.xz"
                df.to_csv(filepath, compression="xz", index=False)

            # Update statistics
            file_size_mb = filepath.stat().st_size / (1024 * 1024)
            self.stats["archive_size_mb"] += file_size_mb

            logger.debug(f"Archived {len(df)} records to {filepath} ({file_size_mb:.2f} MB)")
            return True

        except Exception as e:
            logger.error(f"Failed to archive DataFrame: {e}")
            return False

    async def _delete_old_data(
        self,
        table: str,
        rule: RetentionRule,
        deletion_cutoff: datetime,
    ) -> int:
        """Delete old data from a table.

        Parameters
        ----------
        table : str
            Table name
        rule : RetentionRule
            Retention rule
        deletion_cutoff : datetime
            Delete data older than this

        Returns
        -------
        int
            Number of records deleted
        """
        try:
            async with self.storage._get_async_session() as session:
                # Build deletion query
                base_query = f"""
                    DELETE FROM {table}
                    WHERE timestamp < :deletion_cutoff
                """

                if rule.where_clause:
                    base_query += f" AND ({rule.where_clause})"

                # Execute deletion
                result = await session.execute(
                    text(base_query),
                    {
                        "deletion_cutoff": deletion_cutoff,
                    },
                )

                await session.commit()
                deleted_count = cast(Any, result).rowcount or 0

                if deleted_count > 0:
                    logger.debug(f"Deleted {deleted_count} records from {table}")

                return deleted_count

        except Exception as e:
            logger.error(f"Failed to delete old data from {table}: {e}")
            return 0

    async def _cleanup_loop(self, interval: float) -> None:
        """Background cleanup loop.

        Parameters
        ----------
        interval : float
            Cleanup interval in seconds
        """
        while self._running:
            try:
                await self.run_cleanup_cycle()
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(60.0)  # Wait 1 minute on error

    def add_retention_rule(self, rule: RetentionRule) -> None:
        """Add a custom retention rule.

        Parameters
        ----------
        rule : RetentionRule
            Retention rule to add
        """
        self.retention_rules.append(rule)
        logger.info(f"Added retention rule: {rule.name}")

    def remove_retention_rule(self, rule_name: str) -> bool:
        """Remove a retention rule by name.

        Parameters
        ----------
        rule_name : str
            Name of rule to remove

        Returns
        -------
        bool
            True if rule was removed
        """
        for i, rule in enumerate(self.retention_rules):
            if rule.name == rule_name:
                del self.retention_rules[i]
                logger.info(f"Removed retention rule: {rule_name}")
                return True
        return False

    def get_retention_statistics(self) -> RetentionStats:
        """Get retention and archival statistics.

        Returns
        -------
        RetentionStats
            Statistics dictionary
        """
        return self.stats.copy()

    async def estimate_cleanup_impact(self) -> ImpactResult:
        """Estimate the impact of running cleanup (for planning).

        Returns
        -------
        ImpactResult
            Estimated cleanup impact
        """
        impact: ImpactResult = {
            "estimated_deletions": {},
            "estimated_archives": {},
            "total_size_affected": 0,
        }

        try:
            async with self.storage._get_async_session() as session:
                for rule in self.retention_rules:
                    if not rule.enabled:
                        continue

                    tables = await self._get_matching_tables(rule.table_pattern)

                    for table in tables:
                        # Estimate deletions
                        deletion_cutoff = datetime.now(UTC) - rule.retention_period

                        query = text(
                            f"""
                            SELECT COUNT(*) as count,
                                   pg_total_relation_size('{table}') as table_size
                            FROM {table}
                            WHERE timestamp < :deletion_cutoff
                            {f"AND ({rule.where_clause})" if rule.where_clause else ""}
                        """
                        )

                        result = await session.execute(
                            query,
                            {
                                "deletion_cutoff": deletion_cutoff,
                            },
                        )

                        row = result.first()
                        if row and row[0] > 0:
                            impact["estimated_deletions"][f"{table}_{rule.name}"] = {
                                "records": row[0],
                                "table_size": row.table_size,
                            }

        except Exception as e:
            logger.error(f"Failed to estimate cleanup impact: {e}")

        return impact
