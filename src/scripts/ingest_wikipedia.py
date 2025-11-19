"""CLI entry for Wikipedia ingestion."""
from __future__ import annotations

import argparse
from nfce.config import IngestionConfig
from nfce.ingestion.pipeline import ingest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump_path", type=str, required=True)
    parser.add_argument("--batch_size", type=int, default=32)
    args = parser.parse_args()
    cfg = IngestionConfig(dump_path=args.dump_path, batch_size=args.batch_size)
    ingest(cfg)


if __name__ == "__main__":
    main()
