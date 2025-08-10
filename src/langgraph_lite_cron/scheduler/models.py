from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Cron(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cron_id: UUID
    assistant_id: UUID | None = None
    thread_id: UUID | None = None
    user_id: str | None = None
    payload: dict
    schedule: str
    next_run_date: datetime | None = None
    end_time: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict

    @classmethod
    def from_mapping(cls, row: dict[str, Any]) -> "Cron":
        return cls.model_validate(row)
