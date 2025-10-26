"""Entry point for the synthetic radar simulator desktop app."""
from __future__ import annotations

import argparse
import pathlib
import sys

from ui_main import launch_ui


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synthetic radar simulator")
    parser.add_argument(
        "--config",
        type=pathlib.Path,
        default=pathlib.Path(__file__).with_name("config.yaml"),
        help="Path to configuration YAML file",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    launch_ui(str(args.config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
