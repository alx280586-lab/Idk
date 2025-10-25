"""Matplotlib canvas for radar plan-view visualization."""
from __future__ import annotations

from typing import Dict, Tuple

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

PRODUCT_DISPLAY_SETTINGS = {
    "reflectivity": {"cmap": "Spectral_r", "vmin": -10.0, "vmax": 70.0},
    "velocity": {"cmap": "coolwarm", "vmin": -45.0, "vmax": 45.0},
    "zdr": {"cmap": "RdBu_r", "vmin": -2.5, "vmax": 5.0},
    "cc": {"cmap": "viridis", "vmin": 0.7, "vmax": 1.0},
    "kdp": {"cmap": "plasma", "vmin": -1.0, "vmax": 6.0},
    "spectrum_width": {"cmap": "magma", "vmin": 0.0, "vmax": 8.0},
    "echo_tops": {"cmap": "inferno", "vmin": 0.0, "vmax": 60.0},
    "vil": {"cmap": "cividis", "vmin": 0.0, "vmax": 80.0},
    "rotation": {"cmap": "PuOr_r", "vmin": 0.0, "vmax": 2.0},
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
        self.ax.set_aspect("equal")
        self.ax.set_facecolor("#0b0d11")
        self.figure.set_facecolor("#0b0d11")
        self.ax.grid(True, color="#2c2f36", linewidth=0.6, alpha=0.4)
        self.ax.tick_params(colors="#d7dce5")
        self.ax.spines["bottom"].set_color("#d7dce5")
        self.ax.spines["left"].set_color("#d7dce5")
        self.image = None
        self.warning_patches: Dict[int, Polygon] = {}
        self.warning_labels: Dict[int, object] = {}
        self.domain_size: Tuple[float, float] = (200.0, 200.0)

    def update_ppi(
        self,
        data: np.ndarray,
        description: str,
        units: str,
        field_name: str | None = None,
    ) -> None:
        settings = PRODUCT_DISPLAY_SETTINGS.get(field_name or "", {})
        vmin = settings.get("vmin")
        vmax = settings.get("vmax")
        if vmin is None or vmax is None:
            finite = np.isfinite(data)
            vmin = float(np.nanmin(data)) if finite.any() else 0.0
            vmax = float(np.nanmax(data)) if finite.any() else 1.0
        cmap = settings.get("cmap", "Spectral_r")
        if self.image is None:
            self.image = self.ax.imshow(
                data,
                origin="lower",
                cmap=cmap,
                vmin=vmin,
                vmax=vmax,
                interpolation="bilinear",
                extent=(0, self.domain_size[0], 0, self.domain_size[1]),
            )
            self.colorbar = self.figure.colorbar(self.image, ax=self.ax, label=units)
        else:
            self.image.set_data(data)
            self.image.set_cmap(cmap)
            self.image.set_clim(vmin, vmax)
            self.image.set_extent((0, self.domain_size[0], 0, self.domain_size[1]))
            self.colorbar.set_label(units)
        self.ax.set_xlim(0, self.domain_size[0])
        self.ax.set_ylim(0, self.domain_size[1])
        self.ax.set_title(description)
        self.draw_idle()

    def render_warnings(self, polygons: Dict[int, WarningPolygon]) -> None:
        for patch in self.warning_patches.values():
            patch.remove()
        self.warning_patches.clear()
        for label in self.warning_labels.values():
            label.remove()
        self.warning_labels.clear()

        for storm_id, polygon in polygons.items():
            color = WARNING_COLORS.get(polygon.warning_type, "white")
            linewidth = 3.0 if polygon.warning_type == WarningType.TORNADO_EMERGENCY else 2.0
            linestyle = "--" if polygon.warning_type == WarningType.TORNADO_EMERGENCY else "-"
            patch = Polygon(
                polygon.vertices,
                closed=True,
                fill=False,
                edgecolor=color,
                lw=linewidth,
                linestyle=linestyle,
            )
            self.ax.add_patch(patch)
            self.warning_patches[storm_id] = patch
            centroid = polygon.vertices.mean(axis=0)
            label = self.ax.text(
                centroid[0],
                centroid[1],
                polygon.warning_type.name.replace("_", "\n"),
                color=color,
                fontsize=8,
                ha="center",
                va="center",
                weight="bold",
                alpha=0.8,
            )
            self.warning_labels[storm_id] = label
        self.draw_idle()

    def set_domain_size(self, domain_size: Tuple[float, float]) -> None:
        self.domain_size = domain_size

    def color_for_warning(self, warning_type: WarningType) -> str:
        return WARNING_COLORS.get(warning_type, "#ffffff")
