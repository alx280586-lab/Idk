from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from uuid import uuid4

from app.models.analytics import ClipPerformance
from app.models.schedule import ScheduleSettings
from app.models.video import ClipRequest, ClipTask


@dataclass
class StateStore:
    clip_requests: Dict[str, ClipTask] = field(default_factory=dict)
    schedule: ScheduleSettings = field(default_factory=ScheduleSettings.default)
    performances: Dict[str, List[ClipPerformance]] = field(default_factory=dict)
    automation_enabled: bool = False
    daily_cap: int = 5


class State:
    _instance: Optional["State"] = None

    def __init__(self) -> None:
        self.store = StateStore()

    @classmethod
    def get_instance(cls) -> "State":
        if cls._instance is None:
            cls._instance = State()
        return cls._instance

    def bootstrap(self) -> None:
        """Populate the store with a placeholder dataset for demo purposes."""
        if self.store.performances:
            return

        sample_video_id = str(uuid4())
        clip_task = ClipTask(
            id=sample_video_id,
            source="https://youtube.com/watch?v=dQw4w9WgXcQ",
            status="completed",
            clips=[
                {
                    "clip_id": str(uuid4()),
                    "start": 30,
                    "end": 60,
                    "duration": 30,
                    "aspect_ratio": "9:16",
                    "platforms": ["tiktok", "youtube_shorts"],
                    "subtitles": True,
                    "emojis": True,
                    "captions": True,
                    "thumbnail": "https://placehold.co/320x180?text=Clip+1",
                }
            ],
        )
        self.store.clip_requests[sample_video_id] = clip_task

        self.store.performances[sample_video_id] = [
            ClipPerformance(
                clip_id=clip_task.clips[0]["clip_id"],
                platform="tiktok",
                views=12800,
                likes=1550,
                shares=430,
                retention=0.71,
                watch_time_seconds=9000,
                keywords=["motivation", "growth"],
            ),
            ClipPerformance(
                clip_id=clip_task.clips[0]["clip_id"],
                platform="youtube_shorts",
                views=6500,
                likes=950,
                shares=230,
                retention=0.63,
                watch_time_seconds=5400,
                keywords=["motivation", "story"],
            ),
        ]

    def register_clip_request(self, request: ClipRequest) -> ClipTask:
        clip_task = ClipTask.from_request(request)
        self.store.clip_requests[clip_task.id] = clip_task
        return clip_task

    def update_clip_task(self, task: ClipTask) -> None:
        self.store.clip_requests[task.id] = task

    def get_clip_task(self, task_id: str) -> Optional[ClipTask]:
        return self.store.clip_requests.get(task_id)

    def record_performance(self, task_id: str, performance: ClipPerformance) -> None:
        self.store.performances.setdefault(task_id, []).append(performance)

    def get_performance(self, task_id: str) -> List[ClipPerformance]:
        return self.store.performances.get(task_id, [])

    def update_schedule(self, schedule: ScheduleSettings) -> None:
        self.store.schedule = schedule

    def get_schedule(self) -> ScheduleSettings:
        return self.store.schedule

    def set_automation(self, enabled: bool, daily_cap: Optional[int] = None) -> None:
        self.store.automation_enabled = enabled
        if daily_cap is not None:
            self.store.daily_cap = daily_cap

    def get_automation(self) -> Dict[str, object]:
        return {
            "enabled": self.store.automation_enabled,
            "daily_cap": self.store.daily_cap,
        }
