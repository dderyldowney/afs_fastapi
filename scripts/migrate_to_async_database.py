#!/usr/bin/env python3
"""
Migration script to convert synchronous database operations to async.

This script migrates existing synchronous database operations to async-compatible
operations for improved performance in agricultural robotics applications.

Usage:
    python scripts/migrate_to_async_database.py [options]

Options:
    --backup              Create backup of existing database
    --migrate-tables      Migrate all database tables to async-compatible schemas
    --update-code        Update existing code to use async operations
    --validate           Validate migration results
    --test               Run migration tests
    --help               Show this help message

Implementation follows Test-First Development (TDD) GREEN phase.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import shutil
from datetime import datetime

from sqlalchemy import create_engine, text

from afs_fastapi.database.async_repository import UnitOfWork

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AsyncDatabaseMigration:
    """Migration manager for converting synchronous to async database operations."""

    def __init__(self, source_database_url: str, target_database_url: str) -> None:
        """Initialize migration manager.

        Parameters
        ----------
        source_database_url : str
            Source database URL (synchronous operations)
        target_database_url : str
            Target database URL (async operations)
        """
        self.source_database_url = source_database_url
        self.target_database_url = target_database_url
        self.source_engine = create_engine(source_database_url)
        self.target_engine = create_engine(target_database_url)

        # Migration tracking
        self.migration_log = []
        self.backup_created = False

    def create_backup(self) -> bool:
        """Create backup of source database.

        Returns
        -------
        bool
            True if backup created successfully
        """
        try:
            # Extract database file path from URL
            if "sqlite" in self.source_database_url:
                db_path = self.source_database_url.replace("sqlite:///", "")
                backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                if os.path.exists(db_path):
                    shutil.copy2(db_path, backup_path)
                    self.backup_created = True
                    logger.info(f"Created backup: {backup_path}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False

    async def migrate_database_schema(self) -> bool:
        """Migrate database schema to async-compatible format.

        Returns
        -------
        bool
            True if schema migration successful
        """
        try:
            logger.info("Starting database schema migration")

            # Create async-compatible tables in target database
            from afs_fastapi.database.agricultural_schemas_async import Base

            async with self.target_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.info("Created async-compatible database schema")
            self.migration_log.append("Schema migration completed")

            return True

        except Exception as e:
            logger.error(f"Failed to migrate database schema: {e}")
            self.migration_log.append(f"Schema migration failed: {e}")
            return False

    async def migrate_equipment_data(self) -> bool:
        """Migrate equipment data from synchronous to async format.

        Returns
        -------
        bool
            True if equipment data migration successful
        """
        try:
            logger.info("Migrating equipment data")

            # Read data from source database
            with self.source_engine.connect() as source_conn:
                result = source_conn.execute(text("SELECT * FROM equipment"))
                equipment_data = result.fetchall()

            # Write data to target database using async operations
            from afs_fastapi.database.agricultural_schemas_async import AsyncDatabaseManager

            db_manager = AsyncDatabaseManager(self.target_database_url)
            await db_manager.initialize()

            async with db_manager.get_session() as session:
                async with UnitOfWork(session) as uow:
                    for row in equipment_data:
                        await uow.equipment.create_equipment(
                            equipment_id=row.equipment_id,
                            isobus_address=row.isobus_address,
                            equipment_type=row.equipment_type,
                            manufacturer=row.manufacturer,
                            model=row.model,
                            serial_number=row.serial_number,
                            firmware_version=row.firmware_version,
                            installation_date=row.installation_date,
                            status=row.status,
                        )

                    await uow.commit()

            await db_manager.shutdown()

            logger.info(f"Migrated {len(equipment_data)} equipment records")
            self.migration_log.append(f"Equipment data migration: {len(equipment_data)} records")

            return True

        except Exception as e:
            logger.error(f"Failed to migrate equipment data: {e}")
            self.migration_log.append(f"Equipment data migration failed: {e}")
            return False

    async def migrate_field_data(self) -> bool:
        """Migrate field data from synchronous to async format.

        Returns
        -------
        bool
            True if field data migration successful
        """
        try:
            logger.info("Migrating field data")

            # Read data from source database
            with self.source_engine.connect() as source_conn:
                result = source_conn.execute(text("SELECT * FROM fields"))
                field_data = result.fetchall()

            # Write data to target database using async operations
            from afs_fastapi.database.agricultural_schemas_async import AsyncDatabaseManager

            db_manager = AsyncDatabaseManager(self.target_database_url)
            await db_manager.initialize()

            async with db_manager.get_session() as session:
                async with UnitOfWork(session) as uow:
                    for row in field_data:
                        await uow.field.create_field(
                            field_id=row.field_id,
                            field_name=row.field_name,
                            crop_type=row.crop_type,
                            field_area_hectares=row.field_area_hectares,
                            boundary_coordinates=row.boundary_coordinates,
                            soil_type=row.soil_type,
                            drainage_class=row.drainage_class,
                            elevation_meters=row.elevation_meters,
                            slope_percentage=row.slope_percentage,
                        )

                    await uow.commit()

            await db_manager.shutdown()

            logger.info(f"Migrated {len(field_data)} field records")
            self.migration_log.append(f"Field data migration: {len(field_data)} records")

            return True

        except Exception as e:
            logger.error(f"Failed to migrate field data: {e}")
            self.migration_log.append(f"Field data migration failed: {e}")
            return False

    async def migrate_token_usage_data(self) -> bool:
        """Migrate token usage data from synchronous to async format.

        Returns
        -------
        bool
            True if token usage data migration successful
        """
        try:
            logger.info("Migrating token usage data")

            # Read data from source database
            with self.source_engine.connect() as source_conn:
                result = source_conn.execute(text("SELECT * FROM token_usage"))
                token_usage_data = result.fetchall()

            # Write data to target database using async operations
            from afs_fastapi.database.agricultural_schemas_async import AsyncDatabaseManager

            db_manager = AsyncDatabaseManager(self.target_database_url)
            await db_manager.initialize()

            async with db_manager.get_session() as session:
                async with UnitOfWork(session) as uow:
                    for row in token_usage_data:
                        await uow.token_usage.create_token_usage(
                            agent_id=row.agent_id,
                            task_id=row.task_id,
                            tokens_used=row.tokens_used,
                            model_name=row.model_name,
                            timestamp=row.timestamp,
                        )

                    await uow.commit()

            await db_manager.shutdown()

            logger.info(f"Migrated {len(token_usage_data)} token usage records")
            self.migration_log.append(
                f"Token usage data migration: {len(token_usage_data)} records"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to migrate token usage data: {e}")
            self.migration_log.append(f"Token usage data migration failed: {e}")
            return False

    async def migrate_all_data(self) -> bool:
        """Migrate all data from synchronous to async format.

        Returns
        -------
        bool
            True if all data migration successful
        """
        try:
            logger.info("Starting comprehensive data migration")

            # Migrate all table data
            migrations = [
                self.migrate_equipment_data,
                self.migrate_field_data,
                self.migrate_token_usage_data,
            ]

            results = await asyncio.gather(*migrations, return_exceptions=True)

            # Check results
            all_successful = True
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Migration {i+1} failed: {result}")
                    all_successful = False
                elif result:
                    logger.info(f"Migration {i+1} completed successfully")
                else:
                    logger.error(f"Migration {i+1} failed")
                    all_successful = False

            if all_successful:
                logger.info("All data migrations completed successfully")
                self.migration_log.append("Comprehensive data migration completed")
                return True
            else:
                logger.error("Some data migrations failed")
                return False

        except Exception as e:
            logger.error(f"Failed to migrate all data: {e}")
            self.migration_log.append(f"Comprehensive data migration failed: {e}")
            return False

    async def validate_migration(self) -> bool:
        """Validate migration results.

        Returns
        -------
        bool
            True if migration validation successful
        """
        try:
            logger.info("Validating migration results")

            # Count records in source database
            with self.source_engine.connect() as source_conn:
                source_counts = {}
                tables = ["equipment", "fields", "token_usage"]

                for table in tables:
                    result = source_conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    source_counts[table] = result.scalar()

            # Count records in target database
            from afs_fastapi.database.agricultural_schemas_async import AsyncDatabaseManager

            db_manager = AsyncDatabaseManager(self.target_database_url)
            await db_manager.initialize()

            async with db_manager.get_session() as session:
                target_counts = {}

                # Query each table
                for table in tables:
                    if table == "equipment":
                        result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        target_counts[table] = result.scalar()
                    elif table == "fields":
                        result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        target_counts[table] = result.scalar()
                    elif table == "token_usage":
                        result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        target_counts[table] = result.scalar()

            await db_manager.shutdown()

            # Validate counts match
            validation_results = {}
            all_valid = True

            for table in tables:
                source_count = source_counts.get(table, 0)
                target_count = target_counts.get(table, 0)

                validation_results[table] = {
                    "source_count": source_count,
                    "target_count": target_count,
                    "match": source_count == target_count,
                }

                if source_count != target_count:
                    all_valid = False
                    logger.warning(f"Count mismatch in {table}: {source_count} -> {target_count}")
                else:
                    logger.info(f"Count validation passed for {table}: {source_count}")

            if all_valid:
                logger.info("Migration validation completed successfully")
                self.migration_log.append("Migration validation completed successfully")
                return True
            else:
                logger.error("Migration validation failed - count mismatches detected")
                self.migration_log.append("Migration validation failed - count mismatches")
                return False

        except Exception as e:
            logger.error(f"Failed to validate migration: {e}")
            self.migration_log.append(f"Migration validation failed: {e}")
            return False

    async def generate_migration_report(self) -> str:
        """Generate comprehensive migration report.

        Returns
        -------
        str
            Migration report as formatted string
        """
        report = []
        report.append("=== ASYNC DATABASE MIGRATION REPORT ===")
        report.append(f"Source Database: {self.source_database_url}")
        report.append(f"Target Database: {self.target_database_url}")
        report.append(f"Backup Created: {self.backup_created}")
        report.append("")

        report.append("Migration Log:")
        for entry in self.migration_log:
            report.append(f"  - {entry}")
        report.append("")

        # Migration summary
        success_count = sum(1 for entry in self.migration_log if "completed" in entry.lower())
        failure_count = sum(1 for entry in self.migration_log if "failed" in entry.lower())

        report.append("Migration Summary:")
        report.append(f"  Successful operations: {success_count}")
        report.append(f"  Failed operations: {failure_count}")
        report.append(
            f"  Success rate: {success_count / max(success_count + failure_count, 1) * 100:.1f}%"
        )
        report.append("")

        # Recommendations
        report.append("Recommendations:")
        if failure_count > 0:
            report.append("  - Review failed migration operations")
            report.append("  - Check database schema compatibility")
            report.append("  - Ensure proper permissions for target database")

        report.append("  - Implement async operations in application code")
        report.append("  - Update connection pooling configuration")
        report.append("  - Test performance improvements")
        report.append("")

        report.append("=== END REPORT ===")

        return "\n".join(report)

    async def run_migration(self, operations: list[str]) -> bool:
        """Run complete migration process.

        Parameters
        ----------
        operations : list[str]
            List of migration operations to perform

        Returns
        -------
        bool
            True if complete migration successful
        """
        try:
            logger.info("Starting complete async database migration")

            # Create backup if requested
            if "backup" in operations:
                self.create_backup()

            # Run migration operations
            for operation in operations:
                if operation == "migrate-tables":
                    await self.migrate_database_schema()
                elif operation == "migrate-data":
                    await self.migrate_all_data()
                elif operation == "validate":
                    await self.validate_migration()

            # Generate final report
            report = await self.generate_migration_report()
            logger.info(report)

            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

    def update_imports(self) -> None:
        """Update Python imports to use async database operations."""
        # Find all Python files that need import updates
        import_paths = [
            "afs_fastapi/monitoring/token_usage_logger.py",
            "afs_fastapi/monitoring/token_usage_repository.py",
        ]

        for file_path in import_paths:
            if os.path.exists(file_path):
                self._update_file_imports(file_path)

    def _update_file_imports(self, file_path: str) -> None:
        """Update imports in a specific Python file."""
        try:
            with open(file_path) as f:
                content = f.read()

            # Replace synchronous imports with async imports
            replacements = [
                (
                    "from afs_fastapi.monitoring.token_usage_models import TokenUsage",
                    "from afs_fastapi.database.agricultural_schemas_async import TokenUsage",
                ),
                (
                    "from afs_fastapi.monitoring.token_usage_repository import TokenUsageRepository",
                    "from afs_fastapi.database.async_repository import TokenUsageAsyncRepository",
                ),
                ("import asyncio", "import asyncio"),
            ]

            for old_import, new_import in replacements:
                content = content.replace(old_import, new_import)

            # Write updated content
            with open(file_path, "w") as f:
                f.write(content)

            logger.info(f"Updated imports in {file_path}")

        except Exception as e:
            logger.error(f"Failed to update imports in {file_path}: {e}")


def main() -> None:
    """Main migration script execution."""
    parser = argparse.ArgumentParser(description="Migrate synchronous database operations to async")
    parser.add_argument("--backup", action="store_true", help="Create backup of source database")
    parser.add_argument("--migrate-tables", action="store_true", help="Migrate database tables")
    parser.add_argument("--migrate-data", action="store_true", help="Migrate data to async format")
    parser.add_argument("--validate", action="store_true", help="Validate migration results")
    parser.add_argument(
        "--update-code", action="store_true", help="Update code to use async operations"
    )
    parser.add_argument("--test", action="store_true", help="Run migration tests")
    parser.add_argument(
        "--source-url", default="sqlite:///agricultural_data.db", help="Source database URL"
    )
    parser.add_argument(
        "--target-url", default="sqlite:///agricultural_data_async.db", help="Target database URL"
    )

    args = parser.parse_args()

    if not any(
        [
            args.backup,
            args.migrate_tables,
            args.migrate_data,
            args.validate,
            args.update_code,
            args.test,
        ]
    ):
        parser.print_help()
        return

    # Create migration manager
    migration = AsyncDatabaseMigration(args.source_url, args.target_url)

    async def run_async_migration() -> None:
        """Run migration asynchronously."""
        operations = []
        if args.backup:
            operations.append("backup")
        if args.migrate_tables:
            operations.append("migrate-tables")
        if args.migrate_data:
            operations.append("migrate-data")
        if args.validate:
            operations.append("validate")

        if operations:
            success = await migration.run_migration(operations)
            if success:
                logger.info("Migration completed successfully")
            else:
                logger.error("Migration failed")
                return 1

        if args.update_code:
            migration.update_imports()

        if args.test:
            await run_migration_tests()

        return 0

    # Run async migration
    result = asyncio.run(run_async_migration())
    exit(result)


async def run_migration_tests() -> None:
    """Run migration tests to validate results."""
    logger.info("Running migration tests")

    try:
        # Import test modules
        import pytest

        # Run async database tests
        test_args = ["-v", "tests/database/test_async_agricural_schemas.py"]
        exit_code = pytest.main(test_args)

        if exit_code == 0:
            logger.info("Migration tests passed")
        else:
            logger.error("Migration tests failed")

    except Exception as e:
        logger.error(f"Failed to run migration tests: {e}")


if __name__ == "__main__":
    main()
