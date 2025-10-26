"""Rendering utilities for the radar simulator."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import matplotlib
matplotlib.use("Agg")  # The canvas is embedded in PyQt, not shown directly.
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Polygon as MplPolygon
import cartopy.crs as ccrs
import cartopy.feature as cfeature

PRODUCT_COLORMAPS: Dict[str, ListedColormap] = {}


def _build_reflectivity_cmap() -> ListedColormap:
    # Multi-colour scheme loosely based on NWS reflectivity palettes.
    colors = [
        (0.7, 0.7, 0.7),
        (0.4, 0.6, 0.9),
        (0.2, 0.8, 0.2),
        (0.9, 0.9, 0.0),
        (0.96, 0.6, 0.1),
        (0.9, 0.2, 0.2),
        (0.7, 0.0, 0.7),
        (0.3, 0.0, 0.3),
    ]
    return ListedColormap(colors, name="synthetic_dbz")


def _build_velocity_cmap() -> ListedColormap:
    colors = [
        (0.1, 0.2, 0.6),
        (0.2, 0.4, 0.9),
        (0.9, 0.9, 0.9),
        (0.9, 0.4, 0.4),
        (0.6, 0.1, 0.1),
    ]
    return ListedColormap(colors, name="synthetic_velocity")


def _build_diverging(base_colors) -> ListedColormap:
    return ListedColormap(base_colors, name="synthetic_diverging")


PRODUCT_COLORMAPS["Reflectivity"] = _build_reflectivity_cmap()
PRODUCT_COLORMAPS["Composite Reflectivity"] = PRODUCT_COLORMAPS["Reflectivity"]
PRODUCT_COLORMAPS["Velocity"] = _build_velocity_cmap()
PRODUCT_COLORMAPS["Spectrum Width"] = _build_diverging([
    (0.3, 0.3, 0.3),
    (0.5, 0.7, 0.9),
    (0.95, 0.8, 0.2),
    (0.8, 0.3, 0.05),
])
PRODUCT_COLORMAPS["Correlation Coefficient"] = _build_diverging([
    (0.4, 0.0, 0.0),
    (0.6, 0.2, 0.2),
    (0.8, 0.5, 0.5),
    (0.95, 0.95, 0.95),
])
PRODUCT_COLORMAPS["Differential Reflectivity"] = _build_diverging([
    (0.2, 0.1, 0.4),
    (0.4, 0.2, 0.6),
    (0.9, 0.9, 0.9),
    (0.8, 0.7, 0.3),
])
PRODUCT_COLORMAPS["Specific Differential Phase"] = _build_diverging([
    (0.3, 0.3, 0.3),
    (0.4, 0.7, 0.4),
    (0.8, 0.3, 0.3),
    (0.9, 0.2, 0.9),
])


@dataclass
class RenderOptions:
    vmin: float
    vmax: float
    clutter_filter: bool = True
    dualpol_qc: bool = False
    velocity_dealias: bool = True
    brightness: float = 1.0
    contrast: float = 1.0


class RadarRenderer:
    def __init__(self, config: Dict):
        render_cfg = config.get("rendering", {})
        projection_name = render_cfg.get("map_projection", "LambertConformal")
        if projection_name == "LambertConformal":
            self.projection = ccrs.LambertConformal(central_longitude=-96, central_latitude=35)
        else:
            self.projection = ccrs.PlateCarree()
        self.data_crs = ccrs.PlateCarree()
        self.fig = plt.Figure(figsize=(10, 6))
        self.ax = self.fig.add_subplot(111, projection=self.projection)
        self.ax.set_extent([-125, -66, 24, 50], ccrs.PlateCarree())
        self.ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.6)
        self.ax.add_feature(cfeature.STATES.with_scale("50m"), linewidth=0.3)
        self.ax.add_feature(cfeature.BORDERS.with_scale("50m"), linewidth=0.4)
        self.mesh = None
        self.colorbar = None

    def draw(
        self,
        product_name: str,
        array: np.ndarray,
        lon_grid: np.ndarray,
        lat_grid: np.ndarray,
        warnings: List["WarningPolygon"],
        options: RenderOptions,
    ) -> None:
        cmap = PRODUCT_COLORMAPS.get(product_name, plt.cm.viridis)
        vmin = options.vmin
        vmax = options.vmax
        adjusted = self._adjust_image(array, options)

        if self.mesh is None:
            self.mesh = self.ax.imshow(
                adjusted,
                extent=[lon_grid.min(), lon_grid.max(), lat_grid.min(), lat_grid.max()],
                origin="lower",
                cmap=cmap,
                vmin=vmin,
                vmax=vmax,
                transform=self.data_crs,
            )
        else:
            self.mesh.set_data(adjusted)
            self.mesh.set_cmap(cmap)
            self.mesh.set_clim(vmin=vmin, vmax=vmax)

        if self.colorbar is None:
            self.colorbar = self.fig.colorbar(self.mesh, ax=self.ax, orientation="vertical", shrink=0.7)
        self.colorbar.set_label(product_name)

        # Remove existing warning patches.
        for artist in list(self.ax.artists):
            artist.remove()
        for patch in list(self.ax.patches):
            if isinstance(patch, MplPolygon) and getattr(patch, "_is_warning", False):
                patch.remove()

        for warning in warnings:
            poly = MplPolygon(warning.polygon, closed=True, facecolor=warning.color, edgecolor="black", linewidth=1.0,
                              transform=self.data_crs)
            poly._is_warning = True
            self.ax.add_patch(poly)
            self.ax.text(
                warning.polygon[0][0],
                warning.polygon[0][1],
                f"{warning.type}\n{warning.level}",
                transform=self.data_crs,
                fontsize=7,
                color="black",
                bbox=dict(facecolor="white", alpha=0.6, boxstyle="round,pad=0.2"),
            )

        self.fig.canvas.draw_idle()

    def _adjust_image(self, array: np.ndarray, options: RenderOptions) -> np.ndarray:
        arr = array.astype(np.float32)
        mean = np.mean(arr)
        arr = (arr - mean) * options.contrast + mean
        arr = arr * options.brightness
        return arr


__all__ = ["RadarRenderer", "RenderOptions"]
