"""Run online harvesting to expand the knowledge base."""
from __future__ import annotations

from ai_system.config import DEFAULT_CONFIG
from ai_system.training.online_trainer import OnlineTrainer


def main() -> None:
    trainer = OnlineTrainer(DEFAULT_CONFIG)
    results = trainer.harvest()
    for name, path in results.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()

