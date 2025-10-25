"""Main PyQt window for the StormScope simulator."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Sequence

import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets

from ..analysis.storm_detection import StormDetector
from ..analysis.warnings import WarningEngine, WarningType
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
        self.detector = StormDetector(domain_size=self.generator.domain_size)
        domain = np.array(self.generator.domain_size)
        self.warning_engine = WarningEngine(domain)
        self.clock = SimulationClock()

        self.product_selection = ProductSelection(field="reflectivity", elevation_index=0)
        self._current_description = "Reflectivity"

        self.canvas = RadarCanvas()
        self.canvas.set_domain_size(self.generator.domain_size)
        self.status = self.statusBar()

        self._setup_layout()
        self._setup_timers()

    def _setup_layout(self) -> None:
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        controls_widget = QtWidgets.QWidget()
        controls_widget.setMinimumWidth(280)
        splitter.addWidget(controls_widget)
        splitter.addWidget(self.canvas)
        splitter.setStretchFactor(1, 1)

        controls = QtWidgets.QVBoxLayout(controls_widget)
        controls.setContentsMargins(8, 8, 8, 8)
        controls.setSpacing(10)

        product_group = QtWidgets.QGroupBox("Display Controls")
        product_form = QtWidgets.QFormLayout(product_group)
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
        self.elevation_spin = QtWidgets.QSpinBox()
        self.elevation_spin.setRange(0, self.generator.grid_shape[0] - 1)
        self.elevation_spin.setValue(0)
        self.elevation_spin.valueChanged.connect(self._on_elevation_changed)
        product_form.addRow("Radar Product", self.product_combo)
        product_form.addRow("Elevation", self.elevation_spin)
        controls.addWidget(product_group)

        simulation_group = QtWidgets.QGroupBox("Simulation Control")
        simulation_layout = QtWidgets.QHBoxLayout(simulation_group)
        self.pause_button = QtWidgets.QPushButton("Pause")
        self.pause_button.clicked.connect(self._toggle_pause)
        simulation_layout.addWidget(self.pause_button)
        self.skip_button = QtWidgets.QPushButton("Skip +5 min")
        self.skip_button.clicked.connect(lambda: self.clock.skip_ahead(300))
        simulation_layout.addWidget(self.skip_button)
        controls.addWidget(simulation_group)

        warning_group = QtWidgets.QGroupBox("Active Warnings")
        warning_layout = QtWidgets.QVBoxLayout(warning_group)
        self.warning_list = QtWidgets.QListWidget()
        self.warning_list.setAlternatingRowColors(True)
        self.warning_list.setMinimumHeight(140)
        warning_layout.addWidget(self.warning_list)
        controls.addWidget(warning_group)

        storm_group = QtWidgets.QGroupBox("Storm Monitor")
        storm_layout = QtWidgets.QVBoxLayout(storm_group)
        self.storm_table = QtWidgets.QTableWidget(0, 6)
        self.storm_table.setHorizontalHeaderLabels(
            ["ID", "Age (min)", "Max dBZ", "Rotation", "Hail (in)", "Rain (in/hr)"]
        )
        self.storm_table.verticalHeader().setVisible(False)
        self.storm_table.setAlternatingRowColors(True)
        self.storm_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.storm_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.storm_table.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        self.storm_table.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        header = self.storm_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        storm_layout.addWidget(self.storm_table)
        controls.addWidget(storm_group)

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

        self.canvas.update_ppi(display_data, description, units, selection.field)
        self._current_description = description

        storms = self.detector.detect(volume, self.clock.time_seconds)
        issued = self.warning_engine.update(self.clock.time_seconds, storms)
        self.canvas.render_warnings(self.warning_engine.active)

        self._refresh_storm_table(storms)
        self._update_status(storms, issued)
        self._refresh_warning_list(issued)

    def _update_status(self, storms, warnings) -> None:
        issued_text = f" | Issued: {len(warnings)}" if warnings else ""
        message = (
            f"Time {self.clock.time_seconds/60:.1f} min | {self._current_description} | "
            f"Storms: {len(storms)} | Active warnings: {len(self.warning_engine.active)}"
            f"{issued_text}"
        )
        timeout = 5000 if warnings else 0
        self.status.showMessage(message, timeout)

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

    def _refresh_warning_list(self, recently_issued: Sequence = ()) -> None:
        self.warning_list.clear()
        priority = {
            WarningType.TORNADO_EMERGENCY: 0,
            WarningType.TORNADO: 1,
            WarningType.SEVERE_THUNDERSTORM: 2,
            WarningType.FLASH_FLOOD: 3,
        }
        recent_ids = {
            polygon.metadata.get("storm_id") for polygon in recently_issued if polygon is not None
        }
        polygons = sorted(
            self.warning_engine.active.values(),
            key=lambda poly: (priority.get(poly.warning_type, 4), poly.valid_until),
        )
        for polygon in polygons:
            label = polygon.warning_type.name.replace("_", " ")
            hazard = polygon.metadata.get("hazard", "")
            expires = polygon.valid_until - self.clock.time_seconds
            minutes = max(expires / 60.0, 0.0)
            confidence = polygon.metadata.get("confidence")
            confidence_text = (
                f"{confidence * 100:.0f}%" if isinstance(confidence, (float, int)) else ""
            )
            storm_id = polygon.metadata.get("storm_id")
            parts = [label]
            if storm_id is not None:
                parts.append(f"Storm {storm_id}")
            if hazard:
                parts.append(hazard)
            if confidence_text:
                parts.append(f"Confidence {confidence_text}")
            text = " | ".join(parts)
            text += f" ({minutes:.0f} min left)"
            item = QtWidgets.QListWidgetItem(text)
            color = QtGui.QColor(self.canvas.color_for_warning(polygon.warning_type))
            item.setForeground(color)
            if storm_id in recent_ids:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            self.warning_list.addItem(item)

    def _refresh_storm_table(self, storms: Sequence) -> None:
        storms_sorted = sorted(
            storms,
            key=lambda s: (
                getattr(s, "max_rotation", 0.0),
                getattr(s, "mesh", 0.0),
                getattr(s, "max_reflectivity", 0.0),
            ),
            reverse=True,
        )
        self.storm_table.setRowCount(len(storms_sorted))
        for row, storm in enumerate(storms_sorted):
            age_minutes = getattr(storm, "age_seconds", 0.0) / 60.0
            rainfall_in_hr = getattr(storm, "rainfall_rate", 0.0) / 25.4
            values = [
                str(storm.id),
                f"{age_minutes:.1f}",
                f"{storm.max_reflectivity:.0f}",
                f"{storm.max_rotation:.0f}",
                f"{storm.mesh:.2f}",
                f"{rainfall_in_hr:.1f}",
            ]
            for col, text in enumerate(values):
                self._set_table_item(row, col, text)

            tooltip = (
                f"Storm {storm.id}\n"
                f"Age: {age_minutes:.1f} min\n"
                f"Max Reflectivity: {storm.max_reflectivity:.1f} dBZ\n"
                f"Rotation: {storm.max_rotation:.1f}\n"
                f"MESH: {storm.mesh:.2f} in\n"
                f"Rainfall: {rainfall_in_hr:.1f} in/hr\n"
                f"Area: {storm.area_km2:.0f} km²"
            )
            highlight = None
            if storm.max_rotation >= 45.0:
                highlight = QtGui.QColor("#ffe0e0")
            elif storm.mesh >= 1.2:
                highlight = QtGui.QColor("#fff3cc")
            for col in range(self.storm_table.columnCount()):
                item = self.storm_table.item(row, col)
                if item is not None:
                    item.setToolTip(tooltip)
                    if highlight is not None:
                        item.setBackground(highlight)

    def _set_table_item(self, row: int, column: int, text: str) -> None:
        item = QtWidgets.QTableWidgetItem(text)
        item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        item.setFlags(
            QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEnabled
        )
        self.storm_table.setItem(row, column, item)
