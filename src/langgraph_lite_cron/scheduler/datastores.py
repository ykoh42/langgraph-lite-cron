from contextlib import AsyncExitStack
from datetime import datetime, timezone
from logging import Logger
from typing import Any
from uuid import UUID

import attrs
from apscheduler import Schedule, ScheduleAdded, ScheduleRemoved, ScheduleUpdated
from apscheduler.abc import EventBroker
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore
from sqlalchemy import MetaData, Table, asc, desc
from sqlalchemy.ext.asyncio import AsyncEngine

from langgraph_lite_cron.scheduler.models import Cron


@attrs.define(eq=False, repr=False)
class LanggraphSQLAlchemyDataStore(SQLAlchemyDataStore):
    _t_cron: Table = attrs.field(init=False)

    def __attrs_post_init__(self) -> None:
        super().__attrs_post_init__()
        # prefix = f"{self.schema}." if self.schema else ""
        # self._t_cron = self._metadata.tables[prefix + "cron"]

    def get_table_definitions(self) -> MetaData:
        metadata = super().get_table_definitions()
        Table("cron", metadata, schema=self.schema)
        return metadata

    async def start(
        self,
        exit_stack: AsyncExitStack,
        event_broker: EventBroker,
        logger: Logger,
    ) -> None:
        """Start the data store and subscribe to schedule events."""
        await super().start(exit_stack, event_broker, logger)

        if isinstance(self._engine, AsyncEngine):
            async with self._engine.connect() as aconn:
                def _do_reflect(sync_conn):
                    if 'cron' in self._metadata.tables:
                        self._metadata.remove(self._metadata.tables['cron'])
                    self._metadata.reflect(
                        bind=sync_conn,
                        schema=self.schema,
                        only=["cron"],
                    )

                await aconn.run_sync(_do_reflect)
        else:
            with self._engine.connect() as conn:
                if 'cron' in self._metadata.tables:
                    self._metadata.remove(self._metadata.tables['cron'])
                self._metadata.reflect(bind=conn, schema=self.schema, only=['cron'])

        prefix = f"{self.schema}." if self.schema else ""
        self._t_cron = self._metadata.tables[prefix + "cron"]

        event_broker.subscribe(
            self._handle_schedule_event,
            event_types={ScheduleAdded, ScheduleUpdated, ScheduleRemoved},
            is_async=True,
        )

        logger.info("Langgraph Lite DataStore started with cron table sync")

    async def get_crons(
        self,
        *,
        assistant_id: UUID | None,
        thread_id: UUID | None,
        limit: int,
        offset: int,
        sort_by: str,
        sort_order: str,
    ) -> list[Cron]:

        t = self._t_cron
        query = t.select()

        if assistant_id:
            query = query.where(self._t_cron.c.assistant_id == assistant_id)
        if thread_id:
            query = query.where(self._t_cron.c.thread_id == thread_id)

        sort_col_map = {
            "cron_id": t.c.cron_id,
            "assistant_id": t.c.assistant_id,
            "thread_id": t.c.thread_id,
            "next_run_date": t.c.next_run_date,
            "end_time": t.c.end_time,
            "created_at": t.c.created_at,
            "updated_at": t.c.updated_at,
        }

        sort_col = sort_col_map[sort_by]
        query = query.order_by(asc(sort_col) if sort_order == "asc" else desc(sort_col))
        query = query.offset(offset).limit(limit)

        async for attempt in self._retry():
            with attempt:
                async with self._begin_transaction() as conn:
                    result = await self._execute(conn, query)
                    rows = result.mappings().all()

        return [Cron.from_mapping(row) for row in rows]

    async def _handle_schedule_event(self, event: Any) -> None:
        """Handle schedule events and sync to cron table."""
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
        """Add new schedule to cron table with full schedule details."""
        # Get the full schedule object to access all details
        schedules = await self.get_schedules({event.schedule_id})
        if not schedules:
            self._logger.warning(f"Schedule {event.schedule_id} not found")
            return

        schedule: Schedule = schedules[0]

        # Extract metadata from schedule
        metadata = schedule.metadata or {}

        # Prepare cron table data
        data = {
            'cron_id': schedule.id,
            'assistant_id': metadata.get('assistant_id'),
            'thread_id': metadata.get('thread_id'),
            'user_id': metadata.get('user_id'),
            'payload': metadata.get('payload'),
            'schedule': metadata.get('schedule'),
            'next_run_date': event.next_fire_time,
            'end_time': getattr(schedule.trigger, 'end_time'),
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'metadata': metadata.get('metadata'),
        }

        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        # Insert into cron table
        insert = self._t_cron.insert().values(**data)

        async for attempt in self._retry():
            with attempt:
                async with self._begin_transaction() as conn:
                    await self._execute(conn, insert)
                    self._logger.info(f"Added schedule {schedule.id} to cron table")

    async def _update_cron(self, event: ScheduleUpdated) -> None:
        """Update existing schedule in cron table."""

        update_data = {
            'next_run_date': event.next_fire_time,
            'updated_at': datetime.now(timezone.utc),
        }

        update = (
            self._t_cron.update()
            .where(self._t_cron.c.cron_id == event.schedule_id)
            .values(**update_data)
        )

        async for attempt in self._retry():
            with attempt:
                async with self._begin_transaction() as conn:
                    result = await self._execute(conn, update)
                    if result.rowcount > 0:
                        self._logger.debug(f"Updated schedule {event.schedule_id} in cron table")

    async def _remove_cron(self, event: ScheduleRemoved) -> None:
        """Remove schedule in cron table."""
        delete = (
            self._t_cron.delete()
            .where(self._t_cron.c.cron_id == event.schedule_id)
        )

        async for attempt in self._retry():
            with attempt:
                async with self._begin_transaction() as conn:
                    await self._execute(conn, delete)
                    self._logger.info(f"Removed schedule {event.schedule_id} from cron table")
