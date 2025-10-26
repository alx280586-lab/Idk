"""PyQt6 GUI for the synthetic radar simulator."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QShortcut,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QCheckBox,
)
from PyQt6.QtGui import QKeySequence
import numpy as np
import yaml

from storm_generator import SyntheticStormModel, RadarFrame
from detectors import DetectorSuite
from warnings import WarningEngine, WarningPolygon
from renderer import RadarRenderer, RenderOptions


class RadarWindow(QMainWindow):
    """Main application window."""

    def __init__(self, config: Dict):
        super().__init__()
        self.setWindowTitle("Synthetic Radar Simulator – Bring Your Own Umbrella")
        self.resize(1200, 750)
        self.config = config
        self.model = SyntheticStormModel(config)
        self.detectors = DetectorSuite(config.get("detectors", {}))
        self.warning_engine = WarningEngine(config.get("warnings", {}))
        self.renderer = RadarRenderer(config)
        self.canvas = self._create_canvas()
        self.sim_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        self.frames: List[RadarFrame] = self.model.generate_day()
        self.frame_warnings: List[List[WarningPolygon]] = []
        self._prepare_metadata()

        self.current_index = 0
        self.playing = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._advance_frame)
        self.timer.setInterval(400)

        self._build_ui()
        self._setup_shortcuts()
        self._update_display()

    # ------------------------------------------------------------------
    def _create_canvas(self):
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

        canvas = FigureCanvas(self.renderer.fig)
        return canvas

    def _prepare_metadata(self) -> None:
        for frame in self.frames:
            detections = self.detectors.run_all(frame.products, frame.storms, self.model.lon_grid, self.model.lat_grid)
            warnings = self.warning_engine.generate(
                detections,
                frame.storms,
                frame.products,
                self.sim_start,
                frame.timestamp_minutes,
                self.model.lon_grid,
                self.model.lat_grid,
            )
            self.frame_warnings.append(warnings)

    def _build_ui(self) -> None:
        main_widget = QWidget(self)
        layout = QHBoxLayout(main_widget)

        controls = self._build_controls()
        layout.addWidget(controls, stretch=0)
        layout.addWidget(self.canvas, stretch=1)
        self.setCentralWidget(main_widget)
        self.status_label = QLabel()
        self.statusBar().addWidget(self.status_label)

    def _build_controls(self) -> QWidget:
        panel = QWidget()
        vbox = QVBoxLayout(panel)
        vbox.setContentsMargins(6, 6, 6, 6)
        vbox.setSpacing(8)

        # Product selection
        self.product_combo = QComboBox()
        self.product_combo.addItems(list(self.frames[0].products.keys()))
        self.product_combo.currentTextChanged.connect(self._update_display)
        vbox.addWidget(QLabel("Radar Product"))
        vbox.addWidget(self.product_combo)

        # Brightness/contrast controls
        self.brightness_spin = QDoubleSpinBox()
        self.brightness_spin.setRange(0.2, 3.0)
        self.brightness_spin.setSingleStep(0.1)
        self.brightness_spin.setValue(1.0)
        self.brightness_spin.valueChanged.connect(self._update_display)
        self.contrast_spin = QDoubleSpinBox()
        self.contrast_spin.setRange(0.2, 3.0)
        self.contrast_spin.setSingleStep(0.1)
        self.contrast_spin.setValue(1.0)
        self.contrast_spin.valueChanged.connect(self._update_display)
        vbox.addWidget(QLabel("Brightness"))
        vbox.addWidget(self.brightness_spin)
        vbox.addWidget(QLabel("Contrast"))
        vbox.addWidget(self.contrast_spin)

        # QC toggles
        self.clutter_check = QCheckBox("Clutter Filter")
        self.clutter_check.setChecked(True)
        self.clutter_check.stateChanged.connect(self._update_display)
        self.dualpol_check = QCheckBox("Dual-Pol QC")
        self.dualpol_check.setChecked(False)
        self.dualpol_check.stateChanged.connect(self._update_display)
        self.dealias_check = QCheckBox("Velocity Dealiasing")
        self.dealias_check.setChecked(True)
        self.dealias_check.stateChanged.connect(self._update_display)
        vbox.addWidget(self.clutter_check)
        vbox.addWidget(self.dualpol_check)
        vbox.addWidget(self.dealias_check)

        # Playback controls
        play_layout = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self._toggle_play)
        self.skip_back_button = QPushButton("⏮ -1h")
        self.skip_back_button.clicked.connect(lambda: self._skip_hours(-1))
        self.skip_forward_button = QPushButton("⏭ +1h")
        self.skip_forward_button.clicked.connect(lambda: self._skip_hours(1))
        play_layout.addWidget(self.play_button)
        play_layout.addWidget(self.skip_back_button)
        play_layout.addWidget(self.skip_forward_button)
        vbox.addLayout(play_layout)

        # Time slider
        vbox.addWidget(QLabel("Simulated Time"))
        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setRange(0, len(self.frames) - 1)
        self.time_slider.valueChanged.connect(self._slider_changed)
        vbox.addWidget(self.time_slider)

        # Hour spin to jump to
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.valueChanged.connect(self._jump_to_hour)
        vbox.addWidget(QLabel("Jump to Hour"))
        vbox.addWidget(self.hour_spin)

        # Warning list
        vbox.addWidget(QLabel("Active Warnings"))
        self.warning_list = QListWidget()
        vbox.addWidget(self.warning_list, stretch=1)

        vbox.addStretch(1)
        return panel

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, activated=self._toggle_play)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, activated=lambda: self._skip_hours(1))
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, activated=lambda: self._skip_hours(-1))

    # ------------------------------------------------------------------
    def _slider_changed(self, value: int) -> None:
        self.current_index = value
        total_minutes = self.frames[value].timestamp_minutes
        self.hour_spin.blockSignals(True)
        self.hour_spin.setValue((total_minutes // 60) % 24)
        self.hour_spin.blockSignals(False)
        self._update_display()

    def _jump_to_hour(self, hour: int) -> None:
        # Find the frame closest to the requested hour
        target_minute = hour * 60
        closest = min(range(len(self.frames)), key=lambda i: abs(self.frames[i].timestamp_minutes - target_minute))
        self.time_slider.blockSignals(True)
        self.time_slider.setValue(closest)
        self.time_slider.blockSignals(False)
        self._slider_changed(closest)

    def _toggle_play(self) -> None:
        self.playing = not self.playing
        if self.playing:
            self.timer.start()
            self.play_button.setText("Pause")
        else:
            self.timer.stop()
            self.play_button.setText("Play")

    def _skip_hours(self, hours: int) -> None:
        step = int((60 / self.model.timestep_minutes) * abs(hours))
        if hours < 0:
            new_index = max(0, self.current_index - step)
        else:
            new_index = min(len(self.frames) - 1, self.current_index + step)
        self.time_slider.setValue(new_index)

    def _advance_frame(self) -> None:
        next_index = (self.current_index + 1) % len(self.frames)
        if next_index == 0:
            self.playing = False
            self.timer.stop()
            self.play_button.setText("Play")
        self.time_slider.setValue(next_index)

    def _update_display(self) -> None:
        frame = self.frames[self.current_index]
        product = self.product_combo.currentText()
        array = frame.products[product]
        array = self._apply_filters(product, array)
        options = self._create_render_options(product)
        warnings = self.frame_warnings[self.current_index]
        self.renderer.draw(product, array, self.model.lon_grid, self.model.lat_grid, warnings, options)
        sim_time = self.sim_start + timedelta(minutes=frame.timestamp_minutes)
        storm_count = frame.metadata.get("storm_count", len(frame.storms))
        self._populate_warning_list(warnings)
        self.status_label.setText(
            f"UTC {str(sim_time)} | Storms: {storm_count} | Warnings: {len(warnings)}"
        )
        self.canvas.draw_idle()

    def _apply_filters(self, product: str, array: np.ndarray) -> np.ndarray:
        data = array.copy()
        if not self.clutter_check.isChecked() and product == "Reflectivity":
            data = np.where(data < 20, -5, data)
        if self.dualpol_check.isChecked() and product in ("Correlation Coefficient", "Differential Reflectivity"):
            data = np.where(data < 0.85, 0.9, data)
        if product == "Velocity" and self.dealias_check.isChecked():
            nyquist = self.config["simulation"].get("nyquist_velocity", 32.0)
            # Simple dealiasing: unwrap using neighbouring bins.
            data = np.unwrap(data / nyquist * np.pi, axis=1) * nyquist / np.pi
        return data

    def _create_render_options(self, product: str) -> RenderOptions:
        defaults = self.config.get("rendering", {}).get("product_defaults", {}).get(product, {})
        vmin = defaults.get("vmin", float(np.nanmin(self.frames[0].products[product])))
        vmax = defaults.get("vmax", float(np.nanmax(self.frames[0].products[product])))
        return RenderOptions(
            vmin=vmin,
            vmax=vmax,
            clutter_filter=self.clutter_check.isChecked(),
            dualpol_qc=self.dualpol_check.isChecked(),
            velocity_dealias=self.dealias_check.isChecked(),
            brightness=self.brightness_spin.value(),
            contrast=self.contrast_spin.value(),
        )

    def _populate_warning_list(self, warnings: List[WarningPolygon]) -> None:
        self.warning_list.clear()
        for warning in warnings:
            label = f"{warning.type} ({warning.level}) – ID {warning.id}\nReason: {', '.join(warning.trigger_reason)}"
            item = QListWidgetItem(label)
            self.warning_list.addItem(item)


def load_config(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def launch_ui(config_path: str) -> None:
    config = load_config(config_path)
    app = QApplication([])
    window = RadarWindow(config)
    window.show()
    app.exec()


__all__ = ["RadarWindow", "launch_ui", "load_config"]
