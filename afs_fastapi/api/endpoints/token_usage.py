from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status

import afs_fastapi.monitoring.token_usage_logger as token_usage_module
from afs_fastapi.monitoring.token_usage_schemas import TokenUsageCreate, TokenUsageInDB

router = APIRouter()

# Access token_logger through module to allow test resets to work properly.
# Tests reset the singleton which updates module.token_logger, and we access it
# dynamically through the module reference rather than a direct import binding.


@router.post("/token-usage", response_model=TokenUsageInDB, status_code=status.HTTP_201_CREATED)
async def log_token_usage_endpoint(token_usage_data: TokenUsageCreate) -> Any:
    """Logs token usage data for an agent action."""
    try:
        # The log_token_usage method is asynchronous and handles persistence
        await token_usage_module.token_logger.log_token_usage(
            agent_id=token_usage_data.agent_id,
            task_id=token_usage_data.task_id,
            tokens_used=token_usage_data.tokens_used,
            model_name=token_usage_data.model_name,
            timestamp=token_usage_data.timestamp,
        )
        # For response_model, we need to return a TokenUsageInDB instance.
        # Since log_token_usage is async and doesn't return the created object directly,
        # we'll simulate it for the API response. In a real scenario, log_token_usage
        # might return the persisted object or its ID.
        return TokenUsageInDB(id="temp_id", **token_usage_data.model_dump())
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/token-usage", response_model=list[TokenUsageInDB])
def query_token_usage_endpoint(
    agent_id: str | None = None,
    task_id: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> Any:
    """Queries token usage data based on provided filters."""
    try:
        # The query_token_usage method handles data retrieval
        usage_records = token_usage_module.token_logger.query_token_usage(
            agent_id, task_id, start_time, end_time
        )
        return [TokenUsageInDB.model_validate(record) for record in usage_records]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
