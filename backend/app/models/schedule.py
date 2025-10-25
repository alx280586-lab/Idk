from __future__ import annotations

from datetime import time
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class PostingSlot(BaseModel):
    platform: str
    time_utc: time


class ScheduleSettings(BaseModel):
    posts_per_day: int = 3
    auto_optimize: bool = True
    preferred_slots: List[PostingSlot] = Field(default_factory=list)

    @validator("posts_per_day")
    def validate_posts_per_day(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("posts_per_day must be positive")
        return value

    @classmethod
    def default(cls) -> "ScheduleSettings":
        return cls()


class ScheduleUpdateRequest(BaseModel):
    posts_per_day: Optional[int] = None
    auto_optimize: Optional[bool] = None
    preferred_slots: Optional[List[PostingSlot]] = None
