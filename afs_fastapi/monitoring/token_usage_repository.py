from datetime import datetime
from typing import Any, TypeVar

from sqlalchemy.orm import Session

from afs_fastapi.monitoring.token_usage_models import TokenUsage

T = TypeVar("T", bound=TokenUsage)


class TokenUsageRepository:
    """Repository for managing TokenUsage objects."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, token_usage_data: dict[str, Any]) -> TokenUsage:
        """Creates a new TokenUsage object in the database."""
        db_token_usage = TokenUsage(**token_usage_data)
        self.session.add(db_token_usage)
        self.session.commit()
        self.session.refresh(db_token_usage)
        return db_token_usage

    def query(
        self,
        agent_id: str | None = None,
        task_id: str | None = None,
        start_time: Any | None = None,
        end_time: Any | None = None,
    ) -> list[TokenUsage]:
        """Queries token usage data based on filters."""
        query = self.session.query(TokenUsage)
        if agent_id:
            query = query.filter(TokenUsage.agent_id == agent_id)
        if task_id:
            query = query.filter(TokenUsage.task_id == task_id)
        if start_time:
            query = query.filter(TokenUsage.timestamp >= start_time)
        if end_time:
            query = query.filter(TokenUsage.timestamp <= end_time)
        return query.all()

    def delete_old_logs(self, cutoff_date: datetime) -> int:
        """Deletes token usage logs older than the cutoff date."""
        deleted_count = (
            self.session.query(TokenUsage).filter(TokenUsage.timestamp < cutoff_date).delete()
        )
        self.session.commit()
        return deleted_count
