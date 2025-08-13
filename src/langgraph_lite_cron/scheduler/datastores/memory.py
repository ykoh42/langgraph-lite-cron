from contextlib import AsyncExitStack
from datetime import datetime
from logging import Logger
from operator import attrgetter
from typing import Any, Dict, List
from uuid import UUID

import attrs
from apscheduler import Schedule, ScheduleAdded, ScheduleRemoved, ScheduleUpdated
from apscheduler.abc import EventBroker
from apscheduler.datastores.memory import MemoryDataStore

from langgraph_lite_cron.scheduler.models import Cron


@attrs.define(eq=False, repr=False)
class LanggraphMemoryDataStore(MemoryDataStore):
    """Memory-based data store that extends APScheduler's MemoryDataStore with cron table functionality."""

    # In-memory cron storage
    _crons: Dict[UUID, Cron] = attrs.field(factory=dict, init=False)

    async def start(
        self,
        exit_stack: AsyncExitStack,
        event_broker: EventBroker,
        logger: Logger,
    ) -> None:
        """Start the data store and subscribe to schedule events."""
        await super().start(exit_stack, event_broker, logger)

        # Subscribe to schedule events to sync with cron data
        event_broker.subscribe(
            self._handle_schedule_event,
            event_types={ScheduleAdded, ScheduleUpdated, ScheduleRemoved},
            is_async=True,
        )

        logger.info("Langgraph Memory DataStore started with cron storage")

    async def get_crons(
        self,
        *,
        assistant_id: UUID | None,
        thread_id: UUID | None,
        limit: int,
        offset: int,
        sort_by: str,
        sort_order: str,
    ) -> List[Cron]:
        """Get crons with filtering, sorting, and pagination."""
        # FIXME
        # Filter crons based on criteria
        filtered_crons = []
        for cron in self._crons.values():
            if assistant_id and cron.assistant_id != assistant_id:
                continue
            if thread_id and cron.thread_id != thread_id:
                continue
            filtered_crons.append(cron)

        # 정렬
        valid_fields = {"cron_id", "assistant_id", "thread_id", "next_run_date", "end_time", "created_at", "updated_at"}
        sort_field = sort_by if sort_by in valid_fields else "created_at"
        sort_key = attrgetter(sort_field)
        reverse = sort_order.lower() == "desc"
        filtered_crons.sort(key=sort_key, reverse=reverse)

        # 페이징
        return filtered_crons[offset:offset + limit]

    async def _handle_schedule_event(self, event: Any) -> None:
        """Handle schedule events and sync to cron storage."""
        self._logger.info(f"Handling schedule event: {event}")
        try:
            if isinstance(event, ScheduleAdded):
                await self._add_cron(event)
            elif isinstance(event, ScheduleUpdated):
                await self._update_cron(event)
            elif isinstance(event, ScheduleRemoved):
                await self._remove_cron(event)
        except Exception as e:
            self._logger.error(f"Failed to sync schedule to cron: {e}")

    async def _add_cron(self, event: ScheduleAdded) -> None:
        """Add new schedule to cron storage."""
        # Get the full schedule object to access all details
        schedules = await self.get_schedules({event.schedule_id})
        if not schedules:
            self._logger.warning(f"Schedule {event.schedule_id} not found")
            return

        schedule: Schedule = schedules[0]

        # Extract metadata from schedule
        metadata = schedule.metadata or {}

        # Create cron object
        now = datetime.now()
        cron = Cron(
            cron_id=UUID(schedule.id),
            assistant_id=metadata.get("assistant_id"),
            thread_id=metadata.get("thread_id"),
            user_id=metadata.get("user_id"),
            payload=metadata.get("payload"),
            schedule=metadata.get("schedule"),
            next_run_date=event.next_fire_time,
            end_time=getattr(schedule.trigger, "end_time"),
            created_at=now,
            updated_at=now,
            metadata=metadata,
        )

        # Store in memory
        self._crons[cron.cron_id] = cron
        self._logger.info(f"Added schedule {schedule.id} to cron storage")

    async def _update_cron(self, event: ScheduleUpdated) -> None:
        """Update existing schedule in cron storage."""
        cron_id = UUID(event.schedule_id)
        if cron_id in self._crons:
            cron = self._crons[cron_id]
            # Create updated cron with new data
            updated_cron = attrs.evolve(
                cron,
                next_run_date=event.next_fire_time,
                updated_at=datetime.now()
            )
            self._crons[cron_id] = updated_cron
            self._logger.debug(f"Updated schedule {event.schedule_id} in cron storage")
        else:
            self._logger.warning(f"Cron {event.schedule_id} not found for update")

    async def _remove_cron(self, event: ScheduleRemoved) -> None:
        """Remove schedule from cron storage."""
        cron_id = UUID(event.schedule_id)
        if cron_id in self._crons:
            del self._crons[cron_id]
            self._logger.info(f"Removed schedule {event.schedule_id} from cron storage")
        else:
            self._logger.warning(f"Cron {event.schedule_id} not found for removal")
