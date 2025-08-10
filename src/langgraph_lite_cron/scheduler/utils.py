import os

from apscheduler import AsyncScheduler
from apscheduler.abc import DataStore, EventBroker
from apscheduler.eventbrokers.redis import RedisEventBroker
from apscheduler.serializers.cbor import CBORSerializer

from langgraph_lite_cron.scheduler.datastores import LanggraphSQLAlchemyDataStore


def _normalize_database_uri(uri: str | None) -> str | None:
    if uri is None:
        return None
    if uri.startswith("postgres://"):
        return uri.replace("postgres://", "postgresql://", 1)
    return uri


def create_scheduler(
    *,
    data_store: DataStore | None = None,
    event_broker: EventBroker | None = None,
) -> AsyncScheduler:
    scheduler = AsyncScheduler(
        data_store=data_store or LanggraphSQLAlchemyDataStore(
            engine_or_url=_normalize_database_uri(os.getenv("DATABASE_URI") or os.getenv("POSTGRES_URI")),
            serializer=CBORSerializer(),
        ),
        event_broker=event_broker or RedisEventBroker(
            client_or_url=os.getenv("REDIS_URI"),
        ),
    )
    return scheduler
