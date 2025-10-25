# AutoClipper AI

AutoClipper AI is a full-stack prototype that automatically generates, edits, and schedules short-form video clips derived from long-form YouTube videos. It features a FastAPI backend for orchestration, analytics, and scheduling plus a React dashboard for managing automation preferences.

## Features

- **Video intelligence** – Ingest YouTube URLs, run mock transcription, detect high-energy moments, and produce multi-aspect clips with subtitles/captions toggles.
- **Smart scheduling** – Configure daily posting quotas, auto-optimization, and platform targets.
- **Performance analytics** – View AI-generated recommendations, keyword trends, and per-platform stats for completed clips.
- **Trend integration** – Surfaces trending hashtags and topics from major short-form platforms.
- **Autonomous mode** – Enable always-on automation with adjustable daily clip caps.

## Tech Stack

- **Backend**: FastAPI, Pydantic (with mock services simulating Whisper, ffmpeg, and platform publishing workflows).
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

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies API requests to `http://localhost:8000`.

## Project Structure

```
backend/
  app/
    api/v1/        # FastAPI routers (videos, scheduling, analytics, trends, automation)
    core/          # Application state bootstrap
    models/        # Pydantic schemas & dataclasses
    services/      # Mock transcription, highlight scoring, editing, publishing, analytics
    tasks/         # Background queue simulator
frontend/
  src/
    components/    # React UI panels
    hooks/         # Axios instance
    styles/        # Global styling
```

## Notes

- Processing, analytics, and publishing are simulated to make the experience demo-ready without external credentials.
- Adjust the services layer to connect Whisper, ffmpeg, and actual platform APIs for production use.
