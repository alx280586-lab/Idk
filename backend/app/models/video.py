from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl, validator


class ClipGenerationRequest(BaseModel):
    youtube_url: HttpUrl
    clip_duration_min: int
    clip_duration_max: int
    auto_subtitles: bool = True
    include_emojis: bool = False
    include_captions: bool = True
    aspect_ratios: List[str] = Field(default_factory=lambda: ["9:16"])
    target_platforms: List[str] = Field(default_factory=lambda: ["tiktok", "youtube_shorts"])

    @validator("clip_duration_min", "clip_duration_max")
    def validate_duration(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Duration must be positive")
        return value

    @validator("clip_duration_max")
    def validate_range(cls, value: int, values: Dict[str, int]) -> int:
        minimum = values.get("clip_duration_min")
        if minimum and value < minimum:
            raise ValueError("clip_duration_max must be >= clip_duration_min")
        return value


class ClipGenerationResponse(BaseModel):
    task_id: str
    status: str


class ClipStatusResponse(BaseModel):
    task_id: str
    status: str
    clips: Optional[List[Dict[str, object]]]
    most_watched: Optional[Dict[str, object]] = None
    uploads: Optional[List[Dict[str, object]]] = None


@dataclass
class ClipRequest:
    youtube_url: str
    clip_duration_min: int
    clip_duration_max: int
    auto_subtitles: bool
    include_emojis: bool
    include_captions: bool
    aspect_ratios: List[str]
    target_platforms: List[str]


@dataclass
class ClipTask:
    id: str
    source: str
    status: str
    clips: List[Dict[str, object]] = field(default_factory=list)
    most_watched: Optional[Dict[str, object]] = None
    uploads: List[Dict[str, object]] = field(default_factory=list)

    @classmethod
    def from_request(cls, request: ClipRequest) -> "ClipTask":
        return cls(
            id=str(uuid4()),
            source=request.youtube_url,
            status="processing",
            clips=[],
            most_watched=None,
            uploads=[],
        )

    def mark_completed(
        self,
        clips: List[Dict[str, object]],
        *,
        most_watched: Optional[Dict[str, object]] = None,
        uploads: Optional[List[Dict[str, object]]] = None,
    ) -> None:
        self.status = "completed"
        self.clips = clips
        self.most_watched = most_watched
        if uploads is not None:
            self.uploads = uploads

    def mark_failed(self, reason: str) -> None:
        self.status = f"failed:{reason}"
