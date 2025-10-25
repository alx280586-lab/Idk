from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.core.state import State
from app.models.video import (
    ClipGenerationRequest,
    ClipGenerationResponse,
    ClipRequest,
    ClipStatusResponse,
)
from app.tasks.scheduler import generate_mock_performance, queue_clip_request

router = APIRouter()


@router.post("/ingest", response_model=ClipGenerationResponse)
def ingest_video(payload: ClipGenerationRequest, background_tasks: BackgroundTasks) -> ClipGenerationResponse:
    request = ClipRequest(
        youtube_url=str(payload.youtube_url),
        clip_duration_min=payload.clip_duration_min,
        clip_duration_max=payload.clip_duration_max,
        auto_subtitles=payload.auto_subtitles,
        include_emojis=payload.include_emojis,
        include_captions=payload.include_captions,
        aspect_ratios=payload.aspect_ratios,
        target_platforms=payload.target_platforms,
    )
    state = State.get_instance()
    task = state.register_clip_request(request)
    background_tasks.add_task(queue_clip_request, request, task)
    background_tasks.add_task(generate_mock_performance, task.id)
    return ClipGenerationResponse(task_id=task.id, status=task.status)


@router.get("/{task_id}", response_model=ClipStatusResponse)
def get_clip_status(task_id: str) -> ClipStatusResponse:
    state = State.get_instance()
    task = state.get_clip_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return ClipStatusResponse(
        task_id=task.id,
        status=task.status,
        clips=task.clips,
        most_watched=task.most_watched,
        uploads=task.uploads,
    )
