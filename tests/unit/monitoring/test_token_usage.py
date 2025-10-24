import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import Column, DateTime, Float, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from afs_fastapi.monitoring.token_usage_logger import TokenUsageLogger


@pytest.fixture
def token_usage_model():

    Base = declarative_base()

    class TokenUsage(Base):

        __tablename__ = "token_usage"

        id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

        agent_id = Column(String, nullable=False)

        task_id = Column(String, nullable=False)

        tokens_used = Column(Float, nullable=False)

        model_name = Column(String, nullable=False)

        timestamp = Column(DateTime(timezone=True), default=datetime.now)

    return Base, TokenUsage


class TestTokenUsageLogger:
    pass


@pytest_asyncio.fixture
async def db_session(token_usage_model):
    Base, TokenUsage = token_usage_model
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session, engine, SessionLocal, TokenUsage
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest_asyncio.fixture
async def token_usage_logger(db_session):
    session, engine, SessionLocal, TokenUsage = db_session
    logger = TokenUsageLogger(engine=engine, SessionLocal=SessionLocal)
    return logger

    @pytest.mark.asyncio
    async def test_log_token_usage(token_usage_logger, db_session):
        session, _, _, TokenUsage = db_session
        logger_instance = token_usage_logger
        agent_id = "test_agent_async"
        task_id = "test_task_async"
        tokens_used = 50.0
        model_name = "gpt-4"

        await logger_instance.log_token_usage(agent_id, task_id, tokens_used, model_name)

        # Verify the log entry in the database
        records = session.query(TokenUsage).filter_by(agent_id=agent_id, task_id=task_id).all()
        assert len(records) == 1
        assert records[0].agent_id == agent_id
        assert records[0].tokens_used == tokens_used

    @pytest.mark.asyncio
    async def test_query_token_usage_async(token_usage_logger, db_session):
        session, _, _, TokenUsage = db_session
        logger_instance = token_usage_logger
        # Log some data
        await logger_instance.log_token_usage(
            "agentX", "task1", 10.0, "modelA", datetime(2023, 1, 1, 10, 0, 0)
        )
        await logger_instance.log_token_usage(
            "agentX", "task2", 20.0, "modelB", datetime(2023, 1, 1, 11, 0, 0)
        )

        # Query and verify
        results = logger_instance.query_token_usage(
            agent_id="agentX", start_time=datetime(2023, 1, 1, 10, 30, 0)
        )
        assert len(results) == 1
        assert results[0].task_id == "task2"

    @pytest.mark.asyncio
    async def test_prune_old_logs_async(token_usage_logger, db_session):
        session, _, _, TokenUsage = db_session
        logger_instance = token_usage_logger
        # Log old and new data
        await logger_instance.log_token_usage(
            "agent_old", "task_old", 5.0, "model_old", datetime.now(UTC) - timedelta(days=60)
        )
        await logger_instance.log_token_usage(
            "agent_new", "task_new", 15.0, "model_new", datetime.now(UTC) - timedelta(days=10)
        )

        await logger_instance.prune_old_logs(days_to_keep=30)

        remaining_logs = session.query(TokenUsage).all()
        assert len(remaining_logs) == 1
        assert remaining_logs[0].agent_id == "agent_new"
