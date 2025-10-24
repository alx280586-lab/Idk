"""Convenience entry point to retrain the Luau Synthesis Lab."""
from __future__ import annotations

import json

from luau_lab import RetrievalClient, TrainingSuite, load_config


def main() -> None:
    config = load_config()
    retriever = RetrievalClient(config.get_allowed_sources())
    trainer = TrainingSuite(config, retriever=retriever)
    summary = trainer.run_all()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
