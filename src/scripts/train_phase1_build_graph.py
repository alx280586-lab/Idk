"""Phase 1 training script placeholder."""
from __future__ import annotations

from nfce.config import IngestionConfig
from nfce.ingestion.pipeline import ingest


def main():
    cfg = IngestionConfig()
    ingest(cfg)


if __name__ == "__main__":
    main()
