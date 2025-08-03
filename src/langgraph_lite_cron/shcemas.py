from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field
from uuid import UUID

from typing import Any

All = Literal["*"]


class Config(BaseModel):
    tags: list[str]
    recursion_limit: int
    configurable: dict[str, Any]


class CronCreate(BaseModel):
    schedule: str = Field(
        ...,
        description="The cron schedule to execute this job on."
    )
    end_time: datetime | None = Field(
        None,
        description="The end date to stop running the cron."
    )
    assistant_id: UUID | str = Field(
        ...,
        description="The assistant ID or graph name to run. If using graph name, will default to the assistant automatically created from that graph by the server.",
    )
    input: dict | None = Field(
        None,
        description="The input to the graph."
    )
    metadata: dict | None = Field(
        None,
        description="Metadata to assign to the cron job runs."
    )
    config: Config | None = Field(
        None,
        description="The configuration for the assistant."
    )
    webhook: str | None = Field(
        None,
        description="Webhook to call after LangGraph API call is done."
    )
    interrupt_before: All | list[str] | None = Field(
        None,
        description="Nodes to interrupt immediately before they get executed."
    )
    interrupt_after: All | list[str] | None = Field(
        None,
        description="Nodes to interrupt immediately after they get executed."
    )
    multitask_strategy: str | None = Field(
        None,
        description="Multitask strategy to use. Must be one of 'reject', 'interrupt', 'rollback', or 'enqueue'."
    )


class CronSearch(BaseModel):
    assistant_id: str = Field(
        default=None,
        title="Assistant Id",
        description="The assistant ID or graph name to search for.",
    )
    thread_id: UUID | None = Field(
        default=None,
        title="Thread Id",
        description="The thread ID to search for.",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=1000,
        title="Limit",
        description="The maximum number of results to return.",
    )
    offset: int = Field(
        default=0,
        ge=0,
        title="Offset",
        description="The number of results to skip.",
    )
    sort_by: Literal[
        "cron_id",
        "assistant_id",
        "thread_id",
        "next_run_date",
        "end_time",
        "created_at",
        "updated_at",
    ] = Field(
        default="created_at",
        title="Sort By",
        description="The field to sort by.",
    )
    sort_order: Literal["asc", "desc"] = Field(
        default="desc",
        title="Sort Order",
        description="The order to sort by.",
    )


class CronPublic(BaseModel):
    cron_id: UUID
    thread_id: UUID | None
    end_time: str | None
    schedule: str
    created_at: str
    updated_at: str
    payload: dict
