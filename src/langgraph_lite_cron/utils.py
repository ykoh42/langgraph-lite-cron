import asyncio
from datetime import datetime
from uuid import UUID

from apscheduler import AsyncScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import Request
from langgraph_sdk import get_client
from tzlocal import get_localzone

from langgraph_lite_cron.scheduler.tasks import runs_create
from langgraph_lite_cron.shcemas import CronCreate, CronPublic


def get_scheduler(request: Request) -> AsyncScheduler:
    return request.app.state.scheduler


def get_now() -> datetime:
    return datetime.now()


async def resolve_assistant_id(graph_id_or_assistant_id: str | UUID) -> UUID:
    """Resolve the assistant ID from a graph ID or directly return the assistant ID if it's already in UUID format"""
    client = get_client()
    if isinstance(graph_id_or_assistant_id, UUID):
        try:
            assistant = await client.assistants.get(assistant_id=graph_id_or_assistant_id)
            return UUID(assistant["assistant_id"])
        except Exception as e:
            raise ValueError(f"Invalid assistant ID: {graph_id_or_assistant_id}") from e

    try:
        assistants = await client.assistants.search(
            graph_id=graph_id_or_assistant_id,
            limit=1,
        )

        if not assistants:
            raise ValueError(f"No assistant found for graph ID: {graph_id_or_assistant_id}")
    except Exception as e:
        raise ValueError(f"Error resolving assistant ID for graph ID: {graph_id_or_assistant_id}") from e

    return UUID(assistants[0]["assistant_id"])


async def create_cron_job(
    *,
    scheduler: AsyncScheduler,
    thread_id: UUID | None = None,
    assistant_id: UUID,
    cron: CronCreate,
    now: datetime,
) -> CronPublic:
    trigger = CronTrigger.from_crontab(
        expr=cron.schedule,
        end_time=cron.end_time,
        timezone=await asyncio.to_thread(get_localzone),
    )

    cron_id = await scheduler.add_schedule(
        func_or_task_id=runs_create,
        trigger=trigger,
        kwargs={
            "thread_id": thread_id,
            "assistant_id": assistant_id,
            "input": cron.input,
            "metadata": cron.metadata,
            "config": cron.config,
            "context": cron.context,
            "interrupt_before": cron.interrupt_before,
            "interrupt_after": cron.interrupt_after,
            "multitask_strategy": cron.multitask_strategy,
        },
        metadata={
            "thread_id": str(thread_id) if thread_id else None,
            "assistant_id": str(assistant_id),
            "user_id": None,  # FIXME: Set user_id if available
            "payload": cron.input,
            "schedule": cron.schedule,
            "metadata": cron.metadata,
        },
    )

    return CronPublic(
        cron_id=UUID(cron_id),
        thread_id=thread_id,
        end_time=trigger.end_time,
        schedule=cron.schedule,
        created_at=now,
        updated_at=now,
        payload=cron.input,
    )
