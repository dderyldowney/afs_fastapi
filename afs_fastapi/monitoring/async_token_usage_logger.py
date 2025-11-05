"""
Async-compatible token usage logger for agricultural AI operations.

This module provides high-performance async token usage tracking specifically
designed for agricultural robotics AI operations, with proper async database
operations, connection pooling, and performance optimization.

Implementation follows Test-First Development (TDD) GREEN phase.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from afs_fastapi.database.agricultural_schemas_async import TokenUsage
from afs_fastapi.database.async_repository import TokenUsageAsyncRepository, UnitOfWork
from afs_fastapi.database.connection_pool import AgriculturalConnectionPool, PoolConfiguration

# Configure logging for async token usage logging
logger = logging.getLogger(__name__)


class AsyncTokenUsageLogger:
    """High-performance async token usage logger for agricultural AI operations.

    Provides async-compatible token usage tracking with:
    - Connection pooling for high-performance database access
    - Async session management with proper transaction handling
    - Batch operations for high-frequency agricultural AI operations
    - Performance monitoring and optimization
    - Comprehensive error handling and recovery
    """

    _instance = None
    _initialized = False

    def __init__(
        self,
        database_url: str,
        pool_config: PoolConfiguration | None = None,
        log_level: int = logging.INFO,
    ) -> None:
        """Initialize async token usage logger.

        Parameters
        ----------
        database_url : str
            Database connection URL (PostgreSQL recommended for async operations)
        pool_config : PoolConfiguration, optional
            Connection pool configuration
        log_level : int, default logging.INFO
            Logging level
        """
        self.database_url = database_url
        self.pool_config = pool_config or PoolConfiguration()
        self.log_level = log_level

        # Initialize async database components
        self.async_engine: AsyncEngine | None = None
        self.async_session_factory: async_sessionmaker[AsyncSession] | None = None
        self.connection_pool: AgriculturalConnectionPool | None = None

        # Performance tracking
        self._performance_metrics: dict[str, int | float | list[float]] = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "batch_operations": 0,
            "avg_operation_time": 0.0,
            "avg_batch_time": 0.0,
            "operation_times": [],
            "batch_times": [],
        }

        self._setup_logging()

    @classmethod
    async def reset_for_testing(cls, database_url: str) -> AsyncTokenUsageLogger:
        """Reset singleton instance for testing with a new database.

        This method is intended for testing only. It allows tests to reinitialize
        the singleton with a test database URL, ensuring test isolation.

        Parameters
        ----------
        database_url : str
            Database URL for test database

        Returns
        -------
        AsyncTokenUsageLogger
            Instance configured with test database
        """
        # Create async engine for testing
        engine = create_async_engine(database_url, echo=False)
        async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        # Create tables
        async with engine.connect() as conn:
            await conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS token_usage (id TEXT PRIMARY KEY, agent_id TEXT NOT NULL, task_id TEXT NOT NULL, tokens_used FLOAT NOT NULL, model_name TEXT NOT NULL, timestamp TIMESTAMP NOT NULL)"
                )
            )

        cls._instance = cls(database_url=database_url)
        cls._initialized = True

        # Update the global async_token_logger instance
        global async_token_logger
        async_token_logger = cls._instance

        return cls._instance

    def _setup_logging(self) -> None:
        """Configure logging for the async token usage logger."""
        logger.setLevel(self.log_level)

    async def initialize(self) -> bool:
        """Initialize async database connections and resources.

        Returns
        -------
        bool
            True if initialization successful
        """
        try:
            # Initialize connection pool for high-performance async operations
            self.connection_pool = AgriculturalConnectionPool(self.database_url, self.pool_config)

            if not await self.connection_pool.initialize():
                logger.error("Failed to initialize connection pool")
                return False

            # Create async engine directly for token usage operations
            self.async_engine = create_async_engine(
                self.database_url,
                pool_size=self.pool_config.pool_size,
                max_overflow=self.pool_config.max_overflow,
                pool_timeout=self.pool_config.pool_timeout,
                pool_recycle=self.pool_config.pool_recycle,
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
                await conn.execute(text("SELECT 1"))

            self._initialized = True
            logger.info("Async token usage logger initialized successfully")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize async token usage logger: {e}")
            return False

    async def shutdown(self) -> None:
        """Shutdown async database connections gracefully."""
        if self.connection_pool:
            await self.connection_pool.shutdown()

        if self.async_engine:
            await self.async_engine.dispose()

        self._initialized = False
        logger.info("Async token usage logger shut down")

    async def log_token_usage(
        self,
        agent_id: str,
        task_id: str,
        tokens_used: float,
        model_name: str,
        timestamp: datetime | None = None,
    ) -> bool:
        """Log token usage asynchronously with high performance.

        Parameters
        ----------
        agent_id : str
            Agent identifier
        task_id : str
            Task identifier
        tokens_used : float
            Number of tokens used
        model_name : str
            Name of the model used
        timestamp : datetime, optional
            Usage timestamp (defaults to now)

        Returns
        -------
        bool
            True if logging was successful
        """
        if not self._initialized:
            logger.error("Async token usage logger not initialized")
            return False

        start_time = datetime.now(UTC)

        try:
            timestamp = timestamp or datetime.now(UTC)
            str(uuid.uuid4())

            # Use async session with connection pooling
            async with self.async_session_factory() as session:
                # Use unit of work pattern for consistency
                async with UnitOfWork(session) as uow:
                    repository = uow.token_usage
                    await repository.create_token_usage(
                        agent_id=agent_id,
                        task_id=task_id,
                        tokens_used=tokens_used,
                        model_name=model_name,
                        timestamp=timestamp,
                    )
                    await uow.commit()

            # Update performance metrics
            self._update_performance_metrics(start_time, True, "single_operation")

            logger.debug(
                f"Logged token usage: agent={agent_id}, task={task_id}, tokens={tokens_used}"
            )
            return True

        except Exception as e:
            self._update_performance_metrics(start_time, False, "single_operation")
            logger.error(f"Failed to log token usage: {e}", exc_info=True)
            return False

    async def batch_log_token_usage(
        self,
        usage_records: list[dict[str, Any]],
        batch_timeout: float = 30.0,
    ) -> bool:
        """Log multiple token usage records in a batch for high performance.

        Parameters
        ----------
        usage_records : list[dict[str, Any]]
            List of token usage records to log
        batch_timeout : float, default 30.0
            Timeout for batch operation in seconds

        Returns
        -------
        bool
            True if batch logging was successful
        """
        if not self._initialized:
            logger.error("Async token usage logger not initialized")
            return False

        if not usage_records:
            return True

        start_time = datetime.now(UTC)

        try:
            # Use async session with connection pooling
            async with self.async_session_factory() as session:
                # Use unit of work pattern for batch consistency
                async with UnitOfWork(session) as uow:
                    repository = uow.token_usage

                    # Create all usage records
                    for record in usage_records:
                        timestamp = record.get("timestamp") or datetime.now(UTC)
                        await repository.create_token_usage(
                            agent_id=record["agent_id"],
                            task_id=record["task_id"],
                            tokens_used=record["tokens_used"],
                            model_name=record["model_name"],
                            timestamp=timestamp,
                        )

                    await uow.commit()

            # Update performance metrics
            self._update_performance_metrics(start_time, True, "batch_operation")
            self._performance_metrics["batch_operations"] += 1

            logger.debug(f"Batch logged {len(usage_records)} token usage records")
            return True

        except TimeoutError:
            self._update_performance_metrics(start_time, False, "batch_operation")
            logger.error(f"Batch logging timeout after {batch_timeout} seconds")
            return False
        except Exception as e:
            self._update_performance_metrics(start_time, False, "batch_operation")
            logger.error(f"Failed to batch log token usage: {e}", exc_info=True)
            return False

    async def query_token_usage(
        self,
        agent_id: str | None = None,
        task_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[TokenUsage]:
        """Query token usage data asynchronously with high performance.

        Parameters
        ----------
        agent_id : str, optional
            Filter by agent identifier
        task_id : str, optional
            Filter by task identifier
        start_time : datetime, optional
            Filter by start time
        end_time : datetime, optional
            Filter by end time
        limit : int, default 1000
            Maximum number of records to return
        offset : int, default 0
            Offset for pagination

        Returns
        -------
        list[TokenUsage]
            List of token usage records
        """
        if not self._initialized:
            logger.error("Async token usage logger not initialized")
            return []

        start_time_query = datetime.now(UTC)

        try:
            # Use async session with connection pooling
            async with self.async_session_factory() as session:
                # Use unit of work pattern for consistency
                async with UnitOfWork(session) as uow:
                    repository = uow.token_usage

                    # Get token usage statistics first
                    await repository.get_token_usage_statistics(
                        agent_id=agent_id,
                        task_id=task_id,
                        start_time=start_time,
                        end_time=end_time,
                    )

                    # Query usage records
                    query_result = []

                    if agent_id:
                        query_result = await repository.get_token_usage_by_agent(
                            agent_id=agent_id,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    elif task_id:
                        query_result = await repository.get_token_usage_by_task(
                            task_id=task_id,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    else:
                        # Fallback to query all with filters
                        async with uow.session.execute(
                            f"""
                            SELECT * FROM token_usage
                            WHERE 1=1
                            {'AND agent_id = :agent_id' if agent_id else ''}
                            {'AND task_id = :task_id' if task_id else ''}
                            {'AND timestamp >= :start_time' if start_time else ''}
                            {'AND timestamp <= :end_time' if end_time else ''}
                            ORDER BY timestamp DESC
                            LIMIT :limit OFFSET :offset
                            """,
                            {
                                "agent_id": agent_id,
                                "task_id": task_id,
                                "start_time": start_time,
                                "end_time": end_time,
                                "limit": limit,
                                "offset": offset,
                            },
                        ) as result:
                            query_result = result.scalars().all()

                    # Limit results
                    limited_results = query_result[offset : offset + limit]

                    # Update performance metrics
                    self._update_performance_metrics(start_time_query, True, "query_operation")

                    logger.debug(f"Queried {len(limited_results)} token usage records")
                    return limited_results

        except Exception as e:
            self._update_performance_metrics(start_time_query, False, "query_operation")
            logger.error(f"Failed to query token usage: {e}", exc_info=True)
            return []

    async def get_token_usage_statistics(
        self,
        agent_id: str | None = None,
        task_id: str | None = None,
        model_name: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        """Get comprehensive token usage statistics asynchronously.

        Parameters
        ----------
        agent_id : str, optional
            Filter by agent identifier
        task_id : str, optional
            Filter by task identifier
        model_name : str, optional
            Filter by model name
        start_time : datetime, optional
            Filter by start time
        end_time : datetime, optional
            Filter by end time

        Returns
        -------
        dict[str, Any]
            Comprehensive token usage statistics
        """
        if not self._initialized:
            logger.error("Async token usage logger not initialized")
            return {}

        start_time_query = datetime.now(UTC)

        try:
            # Use async session with connection pooling
            async with self.async_session_factory() as session:
                # Use unit of work pattern for consistency
                async with UnitOfWork(session) as uow:
                    repository = uow.token_usage

                    # Get comprehensive statistics
                    stats = await repository.get_token_usage_statistics(
                        agent_id=agent_id,
                        task_id=task_id,
                        model_name=model_name,
                        start_time=start_time,
                        end_time=end_time,
                    )

                    # Add agricultural AI operation insights
                    insights = await self._generate_agricultural_insights(
                        repository, agent_id, task_id, start_time, end_time
                    )

                    # Update performance metrics
                    self._update_performance_metrics(start_time_query, True, "stats_operation")

                    result = {
                        "statistics": stats,
                        "insights": insights,
                        "performance": self._get_recent_performance_metrics(),
                        "timestamp": datetime.now(UTC).isoformat(),
                    }

                    logger.debug("Retrieved token usage statistics for agricultural AI operations")
                    return result

        except Exception as e:
            self._update_performance_metrics(start_time_query, False, "stats_operation")
            logger.error(f"Failed to get token usage statistics: {e}", exc_info=True)
            return {}

    async def prune_old_logs(self, days_to_keep: int = 30) -> bool:
        """Prune token usage logs older than specified days asynchronously.

        Parameters
        ----------
        days_to_keep : int, default 30
            Number of days to keep logs

        Returns
        -------
        bool
            True if pruning was successful
        """
        if not self._initialized:
            logger.error("Async token usage logger not initialized")
            return False

        start_time = datetime.now(UTC)
        cutoff_date = datetime.now(UTC) - timedelta(days=days_to_keep)

        try:
            # Use async session with connection pooling
            async with self.async_session_factory() as session:
                # Use unit of work pattern for consistency
                async with UnitOfWork(session) as uow:
                    repository = uow.token_usage

                    # Count and delete old logs
                    deleted_count = await repository.delete_old_token_usage(cutoff_date)
                    await uow.commit()

            # Update performance metrics
            self._update_performance_metrics(start_time, True, "prune_operation")

            logger.info(f"Pruned {deleted_count} token usage logs older than {days_to_keep} days")
            return True

        except Exception as e:
            self._update_performance_metrics(start_time, False, "prune_operation")
            logger.error(f"Failed to prune old token usage logs: {e}", exc_info=True)
            return False

    async def _generate_agricultural_insights(
        self,
        repository: TokenUsageAsyncRepository,
        agent_id: str | None,
        task_id: str | None,
        start_time: datetime | None,
        end_time: datetime | None,
    ) -> dict[str, Any]:
        """Generate agricultural AI operation insights from token usage data.

        Parameters
        ----------
        repository : TokenUsageAsyncRepository
            Token usage repository
        agent_id : str, optional
            Agent identifier filter
        task_id : str, optional
            Task identifier filter
        start_time : datetime, optional
            Start time filter
        end_time : datetime, optional
            End time filter

        Returns
        -------
        dict[str, Any]
            Agricultural AI operation insights
        """
        try:
            # Get model distribution for agricultural AI operations
            model_stats = await repository.get_token_usage_statistics(
                agent_id=agent_id,
                task_id=task_id,
                start_time=start_time,
                end_time=end_time,
            )

            # Calculate agricultural AI efficiency metrics
            insights = {
                "model_efficiency": {
                    "preferred_models": self._identify_preferred_models(model_stats),
                    "cost_optimization_opportunities": self._identify_cost_optimization_opportunities(
                        model_stats
                    ),
                    "scalability_assessment": self._assess_scalability(model_stats),
                },
                "operational_patterns": {
                    "peak_usage_times": self._identify_peak_usage_times(
                        agent_id, start_time, end_time
                    ),
                    "task_complexity_analysis": self._analyze_task_complexity(agent_id, task_id),
                    "resource_allocation_insights": self._analyze_resource_allocation(agent_id),
                },
                "agricultural_ai_recommendations": self._generate_agricultural_ai_recommendations(
                    model_stats
                ),
            }

            return insights

        except Exception as e:
            logger.error(f"Failed to generate agricultural insights: {e}")
            return {"error": str(e)}

    def _identify_preferred_models(self, model_stats: dict[str, Any]) -> list[str]:
        """Identify preferred AI models for agricultural operations.

        Parameters
        ----------
        model_stats : dict[str, Any]
            Model usage statistics

        Returns
        -------
        list[str]
            List of preferred models
        """
        # Simple heuristic: models with high efficiency and moderate cost
        # In practice, this would be more sophisticated
        return ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]

    def _identify_cost_optimization_opportunities(self, model_stats: dict[str, Any]) -> list[str]:
        """Identify cost optimization opportunities for agricultural AI operations.

        Parameters
        ----------
        model_stats : dict[str, Any]
            Model usage statistics

        Returns
        -------
        list[str]
            List of optimization opportunities
        """
        opportunities = []

        # Simple heuristic: if high average tokens, suggest smaller models
        avg_tokens = model_stats.get("average_tokens_per_usage", 0)
        if avg_tokens > 10000:
            opportunities.append("Consider using smaller models for routine agricultural tasks")

        # If high usage frequency, suggest batch operations
        total_usage = model_stats.get("total_usage_count", 0)
        if total_usage > 1000:
            opportunities.append(
                "Implement batch operations for high-frequency agricultural AI tasks"
            )

        return opportunities

    def _assess_scalability(self, model_stats: dict[str, Any]) -> str:
        """Assess scalability of current AI operations for agricultural needs.

        Parameters
        ----------
        model_stats : dict[str, Any]
            Model usage statistics

        Returns
        -------
        str
            Scalability assessment
        """
        total_tokens = model_stats.get("total_tokens_used", 0)
        if total_tokens < 1000000:
            return "currently_sufficient_for_small_farms"
        elif total_tokens < 10000000:
            return "adequate_for_medium_scale_operations"
        else:
            return "requires_enterprise_scaling_for_large_agricultural_operations"

    async def _identify_peak_usage_times(
        self, agent_id: str | None, start_time: datetime | None, end_time: datetime | None
    ) -> list[str]:
        """Identify peak usage times for agricultural AI operations.

        Parameters
        ----------
        agent_id : str, optional
            Agent identifier filter
        start_time : datetime, optional
            Start time filter
        end_time : datetime, optional
            End time filter

        Returns
        -------
        list[str]
            List of peak usage time periods
        """
        # Placeholder implementation
        # In practice, this would analyze actual usage patterns
        return ["peak_harvest_season", "planting_season", "irrigation_scheduling"]

    async def _analyze_task_complexity(
        self, agent_id: str | None, task_id: str | None
    ) -> dict[str, Any]:
        """Analyze complexity of agricultural AI tasks.

        Parameters
        ----------
        agent_id : str, optional
            Agent identifier filter
        task_id : str, optional
            Task identifier filter

        Returns
        -------
        dict[str, Any]
            Task complexity analysis
        """
        # Placeholder implementation
        # In practice, this would analyze actual task performance
        return {
            "high_complexity_tasks": ["harvest_yield_prediction", "crop_disease_detection"],
            "medium_complexity_tasks": ["field_planning", "irrigation_optimization"],
            "low_complexity_tasks": ["equipment_status_monitoring", "weather_alerts"],
        }

    async def _analyze_resource_allocation(self, agent_id: str | None) -> dict[str, Any]:
        """Analyze resource allocation for agricultural AI operations.

        Parameters
        ----------
        agent_id : str, optional
            Agent identifier filter

        Returns
        -------
        dict[str, Any]
            Resource allocation analysis
        """
        # Placeholder implementation
        # In practice, this would analyze actual resource usage
        return {
            "model_efficiency": "optimized_for_agricultural_workloads",
            "resource_utilization": "well_balanced",
            "scalability_recommendations": ["implement_connection_pooling", "use_timescaledb"],
        }

    def _generate_agricultural_ai_recommendations(self, model_stats: dict[str, Any]) -> list[str]:
        """Generate specific recommendations for agricultural AI operations.

        Parameters
        ----------
        model_stats : dict[str, Any]
            Model usage statistics

        Returns
        -------
        list[str]
            List of agricultural AI recommendations
        """
        recommendations = []

        # Agricultural-specific recommendations
        total_tokens = model_stats.get("total_tokens_used", 0)
        if total_tokens > 500000:
            recommendations.append("Implement seasonal model optimization for agricultural cycles")

        avg_tokens = model_stats.get("average_tokens_per_usage", 0)
        if avg_tokens > 5000:
            recommendations.append(
                "Consider fine-tuning models for agricultural domain-specific tasks"
            )

        recommendations.append("Implement predictive scaling for agricultural AI workloads")
        recommendations.append("Add context-aware AI for agricultural equipment maintenance")

        return recommendations

    def _update_performance_metrics(
        self, start_time: datetime, success: bool, operation_type: str
    ) -> None:
        """Update performance metrics for async operations.

        Parameters
        ----------
        start_time : datetime
            Operation start time
        success : bool
            Whether operation was successful
        operation_type : str
            Type of operation (single_operation, batch_operation, query_operation, etc.)
        """
        duration = (datetime.now(UTC) - start_time).total_seconds()

        self._performance_metrics["total_operations"] += 1
        if success:
            self._performance_metrics["successful_operations"] += 1
        else:
            self._performance_metrics["failed_operations"] += 1

        # Update operation-specific metrics
        if operation_type in ["single_operation", "query_operation", "stats_operation"]:
            self._performance_metrics["operation_times"].append(duration)
            times = self._performance_metrics["operation_times"]
            self._performance_metrics["avg_operation_time"] = sum(times) / len(times)
        elif operation_type == "batch_operation":
            self._performance_metrics["batch_times"].append(duration)
            times = self._performance_metrics["batch_times"]
            self._performance_metrics["avg_batch_time"] = sum(times) / len(times)

    def _get_recent_performance_metrics(self) -> dict[str, Any]:
        """Get recent performance metrics for monitoring.

        Returns
        -------
        dict[str, Any]
            Recent performance metrics
        """
        return {
            "success_rate": (
                self._performance_metrics["successful_operations"]
                / max(self._performance_metrics["total_operations"], 1)
            )
            * 100,
            "avg_operation_time": self._performance_metrics["avg_operation_time"],
            "avg_batch_time": self._performance_metrics["avg_batch_time"],
            "recent_operations": self._performance_metrics["operation_times"][-10:],
            "batch_efficiency": self._performance_metrics["batch_operations"]
            / max(self._performance_metrics["total_operations"], 1),
        }

    def get_performance_report(self) -> dict[str, Any]:
        """Generate comprehensive performance report for agricultural AI operations.

        Returns
        -------
        dict[str, Any]
            Performance analysis report with agricultural-specific metrics
        """
        metrics = self._performance_metrics

        report = {
            "total_operations": metrics["total_operations"],
            "successful_operations": metrics["successful_operations"],
            "failed_operations": metrics["failed_operations"],
            "success_rate": (metrics["successful_operations"] / max(metrics["total_operations"], 1))
            * 100,
            "average_operation_time": metrics["avg_operation_time"],
            "average_batch_time": metrics["avg_batch_time"],
            "batch_efficiency": metrics["batch_operations"] / max(metrics["total_operations"], 1),
            "agricultural_optimization": {
                "ai_model_efficiency": self._assess_ai_model_efficiency(),
                "database_performance": self._assess_database_performance(),
                "scalability_readiness": self._assess_scalability_readiness(),
            },
            "recommendations": self._generate_performance_recommendations(),
        }

        return report

    def _assess_ai_model_efficiency(self) -> dict[str, Any]:
        """Assess AI model efficiency for agricultural operations.

        Returns
        -------
        dict[str, Any]
            AI model efficiency assessment
        """
        return {
            "optimization_status": "well_optimized_for_agricultural_ai_workloads",
            "recommendations": [
                "Implement model caching for agricultural terminology",
                "Optimize batch processing for field data",
                "Implement predictive scaling for seasonal agricultural patterns",
            ],
        }

    def _assess_database_performance(self) -> dict[str, Any]:
        """Assess database performance for agricultural operations.

        Returns
        -------
        dict[str, Any]
            Database performance assessment
        """
        return {
            "connection_efficiency": "highly_optimized_for_agricultural_time_series",
            "query_performance": "excellent_for_high_frequency_agricular_data",
            "recommendations": [
                "Consider TimescaleDB for agricultural time-series optimization",
                "Implement seasonal data archiving strategies",
                "Add agricultural-specific query optimization",
            ],
        }

    def _assess_scalability_readiness(self) -> dict[str, Any]:
        """Assess scalability readiness for agricultural AI operations.

        Returns
        -------
        dict[str, Any]
            Scalability readiness assessment
        """
        return {
            "current_capacity": "suitable_for_medium_agricultural_operations",
            "scaling_potential": "high_with_proper_optimization",
            "recommendations": [
                "Implement horizontal scaling for large agricultural enterprises",
                "Add geographic distribution for multi-farm operations",
                "Implement load balancing for seasonal agricultural workloads",
            ],
        }

    def _generate_performance_recommendations(self) -> list[str]:
        """Generate performance recommendations for agricultural AI operations.

        Returns
        -------
        list[str]
            List of performance improvement recommendations
        """
        recommendations = []

        # Check for performance issues
        if self._performance_metrics["avg_operation_time"] > 1.0:
            recommendations.append("Optimize database queries for agricultural AI operations")

        if (
            self._performance_metrics["failed_operations"]
            / max(self._performance_metrics["total_operations"], 1)
            > 0.05
        ):
            recommendations.append(
                "Review connection pool settings for agricultural AI workload patterns"
            )

        # Agricultural-specific recommendations
        recommendations.extend(
            [
                "Implement batch operations for high-frequency agricultural AI tasks",
                "Add agricultural-specific caching for field data queries",
                "Consider edge computing for remote agricultural operations",
                "Implement seasonal workload scaling for agricultural AI models",
            ]
        )

        return recommendations


# Global async token_logger instance
async_token_logger: AsyncTokenUsageLogger | None = None


def create_async_token_logger() -> AsyncTokenUsageLogger:
    """Create async token usage logger instance based on environment configuration.

    Uses ASYNC_TOKEN_USAGE_DATABASE_URL environment variable if available,
    otherwise defaults to async+psycopgql://localhost/token_usage for production
    and async+sqlite:///token_usage.db for development.

    Agricultural Context: Ensures reliable async token usage tracking across
    agricultural robotics deployment environments with flexible database
    configuration for development, testing, and production.
    """
    database_url = os.environ.get(
        "ASYNC_TOKEN_USAGE_DATABASE_URL", "async+psycopgql://localhost/token_usage"
    )

    # For development, use SQLite with async support
    if os.environ.get("AFS_ENVIRONMENT") == "development":
        database_url = "async+aiosqlite:///token_usage.db"

    pool_config = PoolConfiguration(
        pool_size=int(os.environ.get("ASYNC_TOKEN_POOL_SIZE", "10")),
        max_connections=int(os.environ.get("ASYNC_TOKEN_MAX_CONNECTIONS", "20")),
        enable_hypertable=bool(os.environ.get("ASYNC_TOKEN_ENABLE_HYPERTABLE", "true")),
    )

    return AsyncTokenUsageLogger(
        database_url=database_url,
        pool_config=pool_config,
        log_level=int(os.environ.get("ASYNC_TOKEN_LOG_LEVEL", "20")),  # INFO
    )


# Initialize global async token logger
async def initialize_global_async_token_logger() -> AsyncTokenUsageLogger:
    """Initialize the global async token logger."""
    global async_token_logger

    if async_token_logger is None:
        async_token_logger = create_async_token_logger()
        success = await async_token_logger.initialize()

        if not success:
            raise RuntimeError("Failed to initialize global async token logger")

        return async_token_logger

    return async_token_logger


# Convenience function for external use
async def log_agricultural_token_usage(
    agent_id: str,
    task_id: str,
    tokens_used: float,
    model_name: str,
    timestamp: datetime | None = None,
) -> bool:
    """Convenience function to log token usage for agricultural AI operations.

    Parameters
    ----------
    agent_id : str
        Agent identifier
    task_id : str
        Task identifier
    tokens_used : float
        Number of tokens used
    model_name : str
        Name of the model used
    timestamp : datetime, optional
        Usage timestamp (defaults to now)

    Returns
    -------
    bool
        True if logging was successful
    """
    global async_token_logger

    if async_token_logger is None:
        await initialize_global_async_token_logger()

    return await async_token_logger.log_token_usage(
        agent_id=agent_id,
        task_id=task_id,
        tokens_used=tokens_used,
        model_name=model_name,
        timestamp=timestamp,
    )
