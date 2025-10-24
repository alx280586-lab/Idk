import argparse
import threading
import time
import webbrowser

from luau_lab import RetrievalClient, load_config
from luau_lab.training import TrainingSuite
from web_server import app


def _open_browser(url: str, delay: float) -> None:
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the Luau Synthesis Lab browser UI.")
    parser.add_argument("--host", default="127.0.0.1", help="Interface to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to serve the UI on (default: 8000)")
    parser.add_argument(
        "--train",
        action="store_true",
        help="Run the training suite before launching the server.",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open the browser window.",
    )
    args = parser.parse_args()

    if args.train:
        config = load_config()
        retriever = RetrievalClient(config.get_allowed_sources())
        suite = TrainingSuite(config, retriever=retriever)
        summary = suite.run_all()
        print("Training summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")

    url = f"http://{args.host}:{args.port}"
    if not args.no_browser:
        threading.Thread(target=_open_browser, args=(url, 1.5), daemon=True).start()

    print(f"Launching Luau Synthesis Lab UI at {url}")
    print("Press Ctrl+C in this window to stop the server.")

    app.run(host=args.host, port=args.port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
