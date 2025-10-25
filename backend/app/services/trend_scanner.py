from __future__ import annotations

import random
from typing import List

from app.models.trends import Trend


TREND_TOPICS = [
    ("tiktok", "#aiTools", "technology"),
    ("instagram", "#creatorTips", "education"),
    ("youtube", "#shortsChallenge", "entertainment"),
    ("tiktok", "#productivity", "business"),
    ("instagram", "#motivation", "self_improvement"),
]


def fetch_trending_topics() -> List[Trend]:
    random.seed()
    trends = []
    for platform, hashtag, category in TREND_TOPICS:
        trends.append(
            Trend(
                platform=platform,
                hashtag=hashtag,
                score=random.uniform(0.4, 0.98),
                category=category,
            )
        )
    trends.sort(key=lambda trend: trend.score, reverse=True)
    return trends
