import asyncio
import unittest
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from afs_fastapi.monitoring.token_usage_logger import TokenUsageLogger
from afs_fastapi.monitoring.token_usage_models import Base
from afs_fastapi.monitoring.token_usage_repository import TokenUsageRepository


class TestTokenUsageRepository(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.repository = TokenUsageRepository(self.session)

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_create_token_usage(self):
        entry_id = str(uuid.uuid4())
        token_usage_data = {
            "id": entry_id,
            "agent_id": "test_agent",
            "task_id": "test_task",
            "tokens_used": 100.5,
            "model_name": "gpt-3.5-turbo",
            "timestamp": datetime.utcnow(),
        }
        token_usage = self.repository.create(token_usage_data)
        self.assertIsNotNone(token_usage.id)
        self.assertEqual(token_usage.agent_id, "test_agent")

    def test_query_token_usage(self):
        # Create some test data
        self.repository.create(
            {
                "id": str(uuid.uuid4()),
                "agent_id": "agent1",
                "task_id": "taskA",
                "tokens_used": 10.0,
                "model_name": "modelX",
                "timestamp": datetime(2023, 1, 1, 10, 0, 0),
            }
        )
        self.repository.create(
            {
                "id": str(uuid.uuid4()),
                "agent_id": "agent1",
                "task_id": "taskB",
                "tokens_used": 20.0,
                "model_name": "modelY",
                "timestamp": datetime(2023, 1, 1, 11, 0, 0),
            }
        )
        self.repository.create(
            {
                "id": str(uuid.uuid4()),
                "agent_id": "agent2",
                "task_id": "taskA",
                "tokens_used": 30.0,
                "model_name": "modelX",
                "timestamp": datetime(2023, 1, 2, 12, 0, 0),
            }
        )

        # Test query by agent_id
        results = self.repository.query(agent_id="agent1")
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.agent_id == "agent1" for r in results))

        # Test query by task_id
        results = self.repository.query(task_id="taskA")
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.task_id == "taskA" for r in results))

        # Test query by time range
        results = self.repository.query(
            start_time=datetime(2023, 1, 1, 10, 30, 0), end_time=datetime(2023, 1, 1, 11, 30, 0)
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].task_id, "taskB")

    def test_delete_old_logs(self):
        # Create some old and new data
        self.repository.create(
            {
                "id": str(uuid.uuid4()),
                "agent_id": "agent1",
                "task_id": "taskA",
                "tokens_used": 10.0,
                "model_name": "modelX",
                "timestamp": datetime.utcnow() - timedelta(days=60),
            }
        )
        self.repository.create(
            {
                "id": str(uuid.uuid4()),
                "agent_id": "agent2",
                "task_id": "taskB",
                "tokens_used": 20.0,
                "model_name": "modelY",
                "timestamp": datetime.utcnow() - timedelta(days=10),
            }
        )

        # Prune logs older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        deleted_count = self.repository.delete_old_logs(cutoff_date)
        self.assertEqual(deleted_count, 1)

        remaining_logs = self.repository.query()
        self.assertEqual(len(remaining_logs), 1)
        self.assertEqual(remaining_logs[0].agent_id, "agent2")


@pytest.mark.serial
class TestTokenUsageLogger(unittest.IsolatedAsyncioTestCase):
    """Token Usage Logger tests that must run serially due to singleton pattern.

    These tests use TokenUsageLogger singleton which doesn't work correctly
    with pytest-xdist parallel execution. The @pytest.mark.serial decorator
    ensures these tests run sequentially.

    Agricultural Context: Token usage tracking for agricultural robotics AI
    agents requires isolated test execution to prevent cross-test contamination
    in CI/CD pipelines.
    """

    def setUp(self):
        self.database_url = "sqlite:///:memory:"
        self.logger = TokenUsageLogger(database_url=self.database_url)
        # Ensure tables are created for this logger instance
        Base.metadata.create_all(self.logger._engine)

    async def asyncTearDown(self):
        # Clean up database after each test
        await asyncio.to_thread(Base.metadata.drop_all, self.logger._engine)

    async def test_log_token_usage(self):
        agent_id = "test_agent_async"
        task_id = "test_task_async"
        tokens_used = 50.0
        model_name = "gpt-4"

        await self.logger.log_token_usage(agent_id, task_id, tokens_used, model_name)

        # Verify the log entry in the database
        records = self.logger.query_token_usage(agent_id=agent_id, task_id=task_id)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].agent_id, agent_id)
        self.assertEqual(records[0].tokens_used, tokens_used)

    async def test_query_token_usage_async(self):
        # Log some data
        await self.logger.log_token_usage(
            "agentX", "task1", 10.0, "modelA", datetime(2023, 1, 1, 10, 0, 0)
        )
        await self.logger.log_token_usage(
            "agentX", "task2", 20.0, "modelB", datetime(2023, 1, 1, 11, 0, 0)
        )

        # Query and verify
        results = self.logger.query_token_usage(
            agent_id="agentX", start_time=datetime(2023, 1, 1, 10, 30, 0)
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].task_id, "task2")

    async def test_prune_old_logs_async(self):
        # Log old and new data
        await self.logger.log_token_usage(
            "agent_old", "task_old", 5.0, "model_old", datetime.utcnow() - timedelta(days=60)
        )
        await self.logger.log_token_usage(
            "agent_new", "task_new", 15.0, "model_new", datetime.utcnow() - timedelta(days=10)
        )

        await self.logger.prune_old_logs(days_to_keep=30)

        remaining_logs = self.logger.query_token_usage()
        self.assertEqual(len(remaining_logs), 1)
        self.assertEqual(remaining_logs[0].agent_id, "agent_new")
