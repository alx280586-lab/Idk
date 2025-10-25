"""Matplotlib canvas for radar plan-view visualization."""
from __future__ import annotations

from typing import Dict

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import Polygon

from ..analysis.warnings import WarningPolygon, WarningType


WARNING_COLORS = {
    WarningType.SEVERE_THUNDERSTORM: "#ffcc00",
    WarningType.TORNADO: "#ff0000",
    WarningType.TORNADO_EMERGENCY: "#ff00ff",
    WarningType.FLASH_FLOOD: "#00aa55",
}


class RadarCanvas(FigureCanvasQTAgg):
    """Provide Matplotlib-based plan view displays integrated with PyQt."""

    def __init__(self) -> None:
        self.figure = Figure(figsize=(6, 6))
        super().__init__(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Radar Reflectivity")
        self.ax.set_xlabel("X (km)")
        self.ax.set_ylabel("Y (km)")
        self.image = None
        self.warning_patches: Dict[int, Polygon] = {}

    def update_ppi(self, data: np.ndarray, description: str, units: str) -> None:
        vmin = float(np.nanmin(data)) if np.isfinite(data).any() else 0.0
        vmax = float(np.nanmax(data)) if np.isfinite(data).any() else 1.0
        if self.image is None:
            self.image = self.ax.imshow(
                data,
                origin="lower",
                cmap="Spectral_r",
                vmin=vmin,
                vmax=vmax,
                interpolation="nearest",
            )
            self.colorbar = self.figure.colorbar(self.image, ax=self.ax, label=units)
        else:
            self.image.set_data(data)
            self.image.set_clim(vmin, vmax)
            self.colorbar.set_label(units)
        self.ax.set_title(description)
        self.draw_idle()

    def render_warnings(self, polygons: Dict[int, WarningPolygon]) -> None:
        for patch in self.warning_patches.values():
            patch.remove()
        self.warning_patches.clear()

        for storm_id, polygon in polygons.items():
            color = WARNING_COLORS.get(polygon.warning_type, "white")
            patch = Polygon(polygon.vertices, closed=True, fill=False, edgecolor=color, lw=2)
            self.ax.add_patch(patch)
            self.warning_patches[storm_id] = patch
        self.draw_idle()
