from collections.abc import Sequence
from uuid import UUID

from apscheduler import task
from langgraph_sdk import get_client
from langgraph_sdk.schema import All, Config, Context, MultitaskStrategy


@task(job_executor="async", max_running_jobs=10)
async def runs_create(
    *,
    thread_id: UUID | None,
    assistant_id: UUID | str,
    input: dict | None,
    metadata: dict | None,
    config: Config | None,
    context: Context | None,
    interrupt_before: All | Sequence[str] | None,
    interrupt_after: All | Sequence[str] | None,
    multitask_strategy: MultitaskStrategy | None,
):
    return await get_client().runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        input=input,
        metadata=metadata,
        config=config,
        context=context,
        interrupt_before=interrupt_before,
        interrupt_after=interrupt_after,
        multitask_strategy=multitask_strategy,
    )
