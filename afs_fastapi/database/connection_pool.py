"""
Enhanced connection pooling system for PostgreSQL/TimescaleDB optimization.

This module provides a unified, high-performance connection pooling system
designed specifically for agricultural robotics data patterns, including
connection health monitoring, automatic failover, and optimized performance
for time-series data operations.

Implementation follows Test-First Development (TDD) GREEN phase.
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)


class ConnectionHealthStatus(Enum):
    """Connection health monitoring status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    RECONNECTING = "reconnecting"


@dataclass
class PoolConfiguration:
    """Configuration for optimized database connection pooling."""

    # Basic pool settings
    max_connections: int = 50
    min_connections: int = 5
    pool_timeout: float = 30.0
    pool_recycle: int = 3600  # Recycle connections after 1 hour

    # Performance optimization
    pool_pre_ping: bool = True
    pool_size: int = 20
    max_overflow: int = 10

    # Time-series specific settings
    enable_hypertable: bool = True
    enable_compression: bool = True
    batch_size: int = 1000

    # Health monitoring
    health_check_interval: float = 60.0
    connection_timeout: float = 5.0
    retry_attempts: int = 3

    # Agricultural-specific optimizations
    agricultural_pgns: list[int] = None
    compression_threshold: int = 1000

    def __post_init__(self) -> None:
        """Set default agricultural PGNs if not provided."""
        if self.agricultural_pgns is None:
            self.agricultural_pgns = [
                61444,  # Tractor data
                65265,  # Vehicle speed
                65266,  # Wheel-based speed
                65267,  # Distance traveled
                65271,  # Torque
                65272,  # Power take-off
                130312,  # GNSS position data
                130313,  # GNSS quality data
            ]


class ConnectionHealthMonitor:
    """Monitors connection health and performance metrics."""

    def __init__(self, pool: QueuePool, config: PoolConfiguration, engine: AsyncEngine) -> None:
        """Initialize connection health monitor.

        Parameters
        ----------
        pool : QueuePool
            SQLAlchemy connection pool
        config : PoolConfiguration
            Pool configuration
        engine : AsyncEngine
            Database engine instance
        """
        self.pool = pool
        self.config = config
        self.engine = engine
        self._health_status = ConnectionHealthStatus.HEALTHY
        self._last_health_check = 0.0
        self._health_metrics = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "avg_response_time": 0.0,
            "last_check_time": 0.0,
        }

    async def check_health(self) -> ConnectionHealthStatus:
        """Perform comprehensive health check on connections.

        Returns
        -------
        ConnectionHealthStatus
            Current health status of the connection pool
        """
        current_time = time.time()

        # Skip if health check was performed recently
        if current_time - self._last_health_check < self.config.health_check_interval:
            return self._health_status

        self._last_health_check = current_time

        try:
            # Test basic connectivity
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                self._health_status = ConnectionHealthStatus.HEALTHY

            # Update pool metrics
            self._update_pool_metrics()

            logger.debug("Connection health check passed")
            return self._health_status

        except Exception as e:
            logger.warning(f"Connection health check failed: {e}")
            self._health_status = (
                ConnectionHealthStatus.DEGRADED
                if self._health_status == ConnectionHealthStatus.HEALTHY
                else ConnectionHealthStatus.UNHEALTHY
            )

            # Attempt to recover
            await self._attempt_recovery()

            return self._health_status

    def _update_pool_metrics(self) -> None:
        """Update connection pool performance metrics."""
        self._health_metrics.update(
            {
                "total_connections": self.pool.size(),
                "active_connections": getattr(self.pool, "_checkedout", 0),
                "failed_connections": getattr(self.pool, "_invalidated", 0),
                "last_check_time": time.time(),
            }
        )

    async def _attempt_recovery(self) -> None:
        """Attempt to recover from connection pool issues."""
        logger.info("Attempting connection pool recovery")

        try:
            # Clear potentially bad connections
            if hasattr(self.pool, "dispose"):
                self.pool.dispose()

            # Recreate pool
            self._health_status = ConnectionHealthStatus.RECONNECTING

        except Exception as e:
            logger.error(f"Connection pool recovery failed: {e}")
            self._health_status = ConnectionHealthStatus.UNHEALTHY


class AgriculturalConnectionPool:
    """Unified connection pooling system optimized for agricultural data patterns.

    This class provides intelligent connection management specifically designed
    for agricultural robotics workloads including:
    - High-frequency CAN message storage
    - Time-series data aggregation
    - Equipment telemetry tracking
    - Farm operation analytics
    """

    def __init__(self, database_url: str, config: PoolConfiguration | None = None) -> None:
        """Initialize agricultural connection pool.

        Parameters
        ----------
        database_url : str
            PostgreSQL database connection URL
        config : Optional[PoolConfiguration], default None
            Pool configuration (uses defaults if None)
        """
        self.database_url = database_url
        self.config = config or PoolConfiguration()
        self._async_engine: AsyncEngine | None = None
        self._sync_engine: Engine | None = None
        self._async_session_factory: async_sessionmaker[AsyncSession] | None = None
        self._sync_session_factory: sessionmaker[Session] | None = None
        self._health_monitor: ConnectionHealthMonitor | None = None
        self._initialized = False

        # Performance tracking
        self._performance_metrics = {
            "total_queries": 0,
            "slow_queries": 0,
            "avg_query_time": 0.0,
            "connection_acquisitions": 0,
            "connection_failures": 0,
        }

    async def initialize(self) -> bool:
        """Initialize the connection pool with optimized settings.

        Returns
        -------
        bool
            True if initialization successful
        """
        try:
            # Create async engine with optimized pooling
            # Note: async engines use different pooling strategy
            # For SQLite/aiosqlite, we let the driver handle pooling
            if "sqlite" in self.database_url:
                self._async_engine = create_async_engine(
                    self.database_url,
                    echo=False,  # Set to True for debugging
                    future=True,
                    connect_args={"check_same_thread": False},
                )
            else:
                # For PostgreSQL with asyncpg, we can use pooling
                # asyncpg doesn't support connect_timeout parameter
                connect_args = {}
                if "asyncpg" not in self.database_url:
                    connect_args = {"connect_timeout": self.config.connection_timeout}

                self._async_engine = create_async_engine(
                    self.database_url,
                    pool_size=self.config.pool_size,
                    max_overflow=self.config.max_overflow,
                    pool_timeout=self.config.pool_timeout,
                    pool_recycle=self.config.pool_recycle,
                    pool_pre_ping=self.config.pool_pre_ping,
                    echo=False,  # Set to True for debugging
                    future=True,
                    connect_args=connect_args,
                )

            # Create sync engine for schema operations
            if "sqlite" in self.database_url:
                sync_url = self.database_url.replace("+aiosqlite", "")
            else:
                sync_url = self.database_url.replace("+asyncpg", "")
            # sync engine connection args depend on database type
            if "sqlite" in sync_url:
                # SQLite doesn't support connect_timeout
                sync_connect_args = {"check_same_thread": False}
            else:
                # PostgreSQL supports connect_timeout
                sync_connect_args = {"connect_timeout": self.config.connection_timeout}

            self._sync_engine = create_engine(
                sync_url,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=self.config.pool_pre_ping,
                echo=False,
                poolclass=QueuePool,
                connect_args=sync_connect_args,
            )

            # Create optimized session factories
            self._async_session_factory = async_sessionmaker(
                self._async_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
            )

            self._sync_session_factory = sessionmaker(
                self._sync_engine, expire_on_commit=False, autoflush=False
            )

            # Initialize health monitoring
            if self._async_engine.pool:
                self._health_monitor = ConnectionHealthMonitor(
                    self._async_engine.pool, self.config, self._async_engine
                )

            # Verify connectivity
            if self._async_session_factory:
                async with self._async_session_factory() as session:
                    await session.execute(text("SELECT 1"))

            self._initialized = True
            logger.info("Agricultural connection pool initialized successfully")
            logger.info(
                f"Pool configuration: {self.config.max_connections} max, {self.config.min_connections} min connections"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to initialize agricultural connection pool: {e}")
            return False

    async def shutdown(self) -> None:
        """Shutdown the connection pool gracefully."""
        if self._async_engine:
            await self._async_engine.dispose()

        if self._sync_engine:
            self._sync_engine.dispose()

        self._initialized = False
        logger.info("Agricultural connection pool shut down")

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an optimized async database session with connection pooling.

        Yields
        ------
        AsyncSession
            Database session with connection pooling and health monitoring

        Raises
        ------
        Exception
            If connection acquisition fails
        """
        if not self._initialized or not self._async_session_factory:
            raise RuntimeError("Connection pool not initialized")

        start_time = time.time()

        try:
            # Check health before acquiring connection
            if self._health_monitor:
                await self._health_monitor.check_health()

            session = self._async_session_factory()
            self._performance_metrics["connection_acquisitions"] += 1

            logger.debug("Acquired async database session from pool")

            try:
                yield session
            except Exception as e:
                await session.rollback()
                self._performance_metrics["connection_failures"] += 1
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
                self._update_performance_metrics(start_time, False)

        except Exception as e:
            self._performance_metrics["connection_failures"] += 1
            self._update_performance_metrics(start_time, True)
            logger.error(f"Failed to acquire database session: {e}")
            raise

    @contextmanager
    def get_sync_session(self):
        """Get a optimized sync database session with connection pooling.

        Yields
        ------
        Session
            Synchronous database session with connection pooling
        """
        if not self._initialized or not self._sync_session_factory:
            raise RuntimeError("Connection pool not initialized")

        start_time = time.time()

        try:
            session = self._sync_session_factory()
            self._performance_metrics["connection_acquisitions"] += 1

            logger.debug("Acquired sync database session from pool")

            try:
                yield session
            except Exception as e:
                session.rollback()
                self._performance_metrics["connection_failures"] += 1
                logger.error(f"Synchronous database session error: {e}")
                raise
            finally:
                session.close()
                self._update_performance_metrics(start_time, False)

        except Exception as e:
            self._performance_metrics["connection_failures"] += 1
            self._update_performance_metrics(start_time, True)
            logger.error(f"Failed to acquire sync database session: {e}")
            raise

    def get_pool_status(self) -> dict[str, any]:
        """Get current connection pool status and metrics.

        Returns
        -------
        dict[str, any]
            Current pool status including health metrics and performance data
        """
        status = {
            "initialized": self._initialized,
            "database_url": self.database_url,
            "pool_config": {
                "max_connections": self.config.max_connections,
                "min_connections": self.config.min_connections,
                "pool_size": self.config.pool_size,
                "max_overflow": self.config.max_overflow,
                "pool_timeout": self.config.pool_timeout,
            },
            "performance_metrics": self._performance_metrics.copy(),
        }

        if self._health_monitor:
            status["health_status"] = self._health_monitor._health_status.value
            status["health_metrics"] = self._health_monitor._health_metrics.copy()

        # Add actual pool statistics if available
        if self._async_engine and self._async_engine.pool:
            pool = self._async_engine.pool
            status["pool_statistics"] = {
                "pool_size": getattr(pool, "size", 0),
                "checked_out": getattr(pool, "_checkedout", 0),
                "overflow": getattr(pool, "_overflow", 0),
                "invalidated": getattr(pool, "_invalidated", 0),
            }

        return status

    def _update_performance_metrics(self, start_time: float, is_error: bool) -> None:
        """Update performance metrics for database operations.

        Parameters
        ----------
        start_time : float
            Operation start timestamp
        is_error : bool
            Whether the operation resulted in an error
        """
        query_time = time.time() - start_time
        self._performance_metrics["total_queries"] += 1

        if is_error:
            self._performance_metrics["connection_failures"] += 1
        elif query_time > 1.0:  # Consider queries taking >1s as slow
            self._performance_metrics["slow_queries"] += 1

        # Update average query time
        total_time = self._performance_metrics["avg_query_time"] * (
            self._performance_metrics["total_queries"] - 1
        )
        self._performance_metrics["avg_query_time"] = (
            total_time + query_time
        ) / self._performance_metrics["total_queries"]

    async def execute_health_check(self) -> dict[str, any]:
        """Execute comprehensive health check of the connection pool.

        Returns
        -------
        dict[str, any]
            Detailed health check results
        """
        if not self._initialized:
            return {"status": "not_initialized", "error": "Connection pool not initialized"}

        try:
            # Test database connectivity
            async with self.get_async_session() as session:
                await session.execute(text("SELECT 1"))

            # Get current status
            status = self.get_pool_status()
            status["status"] = "healthy"

            return status

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e), "pool_status": self.get_pool_status()}

    def get_performance_report(self) -> dict[str, any]:
        """Generate comprehensive performance report.

        Returns
        -------
        dict[str, any]
            Performance analysis report with recommendations
        """
        metrics = self._performance_metrics

        report = {
            "total_operations": metrics["total_queries"],
            "success_rate": (metrics["total_queries"] - metrics["connection_failures"])
            / max(metrics["total_queries"], 1)
            * 100,
            "average_query_time": metrics["avg_query_time"],
            "slow_query_rate": metrics["slow_queries"] / max(metrics["total_queries"], 1) * 100,
            "connection_efficiency": metrics["connection_acquisitions"]
            / max(metrics["total_queries"], 1),
            "recommendations": [],
        }

        # Generate recommendations based on metrics
        if metrics["avg_query_time"] > 0.5:
            report["recommendations"].append(
                "High average query time - consider query optimization"
            )

        if metrics["slow_queries"] / max(metrics["total_queries"], 1) > 0.1:
            report["recommendations"].append("High slow query rate - investigate query performance")

        if metrics["connection_failures"] / max(metrics["total_queries"], 1) > 0.05:
            report["recommendations"].append(
                "Connection failure rate elevated - check network and database health"
            )

        if metrics["connection_acquisitions"] / max(metrics["total_queries"], 1) > 1.5:
            report["recommendations"].append(
                "High connection acquisition rate - consider connection reuse"
            )

        return report
