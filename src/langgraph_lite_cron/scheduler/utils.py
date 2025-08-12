import os

from apscheduler import AsyncScheduler
from apscheduler.eventbrokers.local import LocalEventBroker
from apscheduler.eventbrokers.redis import RedisEventBroker
from apscheduler.serializers.cbor import CBORSerializer

from langgraph_lite_cron.scheduler.datastores.memory import LanggraphMemoryDataStore
from langgraph_lite_cron.scheduler.datastores.sqlalchemy import (
    LanggraphSQLAlchemyDataStore,
)


def _normalize_database_uri(uri: str | None) -> str | None:
    if uri is None:
        return None
    if uri.startswith("postgres://"):
        return uri.replace("postgres://", "postgresql://", 1)
    return uri


def create_scheduler() -> AsyncScheduler:
    serializer = CBORSerializer()
    database_uri = _normalize_database_uri(os.getenv("DATABASE_URI") or os.getenv("POSTGRES_URI"))

    if database_uri:
        data_store = LanggraphSQLAlchemyDataStore(
            engine_or_url=database_uri,
            serializer=serializer,
        )
    else:
        data_store = LanggraphMemoryDataStore()

    redis_url = os.getenv("REDIS_URI")

    if redis_url:
        event_broker = RedisEventBroker(
            client_or_url=redis_url,
            serializer=serializer,
        )
    else:
        event_broker = LocalEventBroker()

    scheduler = AsyncScheduler(
        data_store=data_store,
        event_broker=event_broker,
    )
    return scheduler
