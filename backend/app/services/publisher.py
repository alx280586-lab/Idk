from __future__ import annotations

import datetime as dt
from typing import Dict, List


class PublishingResult(Dict[str, object]):
    """Represents a platform upload summary."""


def publish_to_platforms(clips: List[Dict[str, object]], platforms: List[str]) -> List[PublishingResult]:
    results: List[PublishingResult] = []
    timestamp = dt.datetime.utcnow().isoformat() + "Z"
    for clip in clips:
        for platform in platforms:
            results.append(
                PublishingResult(
                    clip_id=clip["clip_id"],
                    platform=platform,
                    status="scheduled",
                    scheduled_time=timestamp,
                    share_link=f"https://{platform}.com/clip/{clip['clip_id']}",
                )
            )
    return results
