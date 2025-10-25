from __future__ import annotations

from fastapi import APIRouter

from app.models.trends import TrendResponse
from app.services.trend_scanner import fetch_trending_topics

router = APIRouter()


@router.get("/", response_model=TrendResponse)
def get_trends() -> TrendResponse:
    return TrendResponse(trends=fetch_trending_topics())
