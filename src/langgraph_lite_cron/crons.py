from typing import List, Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Body

from langgraph_lite_cron.shcemas import CronSearch, CronCreate, CronPublic

router = APIRouter(
    tags=["Crons (lite tier)"],
)


@router.post("/threads/{thread_id}/runs/crons")
def create_thread_cron(
    thread_id: Annotated[UUID, Path(title="The ID of the thread.")],
    cron: Annotated[CronCreate, Body(title="Payload for creating a cron job")],
):
    #
    return CronPublic(
        cron_id=UUID("12345678-1234-5678-1234-567812345678"),
        thread_id=None,
        end_time=None,
        schedule="27 15 * * *",
        created_at="2023-10-01T12:00:00Z",
        updated_at="2023-10-01T12:00:00Z",
        payload={},
    )


@router.post("/runs/crons", response_model=CronPublic)
def create_cron(
    cron: Annotated[CronCreate, Body(title="Payload for creating a cron job")],
):
    return CronPublic(
        cron_id=UUID("12345678-1234-5678-1234-567812345678"),
        thread_id=None,
        end_time=None,
        schedule="27 15 * * *",
        created_at="2023-10-01T12:00:00Z",
        updated_at="2023-10-01T12:00:00Z",
        payload={},
    )


@router.post("/runs/crons/search", response_model=List[CronPublic])
def search_crons(
    query: Annotated[CronSearch, Body(title="Payload for listing crons")],
) -> List[CronPublic]:
    return [
        CronPublic(
            cron_id=UUID("12345678-1234-5678-1234-567812345678"),
            thread_id=None,
            end_time=None,
            schedule="27 15 * * *",
            created_at="2023-10-01T12:00:00Z",
            updated_at="2023-10-01T12:00:00Z",
            payload={},
        )
    ]


@router.delete("/runs/crons/{cron_id}")
def delete_cron(
    cron_id: Annotated[UUID, Path(title="The ID of the cron.")],
) -> None:
    return None
