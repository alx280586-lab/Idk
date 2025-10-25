from __future__ import annotations

import logging
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable, List, Optional
from urllib.parse import parse_qs, urlparse

from .free_ai import get_open_source_ai

logger = logging.getLogger(__name__)


class TranscriptSegment(dict):
    """Simple container representing a transcript snippet."""

    @property
    def sentiment(self) -> float:
        return self.get("sentiment", 0.0)


def _extract_video_id(youtube_url: str) -> Optional[str]:
    """Return the canonical YouTube video id from the provided URL."""

    parsed = urlparse(youtube_url)
    if parsed.hostname in {"youtu.be"}:
        return parsed.path.lstrip("/") or None

    if parsed.hostname and parsed.hostname.endswith("youtube.com"):
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/")[-1] or None

    # Fallback to regular expression for any other variant.
    match = re.search(r"(?:v=|/videos/|embed/|youtu\.be/)([\w-]{11})", youtube_url)
    if match:
        return match.group(1)
    return None


def _normalize_segments(raw_segments: Iterable[dict]) -> List[TranscriptSegment]:
    segments: List[TranscriptSegment] = []
    for chunk in raw_segments:
        text = chunk.get("text", "").strip()
        if not text:
            continue
        start = float(chunk.get("start", 0.0))
        duration = float(chunk.get("duration", 0.0))
        end = start + duration if duration else start + 5.0
        segments.append(TranscriptSegment(text=text, start=start, end=end))
    return segments


def _transcribe_with_youtube(video_id: str) -> List[TranscriptSegment]:
    try:
        from youtube_transcript_api import (  # type: ignore
            NoTranscriptFound,
            TranscriptsDisabled,
            YouTubeTranscriptApi,
        )
    except ImportError as exc:  # pragma: no cover - optional dependency guard
        logger.debug("youtube_transcript_api is not installed: %s", exc)
        return []

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
        if transcript:
            return _normalize_segments(transcript)
    except (NoTranscriptFound, TranscriptsDisabled):
        try:
            transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
            for candidate in transcripts:
                if candidate.is_translatable:
                    translated = candidate.translate("en").fetch()
                    if translated:
                        return _normalize_segments(translated)
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.debug("Failed to translate transcript: %s", exc)
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.debug("Failed to fetch transcript: %s", exc)
    return []


def _transcribe_with_whisper(youtube_url: str) -> List[TranscriptSegment]:
    """Download the audio and transcribe it using the open-source Whisper model."""

    try:
        from faster_whisper import WhisperModel  # type: ignore
        import yt_dlp  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional dependency guard
        logger.debug("Optional transcription dependency missing: %s", exc)
        return []

    with TemporaryDirectory() as tmpdir:
        audio_path = Path(tmpdir) / "audio.m4a"
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(audio_path),
            "quiet": True,
            "no_warnings": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
        except Exception as exc:  # pragma: no cover - network/io failure guard
            logger.debug("Failed to download audio for whisper transcription: %s", exc)
            return []

        try:
            model = WhisperModel("medium", device="cpu", compute_type="int8")
            segments, _ = model.transcribe(str(audio_path), vad_filter=True)
        except Exception as exc:  # pragma: no cover - inference failure guard
            logger.debug("Whisper transcription failed: %s", exc)
            return []

    normalized: List[TranscriptSegment] = []
    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue
        normalized.append(
            TranscriptSegment(
                text=text,
                start=float(segment.start),
                end=float(segment.end),
            )
        )
    return normalized


def transcribe_video(youtube_url: str) -> List[TranscriptSegment]:
    """Transcribe the video using free, open-source tooling."""

    video_id = _extract_video_id(youtube_url)
    segments: List[TranscriptSegment] = []
    if video_id:
        segments = _transcribe_with_youtube(video_id)

    if not segments:
        segments = _transcribe_with_whisper(youtube_url)

    if not segments:
        raise RuntimeError(
            "Unable to transcribe video. Install youtube-transcript-api or faster-whisper."
        )

    provider = get_open_source_ai()
    provider.enrich_transcript(segments)
    return segments
