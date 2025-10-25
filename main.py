"""Entry point for the StormScope GR-2 Analyst Simulator."""
from __future__ import annotations

import sys

from PyQt6 import QtWidgets

from stormscope.gui.main_window import MainWindow


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
