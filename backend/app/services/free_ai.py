from __future__ import annotations

import logging
from functools import lru_cache
from typing import Dict, Iterable, List, Union


logger = logging.getLogger(__name__)


SENTIMENT_LABELS = {
    "POSITIVE": 1.0,
    "NEGATIVE": -1.0,
    "NEUTRAL": 0.0,
}

EMPHASIS_EMOTIONS = {"joy", "surprise", "anger", "fear"}
REACTION_EMOTIONS = {"joy", "surprise", "love"}


class OpenSourceAIProvider:
    """Wrapper around free Hugging Face models used by the platform."""

    def __init__(self) -> None:
        try:
            from transformers import pipeline  # type: ignore
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise RuntimeError(
                "transformers is required for open-source AI enrichment."
            ) from exc

        self._sentiment = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            return_all_scores=True,
        )
        self._emotion = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            return_all_scores=True,
        )

    def enrich_transcript(self, segments: List[dict]) -> None:
        """Annotate transcript segments with emotion, sentiment, and engagement cues."""

        if not segments:
            return

        texts = [segment.get("text", "") for segment in segments]
        sentiment_batches = self._sentiment(texts, truncation=True)
        emotion_batches = self._emotion(texts, truncation=True)

        for segment, sentiment_scores, emotion_scores in zip(
            segments, sentiment_batches, emotion_batches
        ):
            normalized_sentiment = _ensure_iterable_scores(sentiment_scores)
            normalized_emotions = _ensure_iterable_scores(emotion_scores)
            sentiment_value = _calculate_sentiment(normalized_sentiment)
            emotions = {
                entry.get("label", "").lower(): float(entry.get("score", 0.0))
                for entry in normalized_emotions
                if entry.get("label")
            }
            segment["sentiment"] = sentiment_value
            segment["emotions"] = emotions
            segment["emphasis"] = _calculate_emphasis(emotions)
            segment["audience_reaction"] = _calculate_reaction(emotions)
            segment["viewer_retention"] = _calculate_viewer_retention(
                sentiment_value,
                segment["emphasis"],
                segment["audience_reaction"],
            )


def _ensure_iterable_scores(scores: Union[Iterable[Dict[str, float]], Dict[str, float]]) -> List[Dict[str, float]]:
    if isinstance(scores, dict):
        return [scores]
    return list(scores)


def _calculate_sentiment(scores: Iterable[Dict[str, float]]) -> float:
    value = 0.0
    for score in scores:
        label = score.get("label", "").upper()
        mapped = SENTIMENT_LABELS.get(label)
        if mapped is not None:
            value += mapped * float(score.get("score", 0.0))
    return max(-1.0, min(1.0, value))


def _calculate_emphasis(emotions: Dict[str, float]) -> float:
    return max(0.0, min(1.0, sum(emotions.get(emotion, 0.0) for emotion in EMPHASIS_EMOTIONS)))


def _calculate_reaction(emotions: Dict[str, float]) -> float:
    return max(0.0, min(1.0, sum(emotions.get(emotion, 0.0) for emotion in REACTION_EMOTIONS)))


def _calculate_viewer_retention(sentiment: float, emphasis: float, reaction: float) -> float:
    """Estimate how sticky a moment is likely to be based on emotional cues."""

    positive_sentiment = max(0.0, sentiment)
    base = 0.35 + positive_sentiment * 0.25
    attention = emphasis * 0.3 + reaction * 0.45
    return max(0.05, min(1.0, base + attention))


@lru_cache(maxsize=1)
def get_open_source_ai() -> OpenSourceAIProvider:
    """Return a cached provider instance to avoid reloading models repeatedly."""

    logger.info("Loading open-source Hugging Face pipelines for AutoClipper AI")
    return OpenSourceAIProvider()
