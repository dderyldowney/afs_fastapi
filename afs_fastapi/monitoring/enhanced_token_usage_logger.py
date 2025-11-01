"""
Enhanced token usage logger with connection pooling and performance optimization.

This module provides improved token usage tracking with:
- Connection pooling for high-performance operations
- Async database operations for non-blocking logging
- Performance monitoring and optimization
- Agricultural workload optimizations
- Automatic failover and recovery

Implementation follows Test-First Development (TDD) GREEN phase.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import sessionmaker

from afs_fastapi.database.optimized_db_config import get_optimized_db_config
from afs_fastapi.monitoring.token_usage_models import Base, TokenUsage
from afs_fastapi.monitoring.token_usage_repository import TokenUsageRepository

# Configure logging for enhanced token usage logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class EnhancedTokenUsageLogger:
    """Enhanced token usage logger with connection pooling and optimization.

    This improved version provides:
    - Unified connection pooling with the main database system
    - Async operations for non-blocking performance
    - Performance monitoring and health checks
    - Agricultural workload-specific optimizations
    - Automatic failover and recovery capabilities
    """

    _instance = None
    _initialized = False

    def __init__(self, database_url: str | None = None, log_level: int = logging.INFO) -> None:
        """Initialize enhanced token usage logger.

        Parameters
        ----------
        database_url : Optional[str], default None
            Database URL (uses environment if None)
        log_level : int, default logging.INFO
            Logging level for the logger
        """
        self.database_url = database_url or os.getenv(
            "TOKEN_USAGE_DATABASE_URL", "sqlite:///token_usage.db"
        )
        self.log_level = log_level
        self._async_engine: AsyncEngine | None = None
        self._SessionLocal: sessionmaker | None = None

        # Performance tracking
        self._performance_metrics = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "avg_operation_time": 0.0,
            "async_operations": 0,
            "sync_operations": 0,
        }

        self.set_logging_level(log_level)
        logger.info("Enhanced TokenUsageLogger initialized")

    @classmethod
    def reset_for_testing(cls, database_url: str) -> EnhancedTokenUsageLogger:
        """Reset singleton instance for testing with optimized configuration.

        This method is intended for testing only. It allows tests to reinitialize
        the singleton with a test database URL, ensuring test isolation with
        enhanced connection pooling.

        Parameters
        ----------
        database_url : str
            Database URL for test database

        Returns
        -------
        EnhancedTokenUsageLogger
            Instance configured with test database and pooling

        Agricultural Context: Test isolation critical for validating token usage
        tracking in agricultural robotics CI/CD pipelines with optimized
        connection pooling for performance testing.
        """
        # Create engine with connection pooling
        engine = create_engine(database_url, echo=False, pool_size=5, pool_pre_ping=True)

        # Create session factory with connection pooling
        SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
        )

        # Create tables with optimized schema
        Base.metadata.create_all(bind=engine)

        cls._instance = cls(database_url=database_url)
        cls._initialized = True

        # Update the global token_logger instance for API usage
        global token_logger
        token_logger = cls._instance

        return cls._instance

    def set_logging_level(self, level: int) -> None:
        """Sets the logging level for the EnhancedTokenUsageLogger."""
        logger.setLevel(level)

    async def log_token_usage_optimized(
        self,
        agent_id: str,
        task_id: str,
        tokens_used: float,
        model_name: str,
        timestamp: datetime | None = None,
        use_async: bool = True,
    ) -> bool:
        """Log token usage with optimized performance and connection pooling.

        Parameters
        ----------
        agent_id : str
            Agent identifier
        task_id : str
            Task identifier
        tokens_used : float
            Number of tokens used
        model_name : str
            Model name for the operation
        timestamp : Optional[datetime], default None
            Timestamp for the usage (uses current time if None)
        use_async : bool, default True
            Use async database operations

        Returns
        -------
        bool
            True if logging successful
        """
        if timestamp is None:
            timestamp = datetime.now(UTC)

        log_entry = {
            "id": str(uuid.uuid4()),
            "agent_id": agent_id,
            "task_id": task_id,
            "tokens_used": tokens_used,
            "model_name": model_name,
            "timestamp": timestamp,
        }

        start_time = time.time()
        self._performance_metrics["total_operations"] += 1

        try:
            if use_async:
                await self._perform_log_async(log_entry)
                self._performance_metrics["async_operations"] += 1
            else:
                self._perform_log_sync(log_entry)
                self._performance_metrics["sync_operations"] += 1

            self._performance_metrics["successful_operations"] += 1
            self._update_operation_performance(start_time, False)

            logger.debug(f"Logged token usage: {log_entry}")
            return True

        except Exception as e:
            self._performance_metrics["failed_operations"] += 1
            self._update_operation_performance(start_time, True)
            logger.error(f"Failed to log token usage: {e}", exc_info=True)
            return False

    async def _perform_log_async(self, log_entry: dict[str, Any]) -> None:
        """Asynchronously perform database logging with connection pooling.

        Parameters
        ----------
        log_entry : dict[str, Any]
            Token usage log entry
        """
        try:
            # Try to use optimized database configuration first
            try:
                db_config = await get_optimized_db_config()
                async with db_config.get_session() as session:
                    repository = TokenUsageRepository(session)
                    await asyncio.to_thread(repository.create, log_entry)
                    await session.commit()
                    return
            except (RuntimeError, AttributeError):
                # Fall back to direct database connection if optimized config not available
                logger.debug("Optimized DB config not available, using direct connection")
                pass

            # Use asyncio.to_thread with sync operations for the repository
            await asyncio.to_thread(self._perform_log_sync_fallback, log_entry)

        except Exception as e:
            logger.error(f"Async logging failed: {e}")
            raise

    def _perform_log_sync_fallback(self, log_entry: dict[str, Any]) -> None:
        """Fallback sync logging for async operations using to_thread.

        Parameters
        ----------
        log_entry : dict[str, Any]
            Token usage log entry
        """
        # Convert async database URL to sync URL
        sync_db_url = self.database_url.replace("+aiosqlite", "")

        # Create sync engine
        engine = create_engine(sync_db_url, echo=False, pool_pre_ping=True)

        SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
        )

        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)

        # Perform the logging operation
        with SessionLocal() as session:
            repository = TokenUsageRepository(session)
            repository.create(log_entry)

        engine.dispose()

    def _perform_log_sync(self, log_entry: dict[str, Any]) -> None:
        """Synchronously perform database logging with connection pooling.

        Parameters
        ----------
        log_entry : dict[str, Any]
            Token usage log entry
        """
        try:
            # Create engine with connection pooling (skip pool settings for SQLite)
            engine_kwargs = {"echo": False}
            if not self.database_url.startswith("sqlite"):
                engine_kwargs.update({"pool_size": 5, "pool_pre_ping": True, "pool_recycle": 3600})

            engine = create_engine(self.database_url, **engine_kwargs)

            SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
            )

            with SessionLocal() as session:
                repository = TokenUsageRepository(session)
                repository.create(log_entry)
                session.commit()

        except Exception as e:
            logger.error(f"Sync logging failed: {e}")
            raise

    async def query_token_usage_optimized(
        self,
        agent_id: str | None = None,
        task_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        use_async: bool = True,
    ) -> list[TokenUsage]:
        """Query token usage data with optimized performance.

        Parameters
        ----------
        agent_id : Optional[str], default None
            Filter by agent ID
        task_id : Optional[str], default None
            Filter by task ID
        start_time : Optional[datetime], default None
            Filter by start time
        end_time : Optional[datetime], default None
            Filter by end time
        use_async : bool, default True
            Use async database operations

        Returns
        -------
        list[TokenUsage]
            Query results
        """
        start_time_query = time.time()
        self._performance_metrics["total_operations"] += 1

        try:
            if use_async:
                results = await self._perform_query_async(agent_id, task_id, start_time, end_time)
                self._performance_metrics["async_operations"] += 1
            else:
                results = self._perform_query_sync(agent_id, task_id, start_time, end_time)
                self._performance_metrics["sync_operations"] += 1

            self._performance_metrics["successful_operations"] += 1
            self._update_operation_performance(start_time_query, False)

            return results

        except Exception as e:
            self._performance_metrics["failed_operations"] += 1
            self._update_operation_performance(start_time_query, True)
            logger.error(f"Failed to query token usage: {e}")
            return []

    async def _perform_query_async(
        self,
        agent_id: str | None,
        task_id: str | None,
        start_time: datetime | None,
        end_time: datetime | None,
    ) -> list[TokenUsage]:
        """Asynchronously perform database query with connection pooling.

        Parameters
        ----------
        agent_id : Optional[str]
            Filter by agent ID
        task_id : Optional[str]
            Filter by task ID
        start_time : Optional[datetime]
            Filter by start time
        end_time : Optional[datetime]
            Filter by end time

        Returns
        -------
        list[TokenUsage]
            Query results
        """
        try:
            # Try to use optimized database configuration first
            try:
                db_config = await get_optimized_db_config()
                async with db_config.get_session() as session:
                    repository = TokenUsageRepository(session)
                    return await asyncio.to_thread(
                        repository.query, agent_id, task_id, start_time, end_time
                    )
            except (RuntimeError, AttributeError):
                # Fall back to direct database connection if optimized config not available
                logger.debug("Optimized DB config not available, using direct connection")
                pass

            # Use asyncio.to_thread with sync operations for the repository
            return await asyncio.to_thread(
                self._perform_query_sync_fallback, agent_id, task_id, start_time, end_time
            )

        except Exception as e:
            logger.error(f"Async query failed: {e}")
            raise

    def _perform_query_sync_fallback(
        self,
        agent_id: str | None,
        task_id: str | None,
        start_time: datetime | None,
        end_time: datetime | None,
    ) -> list[TokenUsage]:
        """Fallback sync query for async operations using to_thread.

        Parameters
        ----------
        agent_id : Optional[str]
            Filter by agent ID
        task_id : Optional[str]
            Filter by task ID
        start_time : Optional[datetime]
            Filter by start time
        end_time : Optional[datetime]
            Filter by end time

        Returns
        -------
        list[TokenUsage]
            Query results
        """
        # Convert async database URL to sync URL
        sync_db_url = self.database_url.replace("+aiosqlite", "")

        # Create sync engine
        engine = create_engine(sync_db_url, echo=False, pool_pre_ping=True)

        SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
        )

        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)

        # Perform the query operation
        with SessionLocal() as session:
            repository = TokenUsageRepository(session)
            results = repository.query(agent_id, task_id, start_time, end_time)

        engine.dispose()
        return results

    def _perform_query_sync(
        self,
        agent_id: str | None,
        task_id: str | None,
        start_time: datetime | None,
        end_time: datetime | None,
    ) -> list[TokenUsage]:
        """Synchronously perform database query with connection pooling.

        Parameters
        ----------
        agent_id : Optional[str]
            Filter by agent ID
        task_id : Optional[str]
            Filter by task ID
        start_time : Optional[datetime]
            Filter by start time
        end_time : Optional[datetime]
            Filter by end time

        Returns
        -------
        list[TokenUsage]
            Query results
        """
        try:
            # Create engine with connection pooling
            engine = create_engine(
                self.database_url, echo=False, pool_size=5, pool_pre_ping=True, pool_recycle=3600
            )

            SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
            )

            with SessionLocal() as session:
                repository = TokenUsageRepository(session)
                return repository.query(agent_id, task_id, start_time, end_time)

        except Exception as e:
            logger.error(f"Sync query failed: {e}")
            raise

    async def prune_old_logs_optimized(
        self, days_to_keep: int = 30, use_async: bool = True
    ) -> bool:
        """Prune old token usage logs with optimized performance.

        Parameters
        ----------
        days_to_keep : int, default 30
            Number of days to keep logs
        use_async : bool, default True
            Use async database operations

        Returns
        -------
        bool
            True if pruning successful
        """
        cutoff_date = datetime.now(UTC) - timedelta(days=days_to_keep)
        start_time = time.time()

        self._performance_metrics["total_operations"] += 1

        try:
            if use_async:
                await self._perform_prune_async(cutoff_date)
                self._performance_metrics["async_operations"] += 1
            else:
                self._perform_prune_sync(cutoff_date)
                self._performance_metrics["sync_operations"] += 1

            self._performance_metrics["successful_operations"] += 1
            self._update_operation_performance(start_time, False)

            logger.info(f"Pruned token usage logs older than {days_to_keep} days.")
            return True

        except Exception as e:
            self._performance_metrics["failed_operations"] += 1
            self._update_operation_performance(start_time, True)
            logger.error(f"Failed to prune old token usage logs: {e}", exc_info=True)
            return False

    async def _perform_prune_async(self, cutoff_date: datetime) -> None:
        """Asynchronously perform database pruning with connection pooling.

        Parameters
        ----------
        cutoff_date : datetime
            Cutoff date for pruning
        """
        try:
            # Try to use optimized database configuration first
            try:
                db_config = await get_optimized_db_config()
                async with db_config.get_session() as session:
                    repository = TokenUsageRepository(session)
                    await asyncio.to_thread(repository.delete_old_logs, cutoff_date)
                    await session.commit()
                    return
            except (RuntimeError, AttributeError):
                # Fall back to direct database connection if optimized config not available
                logger.debug("Optimized DB config not available, using direct connection")
                pass

            # Use asyncio.to_thread with sync operations for the repository
            await asyncio.to_thread(self._perform_prune_sync_fallback, cutoff_date)

        except Exception as e:
            logger.error(f"Async pruning failed: {e}")
            raise

    def _perform_prune_sync_fallback(self, cutoff_date: datetime) -> None:
        """Fallback sync pruning for async operations using to_thread.

        Parameters
        ----------
        cutoff_date : datetime
            Cutoff date for pruning
        """
        # Convert async database URL to sync URL
        sync_db_url = self.database_url.replace("+aiosqlite", "")

        # Create sync engine
        engine = create_engine(sync_db_url, echo=False, pool_pre_ping=True)

        SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
        )

        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)

        # Perform the pruning operation
        with SessionLocal() as session:
            repository = TokenUsageRepository(session)
            repository.delete_old_logs(cutoff_date)

        engine.dispose()

    def _perform_prune_sync(self, cutoff_date: datetime) -> None:
        """Synchronously perform database pruning with connection pooling.

        Parameters
        ----------
        cutoff_date : datetime
            Cutoff date for pruning
        """
        try:
            # Create engine with connection pooling
            engine = create_engine(
                self.database_url, echo=False, pool_size=5, pool_pre_ping=True, pool_recycle=3600
            )

            SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
            )

            with SessionLocal() as session:
                repository = TokenUsageRepository(session)
                repository.delete_old_logs(cutoff_date)
                session.commit()

        except Exception as e:
            logger.error(f"Sync pruning failed: {e}")
            raise

    def _update_operation_performance(self, start_time: float, is_error: bool) -> None:
        """Update operation performance metrics.

        Parameters
        ----------
        start_time : float
            Operation start timestamp
        is_error : bool
            Whether the operation resulted in an error
        """
        operation_time = time.time() - start_time

        # Update average operation time
        total_time = self._performance_metrics["avg_operation_time"] * (
            self._performance_metrics["total_operations"] - 1
        )
        self._performance_metrics["avg_operation_time"] = (
            total_time + operation_time
        ) / self._performance_metrics["total_operations"]

        # Track error rate
        if is_error:
            error_rate = self._performance_metrics["failed_operations"] / max(
                self._performance_metrics["total_operations"], 1
            )
            if error_rate > 0.1:  # 10% error threshold
                logger.warning(f"High error rate detected: {error_rate:.2%}")

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get comprehensive performance metrics.

        Returns
        -------
        dict[str, Any]
            Performance metrics and statistics
        """
        total_ops = self._performance_metrics["total_operations"]
        success_rate = self._performance_metrics["successful_operations"] / max(total_ops, 1) * 100

        return {
            "performance_metrics": self._performance_metrics.copy(),
            "success_rate": success_rate,
            "error_rate": (
                self._performance_metrics["failed_operations"] / max(total_ops, 1) * 100
            ),
            "async_ratio": (
                self._performance_metrics["async_operations"] / max(total_ops, 1) * 100
            ),
            "sync_ratio": (self._performance_metrics["sync_operations"] / max(total_ops, 1) * 100),
        }

    def log_performance_report(self) -> None:
        """Log comprehensive performance report."""
        metrics = self.get_performance_metrics()

        logger.info("📊 Enhanced Token Usage Logger Performance Report:")
        logger.info(f"   Total Operations: {metrics['performance_metrics']['total_operations']}")
        logger.info(f"   Success Rate: {metrics['success_rate']:.1f}%")
        logger.info(f"   Error Rate: {metrics['error_rate']:.1f}%")
        logger.info(
            f"   Average Operation Time: {metrics['performance_metrics']['avg_operation_time']:.3f}s"
        )
        logger.info(f"   Async Operations: {metrics['async_ratio']:.1f}%")
        logger.info(f"   Sync Operations: {metrics['sync_ratio']:.1f}%")

        # Performance recommendations
        if metrics["error_rate"] > 5:
            logger.warning("⚠️ High error rate detected - investigate database connectivity")

        if metrics["performance_metrics"]["avg_operation_time"] > 0.1:
            logger.warning(
                "⚠️ Slow operation times detected - consider connection pooling optimization"
            )

        if metrics["async_ratio"] < 80:
            logger.info("💡 Consider using more async operations for better performance")


# Module-level enhanced logger instance for import by other modules
enhanced_token_logger = EnhancedTokenUsageLogger()


def get_enhanced_token_logger() -> EnhancedTokenUsageLogger:
    """Get enhanced token logger instance.

    Returns
    -------
    EnhancedTokenUsageLogger
        Enhanced token logger instance with connection pooling
    """
    return enhanced_token_logger
