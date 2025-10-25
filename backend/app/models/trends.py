from __future__ import annotations

from typing import List

from pydantic import BaseModel


class Trend(BaseModel):
    platform: str
    hashtag: str
    score: float
    category: str


class TrendResponse(BaseModel):
    trends: List[Trend]
