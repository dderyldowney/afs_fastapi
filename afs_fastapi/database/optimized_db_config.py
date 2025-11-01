"""
Optimized database configuration with connection pooling and performance tuning.

This module provides centralized database configuration with:
- Intelligent connection pooling for agricultural workloads
- Performance monitoring and optimization
- TimescaleDB integration for time-series data
- Health monitoring and auto-recovery
- Agricultural-specific optimizations

Implementation follows Test-First Development (TDD) GREEN phase.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager, contextmanager

from afs_fastapi.database.connection_pool import AgriculturalConnectionPool, PoolConfiguration


class OptimizedDatabaseConfig:
    """Optimized database configuration with connection pooling and performance tuning.

    This class provides unified database configuration specifically optimized
    for agricultural robotics workloads with high-frequency CAN data and
    time-series analytics requirements.
    """

    def __init__(self, database_url: str | None = None) -> None:
        """Initialize optimized database configuration.

        Parameters
        ----------
        database_url : Optional[str], default None
            Database URL (uses environment if None)
        """
        self.database_url = database_url or self._get_database_url()
        self.connection_pool: AgriculturalConnectionPool | None = None

        # Default optimized configuration for agricultural workloads
        self.default_pool_config = PoolConfiguration(
            max_connections=50,  # Support multiple farm equipment
            min_connections=10,  # Maintain warm connections
            pool_timeout=30.0,  # Agricultural data timeouts
            pool_recycle=3600,  # Recycle hourly for farm operations
            pool_size=30,  # Optimal for agricultural telemetry
            max_overflow=15,  # Handle peak farm operation periods
            enable_hypertable=True,  # TimescaleDB for time-series
            enable_compression=True,  # Compress agricultural data
            batch_size=1000,  # Optimal batch size for farm data
            health_check_interval=60.0,  # Monitor farm equipment data flow
            agricultural_pgns=[
                61444,  # Tractor data
                65265,  # Vehicle speed
                65266,  # Wheel-based speed
                65267,  # Distance traveled
                65271,  # Torque
                65272,  # Power take-off
                130312,  # GNSS position data
                130313,  # GNSS quality data
                130314,  # Yield monitor data
                130315,  # Moisture sensor data
            ],
        )

    def _get_database_url(self) -> str:
        """Get database URL from environment with agricultural-specific defaults.

        Returns
        -------
        str
            Database URL for agricultural operations
        """
        # Check for PostgreSQL configuration (highest preference)
        postgres_url = os.getenv("AFS_DATABASE_URL") or os.getenv("DATABASE_URL")
        if postgres_url and postgres_url.startswith("postgresql"):
            return postgres_url

        # Check for SQLite configuration (medium preference)
        sqlite_url = os.getenv("AFS_SQLITE_URL") or os.getenv("SQLITE_URL")
        if sqlite_url:
            return sqlite_url

        # Default to PostgreSQL with TimescaleDB for agricultural operations
        return "postgresql://postgres:password@localhost:5432/afs_fastapi?sslmode=require"

    async def initialize_pool(self, custom_config: PoolConfiguration | None = None) -> bool:
        """Initialize connection pool with agricultural optimizations.

        Parameters
        ----------
        custom_config : Optional[PoolConfiguration], default None
            Custom pool configuration (uses defaults if None)

        Returns
        -------
        bool
            True if initialization successful
        """
        try:
            # Create pool with either custom or default configuration
            pool_config = custom_config or self.default_pool_config

            self.connection_pool = AgriculturalConnectionPool(self.database_url, pool_config)

            success = await self.connection_pool.initialize()

            if success:
                self._log_optimization_settings()

            return success

        except Exception as e:
            print(f"Failed to initialize optimized database pool: {e}")
            return False

    async def shutdown_pool(self) -> None:
        """Shutdown connection pool gracefully."""
        if self.connection_pool:
            await self.connection_pool.shutdown()
            self.connection_pool = None

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[object, None]:
        """Get optimized database session with connection pooling.

        Yields
        ------
        AsyncSession
            Optimized database session
        """
        if not self.connection_pool:
            raise RuntimeError("Connection pool not initialized")

        async with self.connection_pool.get_async_session() as session:
            yield session

    @contextmanager
    def get_sync_session(self):
        """Get optimized synchronous database session.

        Yields
        ------
        Session
            Optimized synchronous database session
        """
        if not self.connection_pool:
            raise RuntimeError("Connection pool not initialized")

        with self.connection_pool.get_sync_session() as session:
            yield session

    def get_pool_status(self) -> dict:
        """Get current connection pool status and performance metrics.

        Returns
        -------
        dict
            Pool status and performance information
        """
        if not self.connection_pool:
            return {"status": "not_initialized"}

        return self.connection_pool.get_pool_status()

    def get_performance_report(self) -> dict:
        """Generate comprehensive performance report with agricultural insights.

        Returns
        -------
        dict
            Performance analysis with agricultural-specific recommendations
        """
        if not self.connection_pool:
            return {"error": "Connection pool not initialized"}

        report = self.connection_pool.get_performance_report()

        # Add agricultural-specific insights
        report["agricultural_optimizations"] = {
            "configured_agricultural_pgns": self.default_pool_config.agricultural_pgns,
            "batch_optimization_enabled": self.default_pool_config.enable_compression,
            "timescaledb_optimization": self.default_pool_config.enable_hypertable,
            "connection_pool_size": self.default_pool_config.pool_size,
        }

        # Add agricultural-specific recommendations
        agricultural_recommendations = []

        if self.default_pool_config.batch_size < 2000:
            agricultural_recommendations.append(
                "Consider increasing batch size for high-frequency farm equipment data"
            )

        if self.default_pool_config.health_check_interval > 30:
            agricultural_recommendations.append(
                "Reduce health check interval for real-time farm equipment monitoring"
            )

        if len(self.default_pool_config.agricultural_pgns) < 10:
            agricultural_recommendations.append(
                "Add more agricultural PGNs for comprehensive farm data capture"
            )

        report["agricultural_recommendations"] = agricultural_recommendations

        return report

    def _log_optimization_settings(self) -> None:
        """Log current optimization settings for agricultural operations."""
        config = self.default_pool_config

        print("🚜 Agricultural Database Optimization Configuration:")
        print(f"   Connection Pool: {config.max_connections} max, {config.min_connections} min")
        print(f"   Batch Size: {config.batch_size} messages")
        print(f"   TimescaleDB: {'Enabled' if config.enable_hypertable else 'Disabled'}")
        print(f"   Compression: {'Enabled' if config.enable_compression else 'Disabled'}")
        print(f"   Health Monitoring: {config.health_check_interval}s intervals")
        print(f"   Agricultural PGNs: {len(config.agricultural_pgns)} configured")

        # Check if we have TimescaleDB capability
        if "timescale" in self.database_url.lower():
            print("   🎯 TimescaleDB detected - advanced time-series optimization available")


# Global instance for easy access
_db_config: OptimizedDatabaseConfig | None = None


async def get_optimized_db_config(database_url: str | None = None) -> OptimizedDatabaseConfig:
    """Get or create optimized database configuration instance.

    Parameters
    ----------
    database_url : Optional[str], default None
        Database URL (uses environment if None)

    Returns
    -------
    OptimizedDatabaseConfig
        Database configuration instance
    """
    global _db_config

    if _db_config is None:
        _db_config = OptimizedDatabaseConfig(database_url)

    return _db_config


async def initialize_optimized_database(custom_config: PoolConfiguration | None = None) -> bool:
    """Initialize global optimized database configuration.

    Parameters
    ----------
    custom_config : Optional[PoolConfiguration], default None
        Custom pool configuration

    Returns
    -------
    bool
        True if initialization successful
    """
    db_config = await get_optimized_db_config()
    return await db_config.initialize_pool(custom_config)


async def get_optimized_session() -> AsyncGenerator[object, None]:
    """Get optimized database session from global configuration.

    Yields
    ------
    AsyncSession
        Optimized database session
    """
    db_config = await get_optimized_db_config()
    async with db_config.get_session() as session:
        yield session


async def get_optimized_sync_session() -> AsyncGenerator[object, None]:
    """Get optimized synchronous database session from global configuration.

    Yields
    ------
    Session
        Optimized synchronous database session
    """
    db_config = await get_optimized_db_config()
    with db_config.get_sync_session() as session:
        yield session


def get_database_performance_report() -> dict:
    """Get comprehensive database performance report.

    Returns
    -------
    dict
        Performance report with agricultural insights
    """
    if _db_config:
        return _db_config.get_performance_report()
    return {"error": "Database configuration not initialized"}
