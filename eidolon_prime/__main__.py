"""Command line entry point."""
from __future__ import annotations

from .app import EidolonPrimeApp
from .config import save_default_config


def main() -> None:
    save_default_config()
    app = EidolonPrimeApp.from_config_path()
    app.run_interactive()


if __name__ == "__main__":
    main()
