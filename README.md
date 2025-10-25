# AutoClipper AI

AutoClipper AI is a full-stack prototype that automatically generates, edits, and schedules short-form video clips derived from long-form YouTube videos. It features a FastAPI backend for orchestration, analytics, and scheduling plus a React dashboard for managing automation preferences.

## Features

- **Video intelligence** – Ingest YouTube URLs, fetch free transcripts (or fall back to the open Whisper model), detect high-energy moments with Hugging Face emotion models, and produce multi-aspect clips with subtitles/captions toggles.
- **Smart scheduling** – Configure daily posting quotas, auto-optimization, and platform targets.
- **Performance analytics** – View AI-generated recommendations, keyword trends, and per-platform stats for completed clips.
- **Viewer heatmap detection** – Automatically surfaces the most binge-worthy moment per video based on retention and emotion cues.
- **Hands-free publishing** – Instantly schedules finished clips across TikTok, YouTube Shorts, and Instagram Reels with shareable links.
- **Trend integration** – Surfaces trending hashtags and topics from major short-form platforms.
- **Autonomous mode** – Enable always-on automation with adjustable daily clip caps.

## Tech Stack

- **Backend**: FastAPI, Pydantic, YouTube Transcript API, faster-whisper, and Hugging Face Transformers.
- **Frontend**: React (Vite), React Query, Axios.

## Getting Started

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

> **Prerequisites**
>
> - Install [FFmpeg](https://ffmpeg.org/download.html) so `yt-dlp` and Whisper can extract audio.
> - When using Hugging Face models for the first time the weights are downloaded automatically. Set `HF_HOME` if you need a custom cache directory.
> - If `pip` cannot resolve a PyTorch wheel automatically, follow the official [CPU installation guide](https://pytorch.org/get-started/locally/) for your platform and rerun `pip install -r requirements.txt`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies API requests to `http://localhost:8000`.

## Open-Source AI Stack

AutoClipper AI relies exclusively on free, self-hostable models:

| Capability | Library / Model | Notes |
| --- | --- | --- |
| Transcripts | [`youtube-transcript-api`](https://pypi.org/project/youtube-transcript-api/) | Pulls official captions when available without authentication. |
| Audio fallback | [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) (`WhisperModel` "medium") | Downloads audio with `yt-dlp` and performs CPU-friendly speech-to-text. |
| Sentiment | [`distilbert-base-uncased-finetuned-sst-2-english`](https://huggingface.co/distilbert-base-uncased-finetuned-sst-2-english) | Provides polarity for each segment. |
| Emotion cues | [`j-hartmann/emotion-english-distilroberta-base`](https://huggingface.co/j-hartmann/emotion-english-distilroberta-base) | Determines excitement, surprise, and joy for highlight scoring. |

All models run locally; no paid API keys are required.

## Project Structure

```
backend/
  app/
    api/v1/        # FastAPI routers (videos, scheduling, analytics, trends, automation)
    core/          # Application state bootstrap
    models/        # Pydantic schemas & dataclasses
    services/      # Transcription, highlight scoring, editing, publishing, analytics, open-source AI helpers
    tasks/         # Background queue simulator
frontend/
  src/
    components/    # React UI panels
    hooks/         # Axios instance
    styles/        # Global styling
```

## Notes

- Processing, analytics, and publishing are simulated to make the experience demo-ready without external credentials, but uploads include shareable links per platform to mirror real-world automation.
- The transcription layer now prefers the free YouTube Transcript API and falls back to the open-source Whisper model via `faster-whisper` when necessary.
- Highlight scoring uses Hugging Face emotion and sentiment models (DistilBERT SST-2 + `j-hartmann/emotion-english-distilroberta-base`).
- Adjust the services layer to connect ffmpeg-powered clip rendering and platform APIs for production use.
