import os
import re

from apscheduler import AsyncScheduler
from apscheduler.eventbrokers.local import LocalEventBroker
from apscheduler.eventbrokers.redis import RedisEventBroker
from apscheduler.serializers.cbor import CBORSerializer
from sqlalchemy.exc import ArgumentError, NoSuchModuleError, OperationalError

from langgraph_lite_cron.scheduler.datastores.memory import LanggraphMemoryDataStore
from langgraph_lite_cron.scheduler.datastores.sqlalchemy import (
    LanggraphSQLAlchemyDataStore,
)


def _normalize_database_uri(uri: str | None) -> str | None:
    if uri is None:
        return None
    uri = re.sub(r"^postgres(?=\+|://)", "postgresql", uri, count=1)
    uri = re.sub(r"^sqlite3(?=\+|://)", "sqlite", uri, count=1)
    return uri


def create_scheduler() -> AsyncScheduler:
    serializer = CBORSerializer()
    database_uri = _normalize_database_uri(os.getenv("DATABASE_URI") or os.getenv("POSTGRES_URI"))

    try:
        data_store = LanggraphSQLAlchemyDataStore(
            engine_or_url=database_uri,
            serializer=serializer,
        )
    except (ArgumentError, NoSuchModuleError, OperationalError):
        data_store = LanggraphMemoryDataStore()

    try:
        event_broker = RedisEventBroker(
            client_or_url=os.getenv("REDIS_URI"),
            serializer=serializer,
        )
    except Exception:
        event_broker = LocalEventBroker()

    scheduler = AsyncScheduler(
        data_store=data_store,
        event_broker=event_broker,
    )
    return scheduler
