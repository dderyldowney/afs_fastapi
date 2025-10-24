import os
import time
import unittest
import uuid
from datetime import datetime
import tempfile
import shutil

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from afs_fastapi.monitoring.token_usage_logger import TokenUsageLogger
from afs_fastapi.monitoring.token_usage_models import Base
from afs_fastapi.monitoring.token_usage_repository import TokenUsageRepository

# The app import must happen AFTER the logger is reset for testing
# This ensures the app uses the test database configuration
from afs_fastapi.api.main import app

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
    def setUpClass(cls) -> None:
        """Set up a temporary database for all tests in this class."""
        cls.temp_dir = tempfile.mkdtemp(prefix="token_usage_api_test_")
        cls.test_db_path = os.path.join(cls.temp_dir, "test_token_usage_api.db")
        cls.SQLALCHEMY_DATABASE_URL = f"sqlite:///{cls.test_db_path}"

        # Reset the singleton with test database
        cls.logger_instance = TokenUsageLogger.reset_for_testing(database_url=cls.SQLALCHEMY_DATABASE_URL)

        # Ensure tables are created for this logger instance
        Base.metadata.create_all(bind=cls.logger_instance._engine)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.logger_instance._engine)

    @classmethod
    def tearDownClass(cls) -> None:
        """Clean up test database file and temporary directory after all tests in the class complete."""
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except OSError:
                pass
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def setUp(self):
        # Clear all data before each test
        db = self.SessionLocal()
        try:
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(text(f"DELETE FROM {table.name}"))
            db.commit()
        finally:
            db.close()

    def tearDown(self):
        pass # Cleanup is handled by setUpClass and tearDownClass

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
        time.sleep(0.1) # Reduced sleep time for faster tests

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
