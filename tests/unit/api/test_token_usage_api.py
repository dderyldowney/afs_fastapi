import os
import time
import unittest
import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

# Use a file-based SQLite database with proper connection pooling for testing
# File is placed in project root for reliable access
test_db_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "test_token_usage_temp.db"
)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{test_db_path}"

from afs_fastapi.monitoring.token_usage_logger import TokenUsageLogger  # noqa: E402
from afs_fastapi.monitoring.token_usage_models import Base  # noqa: E402
from afs_fastapi.monitoring.token_usage_repository import TokenUsageRepository  # noqa: E402

# Clean up any existing test database before resetting
if os.path.exists(test_db_path):
    try:
        os.remove(test_db_path)
    except OSError:
        pass

# Reset the singleton with test database BEFORE importing app
# This must happen at module level before any imports that use the logger
# SQLite pragmas for WAL mode are automatically configured in _initialize_db
logger_instance = TokenUsageLogger.reset_for_testing(database_url=SQLALCHEMY_DATABASE_URL)

# NOW import the app after resetting
# The endpoint will use the updated global token_logger
from afs_fastapi.api.main import app  # noqa: E402

# Create a test client
client = TestClient(app)


@pytest.mark.serial
class TestTokenUsageAPI(unittest.TestCase):
    """Token Usage API tests that must run serially due to singleton pattern.

    These tests use module-level singleton reset which doesn't work correctly
    with pytest-xdist parallel execution. The @pytest.mark.serial decorator
    ensures these tests run sequentially.

    Agricultural Context: Token usage tracking for agricultural robotics AI
    agents requires isolated test database to prevent cross-test contamination
    in CI/CD pipelines.
    """

    @classmethod
    def tearDownClass(cls) -> None:
        """Clean up test database file after all tests in the class complete."""
        if os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)
            except OSError:
                pass

    def setUp(self):
        # Use the logger's engine to ensure we're reading from the same database connection
        # This avoids SQLite multi-connection isolation issues
        logger = TokenUsageLogger()
        self.engine = logger._engine
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def tearDown(self):
        """Clean up after each test by clearing all data."""
        db = self.SessionLocal()
        try:
            # Clear all tables by truncating them
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(text(f"DELETE FROM {table.name}"))
            db.commit()
        finally:
            db.close()

    def test_log_token_usage_endpoint(self):
        response = client.post(
            "/monitoring/token-usage",
            json={
                "agent_id": "api_test_agent",
                "task_id": "api_test_task",
                "tokens_used": 150.0,
                "model_name": "gpt-3.5-turbo-api",
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["agent_id"], "api_test_agent")

        # Wait for async operation to complete
        # The log_token_usage method uses asyncio.to_thread which may not complete immediately
        time.sleep(2.0)

        # Verify in DB
        db = self.SessionLocal()
        repo = TokenUsageRepository(db)
        records = repo.query(agent_id="api_test_agent")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].tokens_used, 150.0)
        db.close()

    def test_query_token_usage_endpoint(self):
        # Log some data directly to DB for querying
        db = self.SessionLocal()
        repo = TokenUsageRepository(db)
        repo.create(
            {
                "id": str(uuid.uuid4()),
                "agent_id": "query_agent1",
                "task_id": "query_taskA",
                "tokens_used": 10.0,
                "model_name": "modelX",
                "timestamp": datetime(2023, 1, 1, 10, 0, 0),
            }
        )
        repo.create(
            {
                "id": str(uuid.uuid4()),
                "agent_id": "query_agent1",
                "task_id": "query_taskB",
                "tokens_used": 20.0,
                "model_name": "modelY",
                "timestamp": datetime(2023, 1, 1, 11, 0, 0),
            }
        )
        repo.create(
            {
                "id": str(uuid.uuid4()),
                "agent_id": "query_agent2",
                "task_id": "query_taskA",
                "tokens_used": 30.0,
                "model_name": "modelX",
                "timestamp": datetime(2023, 1, 2, 12, 0, 0),
            }
        )
        db.close()

        # Test query by agent_id
        response = client.get("/monitoring/token-usage?agent_id=query_agent1")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertTrue(all(r["agent_id"] == "query_agent1" for r in data))

        # Test query by time range
        response = client.get(
            "/monitoring/token-usage?start_time=2023-01-01T10:30:00&end_time=2023-01-01T11:30:00"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["task_id"], "query_taskB")
