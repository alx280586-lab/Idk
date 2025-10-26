"""OpenGL/WebGL rendering pipeline for radar visualization."""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

import numpy as np
import xarray as xr

from ..config import RenderingConfig
from ..processing.analysis import StormSummary
from .colormaps import ColorTable, DEFAULT_TABLES


@dataclass(slots=True)
class FrameState:
    product: str
    texture_data: np.ndarray
    timestamp: float


@dataclass(slots=True)
class OverlayState:
    warnings: List[str] = field(default_factory=list)
    highest_warning: Optional[str] = None
    counts: Dict[str, int] = field(default_factory=dict)


class RadarRenderingEngine:
    """Render radar volumes using GPU-friendly texture atlases."""

    def __init__(self, config: RenderingConfig, colormaps: Optional[Dict[str, ColorTable]] = None) -> None:
        self.config = config
        self.colormaps = {**DEFAULT_TABLES, **(colormaps or {})}
        self.frame_cache: Dict[str, List[FrameState]] = {}
        self.latest_texture: Dict[str, np.ndarray] = {}
        self.overlay_state = OverlayState()

    def _normalize(self, data: xr.DataArray, value_range: Optional[Iterable[float]]) -> np.ndarray:
        values = data.values.astype(np.float32)
        if value_range is None:
            minimum, maximum = float(np.nanmin(values)), float(np.nanmax(values))
        else:
            minimum, maximum = value_range
        norm = (values - minimum) / (maximum - minimum + 1e-6)
        return np.clip(norm, 0.0, 1.0)

    def _colorize(self, normalized: np.ndarray, product: str) -> np.ndarray:
        table = self.colormaps.get(product.lower(), DEFAULT_TABLES["reflectivity"])
        return table.map_array(normalized)

    def render_volume(
        self,
        product: str,
        volume: xr.DataArray,
        value_range: Optional[Iterable[float]] = None,
    ) -> np.ndarray:
        normalized = self._normalize(volume, value_range)
        colorized = self._colorize(normalized, product)
        texture = np.flipud(colorized).copy()
        self._cache_frame(product, texture)
        self.latest_texture[product] = texture
        return texture

    def _cache_frame(self, product: str, texture: np.ndarray) -> None:
        cache = self.frame_cache.setdefault(product, [])
        cache.append(FrameState(product=product, texture_data=texture, timestamp=time.time()))
        if len(cache) > self.config.frame_cache_size:
            del cache[0]

    def time_loop(self, product: str) -> Iterable[np.ndarray]:
        cache = self.frame_cache.get(product, [])
        for frame in cache:
            yield frame.texture_data

    def update_overlay(self, summary: StormSummary) -> None:
        self.overlay_state.warnings = [f"{warn.warning_type} ({warn.severity})" for warn in summary.warnings]
        self.overlay_state.counts = dict(Counter(warn.warning_type for warn in summary.warnings))
        if summary.warnings:
            priority = {"TOR": 3, "SVR": 2, "FFW": 1}
            highest = max(summary.warnings, key=lambda w: priority.get(w.warning_type, 0))
            self.overlay_state.highest_warning = f"{highest.warning_type} - {highest.severity}"
        else:
            self.overlay_state.highest_warning = None
            self.overlay_state.counts = {}

    def overlay_summary(self) -> OverlayState:
        return self.overlay_state

    def latest_frame(self, product: str) -> Optional[np.ndarray]:
        return self.latest_texture.get(product)
