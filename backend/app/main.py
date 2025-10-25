from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.state import State


def create_app() -> FastAPI:
    app = FastAPI(
        title="AutoClipper AI",
        description="Autonomous short-form content generator and publisher",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    state = State.get_instance()
    state.bootstrap()

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
