from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class ClipPerformance(BaseModel):
    clip_id: str
    platform: str
    views: int
    likes: int
    shares: int
    retention: float = Field(..., ge=0.0, le=1.0)
    watch_time_seconds: int
    keywords: List[str] = Field(default_factory=list)


class PerformanceInsights(BaseModel):
    task_id: str
    performances: List[ClipPerformance]
    best_keywords: List[str]
    recommended_actions: List[str]
