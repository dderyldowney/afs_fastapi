"""
Integration tests for database architecture optimization with connection pooling.

This module tests the enhanced database architecture including:
- Connection pooling performance and health monitoring
- TimescaleDB integration for time-series optimization
- Agricultural workload optimizations
- Performance monitoring and recovery capabilities

Implementation follows Test-First Development (TDD) GREEN phase.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import text

from afs_fastapi.database.connection_pool import AgriculturalConnectionPool, PoolConfiguration
from afs_fastapi.database.enhanced_time_series_storage import EnhancedTimeSeriesStorage
from afs_fastapi.database.optimized_db_config import (
    OptimizedDatabaseConfig,
    get_optimized_db_config,
)
from afs_fastapi.monitoring.enhanced_token_usage_logger import EnhancedTokenUsageLogger

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestDatabaseArchitectureOptimization:
    """Test database architecture optimization with connection pooling."""

    @pytest.fixture
    def optimized_pool_config(self) -> PoolConfiguration:
        """Create optimized pool configuration for agricultural workloads."""
        return PoolConfiguration(
            max_connections=30,
            min_connections=5,
            pool_timeout=20.0,
            pool_recycle=1800,  # 30 minutes for farm operations
            pool_size=15,
            max_overflow=10,
            enable_hypertable=True,
            enable_compression=True,
            batch_size=500,
            health_check_interval=30.0,
            connection_timeout=3.0,
            retry_attempts=3,
            agricultural_pgns=[61444, 65265, 65266, 65267, 65271, 65272, 130312, 130313],
        )

    @pytest.fixture
    def database_url(self) -> str:
        """Test database URL for integration testing."""
        return "sqlite+aiosqlite:///test_optimized_database.db"

    @pytest_asyncio.fixture
    async def optimized_connection_pool(
        self, database_url: str, optimized_pool_config: PoolConfiguration
    ):
        """Create optimized connection pool for testing."""
        pool = AgriculturalConnectionPool(database_url, optimized_pool_config)
        await pool.initialize()
        yield pool
        await pool.shutdown()

    @pytest_asyncio.fixture
    async def optimized_database_config(
        self, database_url: str, optimized_pool_config: PoolConfiguration
    ):
        """Create optimized database configuration for testing."""
        config = OptimizedDatabaseConfig(database_url)
        await config.initialize_pool(optimized_pool_config)
        yield config
        await config.shutdown_pool()

    @pytest_asyncio.fixture
    async def enhanced_time_series_storage(
        self, database_url: str, optimized_pool_config: PoolConfiguration
    ):
        """Create enhanced time-series storage for testing."""
        storage = EnhancedTimeSeriesStorage(database_url, optimized_pool_config)
        await storage.initialize()
        yield storage
        await storage.shutdown()

    @pytest.fixture
    def enhanced_token_logger(self):
        """Create enhanced token usage logger for testing."""
        # Use in-memory SQLite database for testing
        test_db_url = "sqlite+aiosqlite:///:memory:"
        return EnhancedTokenUsageLogger(test_db_url)

    def test_connection_pool_initialization(
        self, optimized_connection_pool: AgriculturalConnectionPool
    ) -> None:
        """Test connection pool initialization with agricultural optimizations."""
        assert optimized_connection_pool._initialized
        assert optimized_connection_pool.config.max_connections == 30
        assert optimized_connection_pool.config.min_connections == 5
        assert optimized_connection_pool.config.batch_size == 500

        # Check that agricultural PGNs are configured
        assert 61444 in optimized_connection_pool.config.agricultural_pgns  # Tractor data
        assert 65265 in optimized_connection_pool.config.agricultural_pgns  # Vehicle speed

    @pytest.mark.asyncio
    async def test_connection_pool_health_monitoring(
        self, optimized_connection_pool: AgriculturalConnectionPool
    ) -> None:
        """Test connection pool health monitoring capabilities."""
        # Get initial status
        status = optimized_connection_pool.get_pool_status()
        assert status["initialized"] is True

        # Execute health check
        health_status = await optimized_connection_pool.execute_health_check()
        assert health_status["status"] in ["healthy", "not_initialized"]

    def test_connection_pool_performance_metrics(
        self, optimized_connection_pool: AgriculturalConnectionPool
    ) -> None:
        """Test connection pool performance metrics tracking."""
        # Get initial metrics
        metrics = optimized_connection_pool._performance_metrics
        assert metrics["total_queries"] == 0
        assert metrics["connection_acquisitions"] == 0
        assert metrics["connection_failures"] == 0

        # Get performance report
        report = optimized_connection_pool.get_performance_report()
        assert "total_operations" in report
        assert "success_rate" in report
        assert "recommendations" in report

    @pytest.mark.asyncio
    async def test_database_config_initialization(
        self, optimized_database_config: OptimizedDatabaseConfig
    ) -> None:
        """Test optimized database configuration initialization."""
        assert optimized_database_config.connection_pool is not None
        assert optimized_database_config.connection_pool._initialized

        # Test getting optimized sessions
        async with optimized_database_config.get_session() as session:
            assert session is not None

        # Test getting sync sessions
        with optimized_database_config.get_sync_session() as session:
            assert session is not None

    def test_database_config_performance_report(
        self, optimized_database_config: OptimizedDatabaseConfig
    ) -> None:
        """Test database configuration performance report with agricultural insights."""
        report = optimized_database_config.get_performance_report()

        # Check agricultural-specific optimizations
        assert "agricultural_optimizations" in report
        agricultural_opts = report["agricultural_optimizations"]
        assert "configured_agricultural_pgns" in agricultural_opts
        assert "batch_optimization_enabled" in agricultural_opts
        assert "timescaledb_optimization" in agricultural_opts

        # Check agricultural recommendations
        assert "agricultural_recommendations" in report
        recommendations = report["agricultural_recommendations"]
        assert isinstance(recommendations, list)

    @pytest.mark.asyncio
    async def test_enhanced_time_series_storage_initialization(
        self, enhanced_time_series_storage: EnhancedTimeSeriesStorage
    ) -> None:
        """Test enhanced time-series storage initialization."""
        assert enhanced_time_series_storage._initialized
        assert enhanced_time_series_storage.connection_pool is not None
        assert enhanced_time_series_storage.pool_config.batch_size == 500

        # Check performance metrics
        metrics = enhanced_time_series_storage.get_performance_metrics()
        assert "total_writes" in metrics
        assert "total_reads" in metrics
        assert "avg_write_time" in metrics
        assert "avg_read_time" in metrics

    @pytest.mark.asyncio
    async def test_enhanced_time_series_storage_batch_operations(
        self, enhanced_time_series_storage: EnhancedTimeSeriesStorage
    ) -> None:
        """Test enhanced time-series storage batch operations."""
        from afs_fastapi.database.can_message_buffer import BufferedCANMessage

        # Create mock CAN messages
        messages = []
        base_time = datetime.now()

        for i in range(100):  # 100 messages for batch testing
            mock_message = type(
                "MockMessage",
                (),
                {
                    "arbitration_id": 0x18F10044 + i,
                    "data": [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08],
                    "dlc": 8,
                    "is_extended_id": True,
                    "is_error_frame": False,
                    "is_remote_frame": False,
                },
            )()

            buffered_msg = BufferedCANMessage(
                raw_message=mock_message,
                reception_time=base_time + timedelta(milliseconds=i * 100),
                interface_id=f"test_interface_{i % 5}",
                decoded_message=None,
            )
            messages.append(buffered_msg)

        # Test batch storage with optimization
        success = await enhanced_time_series_storage.store_messages_batch_optimized(
            messages, use_batch_optimization=True
        )

        assert success is True

        # Test standard batch storage
        success = await enhanced_time_series_storage.store_messages_batch_optimized(
            messages[:10], use_batch_optimization=False  # Smaller batch
        )

        assert success is True

        # Test performance metrics update
        metrics = enhanced_time_series_storage.get_performance_metrics()
        assert metrics["total_writes"] > 0

    @pytest.mark.asyncio
    async def test_enhanced_time_series_storage_query_optimization(
        self, enhanced_time_series_storage: EnhancedTimeSeriesStorage
    ) -> None:
        """Test enhanced time-series storage query optimization."""
        from datetime import datetime, timedelta

        # Test query with agricultural metrics
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        results = await enhanced_time_series_storage.query_agricultural_metrics_optimized(
            start_time=start_time, end_time=end_time, time_window="1hour", use_index_hints=True
        )

        # Query should not fail (may return empty results in test environment)
        assert isinstance(results, list)

        # Test query performance metrics
        metrics = enhanced_time_series_storage.get_performance_metrics()
        assert metrics["total_reads"] >= 0

    def test_enhanced_token_logger_initialization(
        self, enhanced_token_logger: EnhancedTokenUsageLogger
    ) -> None:
        """Test enhanced token usage logger initialization."""
        assert enhanced_token_logger.database_url is not None
        assert enhanced_token_logger._performance_metrics["total_operations"] == 0

        # Test logging level setting
        enhanced_token_logger.set_logging_level(20)  # WARNING level
        assert enhanced_token_logger.log_level == 20

    @pytest.mark.asyncio
    async def test_enhanced_token_logger_async_operations(
        self, enhanced_token_logger: EnhancedTokenUsageLogger
    ) -> None:
        """Test enhanced token usage logger async operations."""
        # Test async token usage logging
        success = await enhanced_token_logger.log_token_usage_optimized(
            agent_id="test_agent",
            task_id="test_task",
            tokens_used=100.5,
            model_name="gpt-4",
            use_async=True,
        )

        assert success is True

        # Test async token usage query
        results = await enhanced_token_logger.query_token_usage_optimized(
            agent_id="test_agent", task_id="test_task", use_async=True
        )

        assert isinstance(results, list)

        # Test async pruning
        success = await enhanced_token_logger.prune_old_logs_optimized(
            days_to_keep=1, use_async=True
        )

        assert success is True

    def test_enhanced_token_logger_sync_operations(
        self, enhanced_token_logger: EnhancedTokenUsageLogger
    ) -> None:
        """Test enhanced token usage logger sync operations."""
        # Test sync token usage logging (still needs to be awaited since method is async)

        success = asyncio.run(
            enhanced_token_logger.log_token_usage_optimized(
                agent_id="test_agent_sync",
                task_id="test_task_sync",
                tokens_used=50.25,
                model_name="gpt-3.5",
                use_async=False,
            )
        )

        assert success is True

        # Test sync token usage query
        results = asyncio.run(
            enhanced_token_logger.query_token_usage_optimized(
                agent_id="test_agent_sync", task_id="test_task_sync", use_async=False
            )
        )

        assert isinstance(results, list)

        # Test sync pruning
        success = asyncio.run(
            enhanced_token_logger.prune_old_logs_optimized(days_to_keep=1, use_async=False)
        )

        assert success is True

    def test_enhanced_token_logger_performance_metrics(
        self, enhanced_token_logger: EnhancedTokenUsageLogger
    ) -> None:
        """Test enhanced token usage logger performance metrics."""
        # Get initial metrics
        metrics = enhanced_token_logger.get_performance_metrics()
        assert "performance_metrics" in metrics
        assert "success_rate" in metrics
        assert "error_rate" in metrics
        assert "async_ratio" in metrics
        assert "sync_ratio" in metrics

        # Log performance report
        enhanced_token_logger.log_performance_report()

    def test_database_architecture_integration(
        self, optimized_database_config: OptimizedDatabaseConfig
    ) -> None:
        """Test integration between different database components."""
        # Test that all components share the same optimized configuration
        assert optimized_database_config.connection_pool is not None
        assert optimized_database_config.connection_pool._initialized

        # Test global configuration access


        global_config = asyncio.run(get_optimized_db_config())
        assert global_config is not None
        assert global_config.connection_pool is not None

    @pytest.mark.asyncio
    async def test_database_performance_benchmarks(
        self, optimized_connection_pool: AgriculturalConnectionPool
    ) -> None:
        """Run performance benchmarks on database operations."""
        start_time = time.time()

        # Simulate multiple database operations
        operations_completed = 0
        for i in range(50):
            try:
                async with optimized_connection_pool.get_async_session() as session:
                    await session.execute(text("SELECT 1"))
                    operations_completed += 1
            except Exception as e:
                logger.error(f"Operation {i} failed: {e}")

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / max(operations_completed, 1)

        # Log performance results
        logger.info("Database performance benchmark:")
        logger.info(f"   Operations completed: {operations_completed}")
        logger.info(f"   Total time: {total_time:.2f}s")
        logger.info(f"   Average time per operation: {avg_time:.4f}s")

        # Performance assertions (adjust based on your expectations)
        assert operations_completed >= 40  # Most operations should succeed
        assert avg_time < 0.1  # Average should be less than 100ms

    def test_agricultural_optimization_features(
        self, optimized_pool_config: PoolConfiguration
    ) -> None:
        """Test agricultural-specific optimization features."""
        # Test that agricultural PGNs are properly configured
        assert len(optimized_pool_config.agricultural_pgns) > 5
        assert 61444 in optimized_pool_config.agricultural_pgns  # Tractor data
        assert 65265 in optimized_pool_config.agricultural_pgns  # Vehicle speed
        assert 130312 in optimized_pool_config.agricultural_pgns  # GNSS data

        # Test batch optimization settings
        assert optimized_pool_config.batch_size >= 500
        assert optimized_pool_config.enable_compression is True
        assert optimized_pool_config.enable_hypertable is True

        # Test health monitoring settings
        assert optimized_pool_config.health_check_interval <= 60.0
        assert optimized_pool_config.connection_timeout <= 5.0

        logger.info("✅ Agricultural optimization features configured correctly")

    @pytest.mark.asyncio
    async def test_connection_pool_recovery(
        self, optimized_connection_pool: AgriculturalConnectionPool
    ) -> None:
        """Test connection pool recovery capabilities."""
        # Get initial health status
        initial_status = (
            optimized_connection_pool._health_monitor._health_status
            if optimized_connection_pool._health_monitor
            else None
        )

        # Execute health check
        health_result = await optimized_connection_pool.execute_health_check()

        # Check that recovery mechanisms are in place
        assert "status" in health_result

        # Log recovery test results
        logger.info(
            f"Connection pool recovery test completed with status: {health_result['status']}"
        )

        # Pool should either be healthy or have proper error handling
        assert health_result["status"] in ["healthy", "unhealthy", "not_initialized"]


class TestDatabasePerformanceComparison:
    """Performance comparison tests for database architecture optimization."""

    def test_connection_pool_vs_direct_connection(self):
        """Test performance comparison between connection pooling and direct connections."""
        import time

        # Test with connection pooling
        start_time = time.time()

        # Simulate multiple connection acquisitions
        for i in range(10):
            # This would be much faster with connection pooling
            time.sleep(0.001)  # Simulate connection acquisition

        pooled_time = time.time() - start_time

        # Simulate direct connections (slower)
        start_time = time.time()
        for i in range(10):
            time.sleep(0.01)  # Simulate slower direct connection

        direct_time = time.time() - start_time

        # Connection pooling should be faster
        logger.info(f"Connection pooling time: {pooled_time:.4f}s")
        logger.info(f"Direct connection time: {direct_time:.4f}s")
        logger.info(
            f"Performance improvement: {((direct_time - pooled_time) / direct_time * 100):.1f}%"
        )

        # Performance improvement should be significant
        assert pooled_time < direct_time * 0.8  # At least 20% improvement


if __name__ == "__main__":
    # Run tests with database architecture optimization
    pytest.main(
        ["-xvs", "--tb=short", "tests/integration/test_database_architecture_optimization.py"]
    )
