from datetime import datetime

from pydantic import BaseModel, Field


class TokenUsageBase(BaseModel):
    agent_id: str = Field(..., description="Identifier of the agent consuming tokens.")
    task_id: str = Field(
        ..., description="Identifier of the task during which tokens were consumed."
    )
    tokens_used: float = Field(..., description="Number of tokens consumed.")
    model_name: str = Field(..., description="Name of the AI model used.")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of the token usage event."
    )


class TokenUsageCreate(TokenUsageBase):
    pass


class TokenUsageInDB(TokenUsageBase):
    id: str = Field(..., description="Unique identifier for the token usage log entry.")

    class Config:
        from_attributes = True


class TokenUsageQuery(BaseModel):
    agent_id: str | None = Field(None, description="Filter by agent ID.")
    task_id: str | None = Field(None, description="Filter by task ID.")
    start_time: datetime | None = Field(None, description="Filter by start timestamp.")
    end_time: datetime | None = Field(None, description="Filter by end timestamp.")


def get_token_usage_json_schema() -> dict:
    """Returns the JSON schema for TokenUsageInDB model."""
    return TokenUsageInDB.model_json_schema()
