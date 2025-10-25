from __future__ import annotations

import datetime as dt
from typing import Dict, List
from uuid import uuid4


class PublishingResult(Dict[str, object]):
    """Represents a platform upload summary."""


def publish_to_platforms(
    clips: List[Dict[str, object]],
    platforms: List[str],
) -> List[PublishingResult]:
    results: List[PublishingResult] = []
    timestamp = dt.datetime.utcnow().isoformat() + "Z"
    for clip in clips:
        clip_uploads: List[PublishingResult] = []
        for platform in platforms:
            job_id = str(uuid4())
            result = PublishingResult(
                clip_id=clip["clip_id"],
                platform=platform,
                status="uploaded",
                scheduled_time=timestamp,
                share_link=f"https://{platform}.com/clip/{clip['clip_id']}",
                job_id=job_id,
                published_at=timestamp,
            )
            results.append(result)
            clip_uploads.append(result)
        clip["uploads"] = clip_uploads
    return results
