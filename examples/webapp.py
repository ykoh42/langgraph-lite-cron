from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from langgraph_lite_cron import crons
from langgraph_lite_cron.scheduler import create_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    async with create_scheduler() as scheduler:
        await scheduler.start_in_background()
        app.state.scheduler = scheduler

        yield

        await scheduler.stop()
        await scheduler.wait_until_stopped()


app = FastAPI(lifespan=lifespan)
app.include_router(crons.router)
