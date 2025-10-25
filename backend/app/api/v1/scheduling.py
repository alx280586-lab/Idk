from __future__ import annotations

from fastapi import APIRouter

from app.core.state import State
from app.models.schedule import ScheduleSettings, ScheduleUpdateRequest

router = APIRouter()


@router.get("/", response_model=ScheduleSettings)
def get_schedule() -> ScheduleSettings:
    return State.get_instance().get_schedule()


@router.put("/", response_model=ScheduleSettings)
def update_schedule(payload: ScheduleUpdateRequest) -> ScheduleSettings:
    state = State.get_instance()
    schedule = state.get_schedule().copy(update=payload.dict(exclude_unset=True))
    state.update_schedule(schedule)
    return schedule
