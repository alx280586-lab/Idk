"""Double-click friendly training runner for the Luau Synthesis Lab."""
from __future__ import annotations

import json
import pathlib
import sys

from luau_lab import RetrievalClient, TrainingSuite, load_config


def main() -> None:
    config = load_config()
    print("Loaded configuration from", pathlib.Path("config.yaml").resolve())
    retriever = RetrievalClient(config.get_allowed_sources())
    trainer = TrainingSuite(config, retriever=retriever)
    summary = trainer.run_all()
    print("Training finished. Summary:")
    print(json.dumps(summary, indent=2))
    print("You can close this window or re-run it whenever you want to refresh the lab.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
