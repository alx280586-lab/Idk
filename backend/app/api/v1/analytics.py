from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.state import State
from app.models.analytics import PerformanceInsights
from app.services.analytics_engine import derive_insights

router = APIRouter()


@router.get("/{task_id}", response_model=PerformanceInsights)
def get_performance(task_id: str) -> PerformanceInsights:
    state = State.get_instance()
    performances = state.get_performance(task_id)
    if performances is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return derive_insights(task_id, performances)
