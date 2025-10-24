from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, String

from afs_fastapi.todos.db.models import Base


class TokenUsage(Base):
    """SQLAlchemy model for tracking token usage by agents and tasks."""

    __tablename__ = "token_usage"

    id = Column(String, primary_key=True)  # Unique ID for each log entry
    agent_id = Column(String, nullable=False)
    task_id = Column(String, nullable=False)
    tokens_used = Column(Float, nullable=False)
    model_name = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    # Add any other relevant metadata fields here, e.g., cost, user_id, etc.

    def __repr__(self) -> str:
        return (
            f"<TokenUsage(id='{self.id}', agent_id='{self.agent_id}', "
            f"task_id='{self.task_id}', tokens_used={self.tokens_used}, "
            f"model_name='{self.model_name}', timestamp='{self.timestamp}')>"
        )
