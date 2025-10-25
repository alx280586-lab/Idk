"""Main PyQt window for the StormScope simulator."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets

from ..analysis.storm_detection import StormDetector
from ..analysis.warnings import WarningEngine
from ..data.products import RadarProductComputer
from ..data.synthetic_generator import SyntheticRadarGenerator
from ..simulation.clock import SimulationClock
from ..visualization.radar_canvas import RadarCanvas


@dataclass
class ProductSelection:
    field: str
    elevation_index: int | None


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("StormScope GR-2 Analyst Simulator")
        self.resize(1200, 800)

        self.generator = SyntheticRadarGenerator()
        self.detector = StormDetector()
        domain = np.array(self.generator.domain_size)
        self.warning_engine = WarningEngine(domain)
        self.clock = SimulationClock()

        self.product_selection = ProductSelection(field="reflectivity", elevation_index=0)

        self.canvas = RadarCanvas()
        self.canvas.set_domain_size(self.generator.domain_size)
        self.status = self.statusBar()

        self._setup_layout()
        self._setup_timers()

    def _setup_layout(self) -> None:
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QHBoxLayout(central)

        controls = QtWidgets.QVBoxLayout()
        layout.addLayout(controls, stretch=0)
        layout.addWidget(self.canvas, stretch=1)

        controls.addWidget(QtWidgets.QLabel("Radar Product"))
        self.product_combo = QtWidgets.QComboBox()
        self.product_combo.addItems(
            [
                "Reflectivity",
                "Velocity",
                "Differential Reflectivity",
                "Correlation Coefficient",
                "Specific Differential Phase",
                "Spectrum Width",
                "Echo Tops",
                "VIL",
                "Rotation",
            ]
        )
        self.product_combo.currentIndexChanged.connect(self._on_product_changed)
        controls.addWidget(self.product_combo)

        controls.addWidget(QtWidgets.QLabel("Elevation"))
        self.elevation_spin = QtWidgets.QSpinBox()
        self.elevation_spin.setRange(0, self.generator.grid_shape[0] - 1)
        self.elevation_spin.setValue(0)
        self.elevation_spin.valueChanged.connect(self._on_elevation_changed)
        controls.addWidget(self.elevation_spin)

        self.pause_button = QtWidgets.QPushButton("Pause")
        self.pause_button.clicked.connect(self._toggle_pause)
        controls.addWidget(self.pause_button)

        self.skip_button = QtWidgets.QPushButton("Skip +5 min")
        self.skip_button.clicked.connect(lambda: self.clock.skip_ahead(300))
        controls.addWidget(self.skip_button)

        controls.addWidget(QtWidgets.QLabel("Active Warnings"))
        self.warning_list = QtWidgets.QListWidget()
        self.warning_list.setMinimumWidth(220)
        controls.addWidget(self.warning_list)

        controls.addStretch(1)

    def _setup_timers(self) -> None:
        self.update_timer = QtCore.QTimer(self)
        self.update_timer.setInterval(1000)
        self.update_timer.timeout.connect(self._tick)
        self.update_timer.start()

    def _tick(self) -> None:
        self.clock.advance(1.0)
        volume = self.generator.step(self.clock.time_seconds)
        products = RadarProductComputer(volume)

        selection = self.product_selection
        if selection.field in volume.fields:
            ppi = products.ppi(selection.field, selection.elevation_index)
            display_data = ppi.data
            description = ppi.description
            units = ppi.units
        elif selection.field == "echo_tops":
            display_data = products.echo_tops()
            description = "Echo Tops (kft)"
            units = "kft"
        elif selection.field == "vil":
            display_data = products.vertically_integrated_liquid()
            description = "Vertically Integrated Liquid"
            units = "kg/m²"
        elif selection.field == "rotation":
            display_data = products.normalized_rotation()
            description = "Normalized Rotation"
            units = "s⁻¹"
        else:
            display_data = products.ppi("reflectivity").data
            description = "Reflectivity"
            units = "dBZ"

        self.canvas.update_ppi(display_data, description, units)

        storms = self.detector.detect(volume, self.clock.time_seconds)
        issued = self.warning_engine.update(self.clock.time_seconds, storms)
        self.canvas.render_warnings(self.warning_engine.active)

        self._update_status(storms, issued)
        self._refresh_warning_list()

    def _update_status(self, storms, warnings) -> None:
        message = (
            f"Time: {self.clock.time_seconds/60:.1f} min | "
            f"Storms: {len(storms)} | Active warnings: {len(self.warning_engine.active)}"
        )
        self.status.showMessage(message)

    def _toggle_pause(self) -> None:
        self.clock.toggle_running()
        self.pause_button.setText("Resume" if not self.clock.running else "Pause")

    def _on_product_changed(self, index: int) -> None:
        mapping = {
            0: ("reflectivity", 0),
            1: ("velocity", 0),
            2: ("zdr", 0),
            3: ("cc", 0),
            4: ("kdp", 0),
            5: ("spectrum_width", 0),
            6: ("echo_tops", None),
            7: ("vil", None),
            8: ("rotation", None),
        }
        field, elevation = mapping.get(index, ("reflectivity", 0))
        self.product_selection = ProductSelection(field=field, elevation_index=elevation)
        if elevation is None:
            self.elevation_spin.setEnabled(False)
        else:
            self.elevation_spin.setEnabled(True)
            self.elevation_spin.setValue(elevation)

    def _on_elevation_changed(self, value: int) -> None:
        self.product_selection = ProductSelection(
            field=self.product_selection.field, elevation_index=value
        )

    def _refresh_warning_list(self) -> None:
        self.warning_list.clear()
        for polygon in self.warning_engine.active.values():
            label = polygon.warning_type.name.replace("_", " ")
            hazard = polygon.metadata.get("hazard", "")
            expires = polygon.valid_until - self.clock.time_seconds
            minutes = max(expires / 60.0, 0.0)
            self.warning_list.addItem(f"{label}: {hazard} ({minutes:.0f} min left)")
