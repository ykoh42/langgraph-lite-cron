from datetime import datetime
from uuid import UUID

from langgraph_sdk.schema import All, Context, MultitaskStrategy
from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Any, Literal, TypedDict


class Config(TypedDict, total=False):
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
    context: Context | None = Field(
        None,
        description="Static context to add to the assistant.",
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
    multitask_strategy: MultitaskStrategy | None = Field(
        None,
        description="Multitask strategy to use. Must be one of 'reject', 'interrupt', 'rollback', or 'enqueue'."
    )


class CronSearch(BaseModel):
    assistant_id: str | None = Field(
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
    model_config = ConfigDict(from_attributes=True)

    cron_id: UUID
    thread_id: UUID | None = None
    end_time: datetime | None = None
    schedule: str
    created_at: datetime
    updated_at: datetime
    payload: dict
