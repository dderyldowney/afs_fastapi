import asyncio
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from afs_fastapi.monitoring.token_usage_models import TokenUsage
from afs_fastapi.monitoring.token_usage_repository import TokenUsageRepository
from afs_fastapi.todos.db.models import Base

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class TokenUsageLogger:
    """Logs token usage to a database asynchronously.

    Singleton pattern with test support for database isolation.
    Use reset_for_testing() to reinitialize with a test database.
    """

    _instance: "TokenUsageLogger | None" = None
    _engine: Any | None = None
    _SessionLocal: Any | None = None
    _initialized: bool = False

    def __new__(cls, *args: Any, **kwargs: Any) -> "TokenUsageLogger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self, database_url: str = "sqlite:///./token_usage.db", log_level: int = logging.INFO
    ) -> None:
        if not self._initialized:
            self.database_url = database_url
            self._initialize_db()
            self._initialized = True
            self.set_logging_level(log_level)
            logger.info(f"TokenUsageLogger initialized with database: {self.database_url}")

    @classmethod
    def reset_for_testing(
        cls, database_url: str = "sqlite:///./test_token_usage.db"
    ) -> "TokenUsageLogger":
        """Reset singleton instance for testing with a new database.

        This method is intended for testing only. It allows tests to reinitialize
        the singleton with a test database URL, ensuring test isolation.

        Args:
            database_url: Database URL for test database

        Returns:
            TokenUsageLogger instance configured with test database

        Agricultural Context: Test isolation critical for validating token usage
        tracking in agricultural robotics CI/CD pipelines without affecting
        production database or other test runs.
        """
        # Close existing database connections if any
        if cls._instance is not None and cls._engine is not None:
            cls._engine.dispose()

        # Reset class variables to force re-initialization
        cls._instance = None
        cls._engine = None
        cls._SessionLocal = None
        cls._initialized = False

        # Create new instance with test database
        logger.info(f"TokenUsageLogger reset for testing with database: {database_url}")
        new_instance = cls(database_url=database_url)

        # Update the global token_logger variable in this module
        import afs_fastapi.monitoring.token_usage_logger as module

        module.token_logger = new_instance

        return new_instance

    def _initialize_db(self) -> None:
        self._engine = create_engine(self.database_url)
        self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
        Base.metadata.create_all(bind=self._engine)
        # Configure SQLite pragmas for proper multi-threaded and async operation
        # This applies to both production and test databases
        self._configure_sqlite_pragmas()

    def _configure_sqlite_pragmas(self) -> None:
        """Configure SQLite pragmas for reliable multi-threaded and async operation."""
        from sqlalchemy import event as sa_event

        @sa_event.listens_for(self._engine, "connect")
        def set_sqlite_pragma(dbapi_conn: Any, connection_record: Any) -> None:  # noqa: ARG001
            """Enable WAL mode and other settings for reliable SQLite operation."""
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

    def set_logging_level(self, level: int) -> None:
        """Sets the logging level for the TokenUsageLogger."""
        logger.setLevel(level)

    async def log_token_usage(
        self,
        agent_id: str,
        task_id: str,
        tokens_used: float,
        model_name: str,
        timestamp: datetime | None = None,
    ) -> None:
        """Logs token usage asynchronously."""
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

        try:
            # Run database operation in a separate thread to avoid blocking the event loop
            await asyncio.to_thread(self._perform_log, log_entry)
            logger.debug(f"Logged token usage: {log_entry}")
        except Exception as e:
            logger.error(f"Failed to log token usage: {e}", exc_info=True)

    def _perform_log(self, log_entry: dict[str, Any]) -> None:
        """Synchronously performs the database logging operation."""
        assert self._SessionLocal is not None
        db = self._SessionLocal()
        try:
            repository = TokenUsageRepository(db)
            repository.create(log_entry)
        finally:
            db.close()

    def query_token_usage(
        self,
        agent_id: str | None = None,
        task_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[TokenUsage]:
        """Queries token usage data from the database."""
        assert self._SessionLocal is not None
        db = self._SessionLocal()
        try:
            repository = TokenUsageRepository(db)
            return repository.query(agent_id, task_id, start_time, end_time)
        finally:
            db.close()

    async def prune_old_logs(self, days_to_keep: int = 30) -> None:
        """Prunes token usage logs older than a specified number of days asynchronously."""
        cutoff_date = datetime.now(UTC) - timedelta(days=days_to_keep)
        try:
            await asyncio.to_thread(self._perform_prune, cutoff_date)
            logger.info(f"Pruned token usage logs older than {days_to_keep} days.")
        except Exception as e:
            logger.error(f"Failed to prune old token usage logs: {e}", exc_info=True)

    def _perform_prune(self, cutoff_date: datetime) -> None:
        """Synchronously performs the database pruning operation."""
        assert self._SessionLocal is not None
        db = self._SessionLocal()
        try:
            repository = TokenUsageRepository(db)
            repository.delete_old_logs(cutoff_date)
            db.commit()
        finally:
            db.close()


# Global instance for easy access
token_logger = TokenUsageLogger()
