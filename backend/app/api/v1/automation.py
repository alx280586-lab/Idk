from __future__ import annotations

from fastapi import APIRouter

from app.core.state import State
from app.models.automation import AutomationSettings

router = APIRouter()


@router.get("/", response_model=AutomationSettings)
def get_automation() -> AutomationSettings:
    state = State.get_instance()
    data = state.get_automation()
    return AutomationSettings(**data)


@router.post("/", response_model=AutomationSettings)
def update_automation(payload: AutomationSettings) -> AutomationSettings:
    state = State.get_instance()
    state.set_automation(enabled=payload.enabled, daily_cap=payload.daily_cap)
    return AutomationSettings(**state.get_automation())
