from __future__ import annotations

from typing import List

from .transcription import TranscriptSegment


class HighlightCandidate(dict):
    """Represents a candidate clip derived from transcript metadata."""

    @property
    def score(self) -> float:
        return self.get("score", 0.0)


def find_highlights(segments: List[TranscriptSegment], min_duration: int, max_duration: int) -> List[HighlightCandidate]:
    """Generate highlight candidates based on sentiment and engagement cues."""

    highlights: List[HighlightCandidate] = []
    for segment in segments:
        duration = segment["end"] - segment["start"]
        if duration < min_duration or duration > max_duration:
            continue
        sentiment = segment.get("sentiment", 0.0)
        emphasis = segment.get("emphasis", 0.0)
        audience_reaction = segment.get("audience_reaction", 0.0)
        emotions = segment.get("emotions", {})
        dominant_emotion = max(emotions, key=emotions.get) if emotions else None
        emotion_bonus = max((emotions.get(label, 0.0) for label in ("joy", "surprise", "anger")), default=0.0)
        retention = segment.get("viewer_retention", 0.0)
        score = max(
            0.0,
            sentiment * 0.25
            + emphasis * 0.3
            + audience_reaction * 0.2
            + emotion_bonus * 0.05
            + retention * 0.2,
        )
        if score > 0.3:
            highlights.append(
                HighlightCandidate(
                    start=segment["start"],
                    end=segment["end"],
                    text=segment["text"],
                    score=score,
                    dominant_emotion=dominant_emotion,
                    viewer_retention=retention,
                )
            )
    highlights.sort(key=lambda candidate: candidate.score, reverse=True)
    return highlights[:10]


def identify_most_watched_segment(
    segments: List[TranscriptSegment],
    max_duration: int,
) -> HighlightCandidate | None:
    """Return the segment predicted to keep the most viewers watching."""

    best_candidate: HighlightCandidate | None = None
    best_score = -1.0

    for segment in segments:
        duration = segment["end"] - segment["start"]
        if duration <= 0:
            continue
        if duration > max_duration:
            continue
        retention = segment.get("viewer_retention", 0.0)
        reaction = segment.get("audience_reaction", 0.0)
        emphasis = segment.get("emphasis", 0.0)
        composite = retention * 0.6 + reaction * 0.25 + emphasis * 0.15
        if composite > best_score:
            best_score = composite
            best_candidate = HighlightCandidate(
                start=segment["start"],
                end=segment["end"],
                text=segment["text"],
                score=composite,
                viewer_retention=retention,
            )

    return best_candidate
