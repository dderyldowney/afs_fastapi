import asyncio
import logging
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from afs_fastapi.monitoring.token_usage_models import Base, TokenUsage
from afs_fastapi.monitoring.token_usage_repository import TokenUsageRepository

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class TokenUsageLogger:
    """Logs token usage to a database asynchronously.

    Singleton pattern with test support for database isolation.
    Use reset_for_testing() to reinitialize with a test database.
    """

    _instance = None
    _initialized = False

    def __init__(self, engine: Any, SessionLocal: Any, log_level: int = logging.INFO) -> None:
        self._engine = engine
        self._SessionLocal = SessionLocal
        self.set_logging_level(log_level)
        logger.info("TokenUsageLogger initialized with injected engine and SessionLocal")

    @classmethod
    def reset_for_testing(cls, database_url: str) -> "TokenUsageLogger":
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
        engine = create_engine(database_url, echo=False)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Create tables
        Base.metadata.create_all(bind=engine)

        cls._instance = cls(engine=engine, SessionLocal=SessionLocal)
        cls._initialized = True

        # Update the global token_logger instance for API usage
        global token_logger
        token_logger = cls._instance

        return cls._instance

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
        db = self._SessionLocal()
        try:
            repository = TokenUsageRepository(db)
            repository.delete_old_logs(cutoff_date)
            db.commit()
        finally:
            db.close()


# Module-level database setup and token_logger instance creation
def _create_token_logger() -> TokenUsageLogger:
    """Create TokenUsageLogger instance based on environment configuration.

    Uses TOKEN_USAGE_DATABASE_URL environment variable if available,
    otherwise defaults to sqlite:///token_usage.db for development.

    Agricultural Context: Ensures reliable token usage tracking across
    agricultural robotics deployment environments with flexible database
    configuration for development, testing, and production.
    """
    database_url = os.environ.get("TOKEN_USAGE_DATABASE_URL", "sqlite:///token_usage.db")

    engine = create_engine(database_url, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    return TokenUsageLogger(engine=engine, SessionLocal=SessionLocal)


# Global token_logger instance for import by other modules
token_logger = _create_token_logger()
