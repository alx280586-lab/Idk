from __future__ import annotations

import random
from typing import List


class TranscriptSegment(dict):
    """Simple container representing a transcript snippet."""

    @property
    def sentiment(self) -> float:
        return self.get("sentiment", 0.0)


def transcribe_video(youtube_url: str) -> List[TranscriptSegment]:
    """Mock transcription that returns generated segments.

    In a production environment, this would call Whisper or the YouTube transcript API.
    """

    random.seed(hash(youtube_url) % 10_000)
    segments: List[TranscriptSegment] = []
    start = 0.0
    for idx in range(20):
        duration = random.uniform(5, 20)
        end = start + duration
        segments.append(
            TranscriptSegment(
                text=f"Segment {idx + 1} discussing insights on creator growth.",
                start=start,
                end=end,
                sentiment=random.uniform(-1, 1),
                emphasis=random.uniform(0, 1),
                audience_reaction=random.choice([0.0, 0.3, 0.5, 0.8]),
            )
        )
        start = end
    return segments
