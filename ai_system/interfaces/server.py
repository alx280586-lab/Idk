"""FastAPI server exposing the organic scripting AI through a browser."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ai_system.config import SystemConfig
from ai_system.core.memory import MemoryTrace
from ai_system.interfaces.runtime import RuntimeContext, create_runtime


class MissionRequest(BaseModel):
    """Incoming mission payload from the browser client."""

    goal: str = Field(..., description="High-level mission objective")
    keywords: str = Field("", description="Space separated keywords to search knowledge")
    log_response: bool = Field(True, description="Persist the response into the knowledge cache")
    tags: List[str] = Field(default_factory=lambda: ["web"])


def _compose_response(mission: str, considerations: List[str], conclusion: str) -> str:
    return (
        f"Mission: {mission}\n"
        f"Plan: {conclusion}\n"
        + "Notes:\n- "
        + "\n- ".join(considerations)
    )


def _trace_to_dict(trace: MemoryTrace) -> Dict[str, Any]:
    return {
        "context": trace.context,
        "response": trace.response,
        "score": trace.score,
        "tags": trace.tags,
    }


def _knowledge_listing(runtime: RuntimeContext, limit: int = 10) -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    knowledge_paths = sorted(
        (runtime.config.data_root / "knowledge").glob("*.md"),
        key=lambda item: item.stat().st_mtime,
    )
    for path in knowledge_paths[-limit:]:
        entries.append({"id": path.stem, "path": str(path)})
    return entries


def create_app(config: SystemConfig | None = None) -> FastAPI:
    """Create a FastAPI application bound to a runtime context."""

    runtime: RuntimeContext = create_runtime(config)
    app = FastAPI(title="Organic Scripting AI", version="0.2.0")

    static_dir = Path(__file__).resolve().parents[2] / "web" / "public"
    if static_dir.exists():
        app.mount("/ui", StaticFiles(directory=static_dir, html=True), name="ui")

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse | JSONResponse:
        if static_dir.exists():
            return FileResponse(static_dir / "index.html")
        return JSONResponse({"message": "UI assets missing. Visit /api/health for status."})

    @app.get("/api/health")
    async def health() -> Dict[str, Any]:
        knowledge_dir = runtime.config.data_root / "knowledge"
        knowledge_dir.mkdir(parents=True, exist_ok=True)
        return {
            "status": "ok",
            "knowledge_entries": len(list(knowledge_dir.glob("*.md"))),
            "trusted_sources": [source.url for source in runtime.config.trusted_sources],
        }

    @app.post("/api/missions")
    async def run_mission(payload: MissionRequest) -> Dict[str, Any]:
        mission = payload.goal.strip()
        if not mission:
            raise HTTPException(status_code=400, detail="Mission goal cannot be empty")

        thought = runtime.reasoner.brainstorm(mission, {"keywords": payload.keywords})
        response = _compose_response(mission, thought.considerations, thought.conclusion)
        trace = MemoryTrace(mission, response, thought.confidence, payload.tags)
        runtime.memory.record(trace)

        stored_path: str | None = None
        if payload.log_response:
            stored = runtime.knowledge.store(
                "web_" + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
                response,
            )
            stored_path = str(stored)

        return {
            "mission": mission,
            "confidence": thought.confidence,
            "considerations": thought.considerations,
            "response": response,
            "stored_path": stored_path,
        }

    @app.get("/api/history")
    async def history(limit: int = 10) -> Dict[str, Any]:
        traces = runtime.memory.recall()
        return {
            "items": [_trace_to_dict(trace) for trace in traces[-limit:]],
            "total": len(traces),
        }

    @app.get("/api/knowledge")
    async def knowledge(limit: int = 10) -> Dict[str, Any]:
        return {"items": _knowledge_listing(runtime, limit)}

    return app


__all__ = ["create_app", "MissionRequest"]

