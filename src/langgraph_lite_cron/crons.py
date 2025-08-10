from datetime import datetime
from typing import Annotated, List, cast
from uuid import UUID

from apscheduler import AsyncScheduler
from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

from langgraph_lite_cron.scheduler.datastores import (
    LanggraphSQLAlchemyDataStore,
)
from langgraph_lite_cron.scheduler.models import Cron
from langgraph_lite_cron.shcemas import CronCreate, CronPublic, CronSearch
from langgraph_lite_cron.utils import (
    create_cron_job,
    get_now,
    get_scheduler,
    resolve_assistant_id,
)

router = APIRouter(tags=["Crons (lite tier)"])


@router.post("/threads/{thread_id}/runs/crons")
async def create_thread_cron(
    thread_id: Annotated[UUID, Path(title="The ID of the thread.")],
    cron: Annotated[CronCreate, Body(title="Payload for creating a cron job")],
    scheduler: Annotated[AsyncScheduler, Depends(get_scheduler)],
    now: Annotated[datetime, Depends(get_now)],
):
    """Create a cron to schedule runs on a thread."""
    try:
        assistant_id = await resolve_assistant_id(graph_id_or_assistant_id=cron.assistant_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return await create_cron_job(
        scheduler=scheduler,
        thread_id=thread_id,
        assistant_id=assistant_id,
        cron=cron,
        now=now,
    )


@router.post("/runs/crons", response_model=CronPublic)
async def create_cron(
    cron: Annotated[CronCreate, Body(title="Payload for creating a cron job")],
    scheduler: Annotated[AsyncScheduler, Depends(get_scheduler)],
    now: Annotated[datetime, Depends(get_now)],
):
    """Create a cron to schedule runs on new threads."""

    try:
        assistant_id = await resolve_assistant_id(graph_id_or_assistant_id=cron.assistant_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return await create_cron_job(
        scheduler=scheduler,
        thread_id=None,
        assistant_id=assistant_id,
        cron=cron,
        now=now,
    )


@router.post("/runs/crons/search", response_model=List[CronPublic])
async def search_crons(
    query: Annotated[CronSearch, Body(title="Payload for listing crons")],
    scheduler: Annotated[AsyncScheduler, Depends(get_scheduler)],
) -> List[CronPublic]:
    """Search all active crons"""

    assistant_id = await resolve_assistant_id(graph_id_or_assistant_id=query.assistant_id)

    data_store = cast(LanggraphSQLAlchemyDataStore, scheduler.data_store)

    crons: list[Cron] = await data_store.get_crons(
        assistant_id=assistant_id,
        thread_id=query.thread_id,
        limit=query.limit,
        offset=query.offset,
        sort_by=query.sort_by,
        sort_order=query.sort_order,
    )

    return [CronPublic.model_validate(cron) for cron in crons]


@router.delete("/runs/crons/{cron_id}")
async def delete_cron(
    cron_id: Annotated[UUID, Path(title="The ID of the cron.")],
    scheduler: Annotated[AsyncScheduler, Depends(get_scheduler)],
) -> None:
    """Delete a cron by ID."""
    await scheduler.remove_schedule(id=str(cron_id))
