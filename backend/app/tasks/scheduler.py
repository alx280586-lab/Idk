from __future__ import annotations

import random
import threading
import time

from app.core.state import State
from app.models.analytics import ClipPerformance
from app.models.video import ClipRequest, ClipTask
from app.services import editor, highlights, publisher, transcription


PROCESSING_DELAY_SECONDS = 1.5


def _simulate_processing(task: ClipTask, request: ClipRequest) -> None:
    time.sleep(PROCESSING_DELAY_SECONDS)

    segments = transcription.transcribe_video(request.youtube_url)
    candidates = highlights.find_highlights(
        segments,
        min_duration=request.clip_duration_min,
        max_duration=request.clip_duration_max,
    )
    if not candidates:
        task.mark_failed("no_highlights_found")
    else:
        selected_candidates = candidates[: random.randint(1, min(3, len(candidates)))]
        clips = editor.generate_clip_assets(
            candidates=selected_candidates,
            auto_subtitles=request.auto_subtitles,
            include_emojis=request.include_emojis,
            include_captions=request.include_captions,
            aspect_ratios=request.aspect_ratios,
            target_platforms=request.target_platforms,
        )
        task.mark_completed(clips)
        publisher.publish_to_platforms(clips, request.target_platforms)
    State.get_instance().update_clip_task(task)


def queue_clip_request(request: ClipRequest, task: ClipTask) -> None:
    threading.Thread(target=_simulate_processing, args=(task, request), daemon=True).start()


def generate_mock_performance(task_id: str) -> None:
    time.sleep(PROCESSING_DELAY_SECONDS + 0.5)
    state = State.get_instance()
    task = state.get_clip_task(task_id)
    if not task or task.status != "completed":
        return

    for clip in task.clips:
        for platform in clip["platforms"]:
            performance = ClipPerformance(
                clip_id=clip["clip_id"],
                platform=platform,
                views=random.randint(1_000, 20_000),
                likes=random.randint(100, 3_000),
                shares=random.randint(20, 900),
                retention=round(random.uniform(0.35, 0.9), 2),
                watch_time_seconds=random.randint(1_000, 12_000),
                keywords=["growth", "ai", "content"],
            )
            state.record_performance(task_id, performance)
