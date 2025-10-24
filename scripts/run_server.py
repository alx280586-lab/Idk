"""Launch the FastAPI server for browser-based interactions."""
from __future__ import annotations

import argparse

import uvicorn

from ai_system.interfaces.server import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the organic scripting AI web server")
    parser.add_argument("--host", default="0.0.0.0", help="Interface to bind the server")
    parser.add_argument("--port", type=int, default=8000, help="Port to expose the service")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (useful during development, disable in production)",
    )
    args = parser.parse_args()

    uvicorn.run(create_app(), host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()

