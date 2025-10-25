from __future__ import annotations

from collections import Counter
from typing import List

from app.models.analytics import ClipPerformance, PerformanceInsights


def derive_insights(task_id: str, performances: List[ClipPerformance]) -> PerformanceInsights:
    if not performances:
        return PerformanceInsights(
            task_id=task_id,
            performances=[],
            best_keywords=[],
            recommended_actions=["Collect more data to generate insights."],
        )

    keywords = Counter(keyword for perf in performances for keyword in perf.keywords)
    best_keywords = [keyword for keyword, _ in keywords.most_common(5)]

    best_platform = max(performances, key=lambda perf: perf.retention)

    recommended_actions = [
        f"Produce more clips featuring '{best_keywords[0]}'" if best_keywords else "Experiment with new hooks.",
        f"Prioritize {best_platform.platform} since it drives the best retention ({best_platform.retention:.0%}).",
    ]

    return PerformanceInsights(
        task_id=task_id,
        performances=performances,
        best_keywords=best_keywords,
        recommended_actions=recommended_actions,
    )
