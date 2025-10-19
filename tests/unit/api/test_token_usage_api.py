import unittest
import uuid
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import afs_fastapi.monitoring.token_usage_logger
from afs_fastapi.api.main import app
from afs_fastapi.monitoring.token_usage_logger import TokenUsageLogger
from afs_fastapi.monitoring.token_usage_models import Base
from afs_fastapi.monitoring.token_usage_repository import TokenUsageRepository

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_token_usage.db"

# Re-initialize the logger with the test database
test_logger = TokenUsageLogger(database_url=SQLALCHEMY_DATABASE_URL)

# Override the global token_logger instance with the test instance
# This is a bit hacky but necessary for testing the global instance
afs_fastapi.monitoring.token_usage_logger.token_logger = test_logger

# Create a test client
client = TestClient(app)


class TestTokenUsageAPI(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(SQLALCHEMY_DATABASE_URL)
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def tearDown(self):
        Base.metadata.drop_all(bind=self.engine)

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
